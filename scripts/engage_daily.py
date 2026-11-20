#!/usr/bin/env python3
"""Morning engagement check for @ayurpetofficial and @ayurpet_global. Read only: it never sends or posts anything.

    python scripts/engage_daily.py [--hours 48] [--accounts ayurpetofficial,ayurpet_global]

Writes engagement/reports/<date>.md (git-ignored: it holds signed story links and customers' messages) and prints a short
summary. Claude then drafts replies from the report, shows Kainaat each customer message next to the draft, and sends
only after her yes in chat (see docs/ENGAGEMENT.md).
"""
import argparse, datetime as dt, io, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENG = os.path.join(ROOT, "engagement")
PY = sys.executable


def run(*args):
    r = subprocess.run([PY, os.path.join(HERE, "engage.py"), *args], capture_output=True, text=True, encoding="utf-8",
                       env={**os.environ, "PYTHONUTF8": "1"})
    if r.returncode:
        return {"error": (r.stderr or "").strip()[-300:]}
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {"error": "unreadable output"}


def one_line(t, n=160):
    return (t or "").replace("\n", " ")[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=48)
    ap.add_argument("--accounts", default="ayurpetofficial,ayurpet_global")
    a = ap.parse_args()
    today = dt.date.today().isoformat()
    state = {}
    try:
        state = json.load(open(os.path.join(ENG, "state.json"), encoding="utf-8"))
    except FileNotFoundError:
        pass
    targets = json.load(open(os.path.join(ENG, "targets.json"), encoding="utf-8"))
    quota = targets["quota_per_account_per_day"]
    out = io.StringIO()
    w = lambda s="": print(s, file=out)
    w(f"# Engagement check, {today}")
    w("Read only. Nothing below has been sent. Replies and comments go out only after Kainaat's yes in chat.")
    summary = []
    for acct in a.accounts.split(","):
        w(f"\n## @{acct}")
        inbox = run("inbox", acct, "--hours", str(a.hours))
        w(f"\n### 1. DMs waiting for a reply ({inbox.get('needs_reply', '?')})")
        if "error" in inbox:
            w(f"ERROR: {inbox['error']}")
        for it in inbox.get("items", []):
            last = it["thread"][-1]
            win = "reply window OPEN (can answer here)" if it["reply_window_open"] else "window CLOSED (over 24 h: answer by hand in the app)"
            w(f"- **@{it['username']}** (igsid {it['igsid']}, msg_id {it['msg_id'][:24]}...), last message {it['last_at'][:16]}, {win}")
            for m in it["thread"][-4:]:
                who = "us" if m["from"] == acct else "@" + str(m["from"])
                body = m["text"] or (f"[story {m['story']}]" if m["story"] else "[photo, video or shared post]")
                w(f"    - {who} ({m['at'][:16]}): {one_line(body, 300)}")
            if any(m.get("story") == "mention" and m["from"] != acct for m in it["thread"][-3:]):
                w("    - STORY MENTION: they tagged us in a story. Say thank you in the DM and reshare it to our story by hand.")
        com = run("comments", acct, "--posts", "12")
        w(f"\n### 2. Comments on our posts with no reply from us ({com.get('needs_reply', '?')})")
        if "error" in com:
            w(f"ERROR: {com['error']}")
        for c in com.get("items", []):
            w(f"- **@{c['username']}** on {c['post']} ({c['at'][:10]}): {one_line(c['text'])}  [comment_id {c['comment_id']}]")
        tg = run("tags", acct, "--limit", "10")
        new = [x for x in tg.get("items", []) if x.get("new") and x.get("by") not in ("ayurpetofficial", "ayurpet_global")]
        w(f"\n### 3. New tags and collab posts ({len(new)})")
        if "error" in tg:
            w(f"ERROR: {tg['error']}")
        for x in new:
            w(f"- **@{x['by']}** {x['at'][:10]} {x['permalink']}: {one_line(x['caption'])}")
        wa = run("watch-all", acct)
        today_n = sum(1 for o in state.get("outbound", []) if o.get("acct") == acct and o.get("date") == today)
        w(f"\n### 4. Outbound: what our targets posted lately (we have commented on {today_n} of {quota['total']} today)")
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=a.hours)
        order = ["affiliates_partners", "pet_pages", "influencers", "brands"]
        fresh = []
        for r in wa.get("items", []):
            for p in r.get("posts", []):
                t = dt.datetime.strptime(p["at"], "%Y-%m-%dT%H:%M:%S%z")
                if t >= cutoff and not p.get("we_commented"):
                    fresh.append((order.index(r.get("group")) if r.get("group") in order else 9, t, r, p))
        for g in order:
            rows = [x for x in fresh if x[0] == order.index(g)]
            w(f"\n**{g}** (daily goal {quota[g]})")
            for _, t, r, p in sorted(rows, key=lambda x: x[1], reverse=True):
                w(f"- @{r['username']} ({r.get('followers')} followers) {p['at'][:16]} {p['permalink']}  {p['likes']} likes: {one_line(p['caption'], 110)}")
            if not rows:
                w("- nothing new in the window")
        summary.append(f"@{acct}: {inbox.get('needs_reply', '?')} DMs, {com.get('needs_reply', '?')} comments, {len(new)} new tags, {len(fresh)} target posts")
    os.makedirs(os.path.join(ENG, "reports"), exist_ok=True)
    path = os.path.join(ENG, "reports", f"{today}.md")
    open(path, "w", encoding="utf-8").write(out.getvalue())
    print("\n".join(summary)); print("report:", path)


if __name__ == "__main__":
    main()
