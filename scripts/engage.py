#!/usr/bin/env python3
"""AyurPet daily engagement: DMs, comments, tags and watching other accounts, on Meta's Graph API (uses ig.py's token).

Read (safe, any time):
  engage.py inbox <acct> [--hours 48]        conversations whose last message is from the customer (needs a reply), story
                                             mentions and shared posts included. Skips ones already handled (state file)
  engage.py comments <acct> [--posts 12]     new comments on our latest posts that we have not replied to
  engage.py tags <acct> [--limit 10]         posts that tag us or collab with us
  engage.py watch <acct> <username> [--n 3]  latest posts of another business/creator account (business_discovery)
  engage.py watch-all <acct> [--group G]     active targets for this account in engagement/targets.json, newest posts + whether we commented
  engage.py log-outbound <acct> --target U --permalink URL --text T   record a comment posted by hand (feeds the daily quota)
  engage.py tags-seen <acct>                 mark the current tags/collabs as seen so tomorrow only shows new ones
Write (dry run unless --send; every send needs Kainaat's yes in chat first, see docs/ENGAGEMENT.md):
  engage.py dm-send <acct> --to <igsid> --text-file F [--send]
  engage.py reply <acct> --comment <comment_id> --text-file F [--send]
  engage.py done <acct> --kind dm|comment --id <id>      mark handled without sending (spam, no reply needed)

Instagram's API cannot comment on OTHER accounts' posts. Those comments are posted by hand (Kainaat or Claude in the signed-in
browser) from the approved list. A DM can only be sent within 24 h of the customer's last message.
"""
import argparse, json, os, sys, time, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ig  # token, call(), ACCOUNTS, out(), die()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "engagement", "state.json")
TARGETS = os.path.join(ROOT, "engagement", "targets.json")


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save_state(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=1, ensure_ascii=False)


def parse_time(s):
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")


def inbox(a, hours):
    i = ig.acct(a)
    st = load(STATE, {}); handled = set(st.get(a, {}).get("dm", []))
    r = ig.call("GET", f"{i}/conversations", {"platform": "instagram", "limit": 50, "fields":
        "id,updated_time,participants,messages.limit(6){id,message,from,created_time,attachments,shares,story,reply_to}"})
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)
    items = []
    for c in r.get("data", []):
        msgs = (c.get("messages") or {}).get("data", [])
        if not msgs:
            continue
        last = msgs[0]  # newest first
        who = last.get("from", {})
        if who.get("id") == i:
            continue  # we spoke last
        when = parse_time(last["created_time"])
        if when < cutoff or last["id"] in handled:
            continue
        thread = [{"from": m.get("from", {}).get("username"), "at": m["created_time"], "text": m.get("message"),
                   "attachments": [x.get("type") or x.get("mime_type") for x in (m.get("attachments", {}) or {}).get("data", [])]
                   if isinstance(m.get("attachments"), dict) else None,
                   "story": ("mention" if (m.get("story") or {}).get("mention") else "reply" if (m.get("story") or {}).get("reply_to") else None),
                   "story_link": ((m.get("story") or {}).get("mention") or {}).get("link"),  # signed CDN link, expires in 24 h; never commit it
                   "shared_post": bool(m.get("shares"))} for m in reversed(msgs)]
        items.append({"msg_id": last["id"], "igsid": who.get("id"), "username": who.get("username"),
                      "last_at": last["created_time"], "reply_window_open": (dt.datetime.now(dt.timezone.utc) - when).total_seconds() < 86400,
                      "thread": thread})
    ig.out({"account": a, "needs_reply": len(items), "items": items})


def comments(a, posts):
    i = ig.acct(a)
    st = load(STATE, {}); handled = set(st.get(a, {}).get("comment", []))
    media = ig.call("GET", f"{i}/media", {"limit": posts, "fields": "id,permalink,caption,timestamp,comments_count"}).get("data", [])
    items = []
    for m in media:
        if not m.get("comments_count"):
            continue
        cs = ig.call("GET", f"{m['id']}/comments", {"limit": 50, "fields":
            "id,text,username,timestamp,like_count,replies.limit(25){id,username}"}).get("data", [])
        for c in cs:
            if c["id"] in handled or c.get("username") == a:
                continue
            if any(r.get("username") == a for r in (c.get("replies") or {}).get("data", [])):
                continue  # already replied
            items.append({"comment_id": c["id"], "username": c.get("username"), "text": c.get("text"), "at": c.get("timestamp"),
                          "post": m["permalink"], "post_caption": (m.get("caption") or "")[:80]})
    ig.out({"account": a, "needs_reply": len(items), "items": items})


def tags(a, limit):
    i = ig.acct(a)
    r = ig.call("GET", f"{i}/tags", {"limit": limit, "fields": "id,username,caption,permalink,timestamp,media_type"})
    st = load(STATE, {}); seen = set(st.get(a, {}).get("tags_seen", []))
    items = [{"id": x["id"], "by": x.get("username"), "at": x.get("timestamp"), "new": x["id"] not in seen,
              "permalink": x.get("permalink"), "caption": (x.get("caption") or "")[:140]} for x in r.get("data", [])]
    ig.out({"account": a, "new": sum(1 for x in items if x["new"]), "items": items})


def watch_one(a, user, n):
    i = ig.acct(a)
    r = ig.call("GET", i, {"fields": f"business_discovery.username({user}){{username,followers_count,"
                           f"media.limit({n}){{caption,permalink,timestamp,like_count,comments_count,media_type}}}}"})
    d = r.get("business_discovery", {})
    return {"username": d.get("username", user), "followers": d.get("followers_count"),
            "posts": [{"at": m.get("timestamp"), "permalink": m.get("permalink"), "likes": m.get("like_count"),
                       "comments": m.get("comments_count"), "caption": (m.get("caption") or "")[:140]}
                      for m in (d.get("media") or {}).get("data", [])]}


def watch_all(a, group=None):
    """Newest posts of every active target meant for this account (targets with audience IN never go to ayurpet_global)."""
    t = [x for x in load(TARGETS, {"targets": []})["targets"]
         if a in x.get("accounts", [a]) and x.get("status", "active") == "active" and (not group or x.get("group") == group)]
    done = {o["permalink"] for o in load(STATE, {}).get("outbound", []) if o.get("acct") == a}
    res = []
    for x in t:
        try:
            r = watch_one(a, x["username"], 2); r["group"] = x.get("group"); r["note"] = x.get("note")
            for q in r["posts"]:
                q["we_commented"] = q["permalink"] in done
            res.append(r)
        except SystemExit:
            res.append({"username": x["username"], "group": x.get("group"), "error": "not a public business/creator account, or private; check by hand"})
        time.sleep(1)
    ig.out({"checked": len(res), "items": res})


def log_outbound(a, target, permalink, text):
    """Record a comment we posted by hand on someone else's post, so the daily quota and 'already commented' work."""
    st = load(STATE, {}); st.setdefault("outbound", []).append(
        {"date": dt.date.today().isoformat(), "acct": a, "target": target, "permalink": permalink, "text": text})
    save_state(st)
    today = sum(1 for o in st["outbound"] if o["acct"] == a and o["date"] == dt.date.today().isoformat())
    ig.out({"logged": permalink, "comments_today_for_account": today})


def mark_tags_seen(a):
    i = ig.acct(a)
    ids = [x["id"] for x in ig.call("GET", f"{i}/tags", {"limit": 50, "fields": "id"}).get("data", [])]
    st = load(STATE, {}); st.setdefault(a, {}).setdefault("tags_seen", [])
    st[a]["tags_seen"] = sorted(set(st[a]["tags_seen"]) | set(ids)); save_state(st)
    ig.out({"tags_marked_seen": len(ids)})


def mark(a, kind, id_):
    st = load(STATE, {}); st.setdefault(a, {}).setdefault(kind, [])
    if id_ not in st[a][kind]:
        st[a][kind].append(id_)
    save_state(st)


def text_of(path):
    with open(path, encoding="utf-8") as f:
        t = f.read().strip()
    if "—" in t or "–" in t:
        ig.die("no em dashes or en dashes in anything we send (brand rule)")
    return t


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    x = sp.add_parser("inbox"); x.add_argument("acct"); x.add_argument("--hours", type=int, default=48)
    x = sp.add_parser("comments"); x.add_argument("acct"); x.add_argument("--posts", type=int, default=12)
    x = sp.add_parser("tags"); x.add_argument("acct"); x.add_argument("--limit", type=int, default=10)
    x = sp.add_parser("watch"); x.add_argument("acct"); x.add_argument("user"); x.add_argument("--n", type=int, default=3)
    x = sp.add_parser("watch-all"); x.add_argument("acct"); x.add_argument("--group")
    x = sp.add_parser("log-outbound"); x.add_argument("acct"); x.add_argument("--target", required=True)
    x.add_argument("--permalink", required=True); x.add_argument("--text", required=True)
    x = sp.add_parser("tags-seen"); x.add_argument("acct")
    x = sp.add_parser("dm-send"); x.add_argument("acct"); x.add_argument("--to", required=True); x.add_argument("--text-file", required=True)
    x.add_argument("--msg-id"); x.add_argument("--send", action="store_true")
    x = sp.add_parser("reply"); x.add_argument("acct"); x.add_argument("--comment", required=True); x.add_argument("--text-file", required=True); x.add_argument("--send", action="store_true")
    x = sp.add_parser("done"); x.add_argument("acct"); x.add_argument("--kind", choices=["dm", "comment"], required=True); x.add_argument("--id", required=True)
    a = p.parse_args()
    if a.cmd == "inbox": inbox(a.acct, a.hours)
    elif a.cmd == "comments": comments(a.acct, a.posts)
    elif a.cmd == "tags": tags(a.acct, a.limit)
    elif a.cmd == "watch": ig.out(watch_one(a.acct, a.user.lstrip("@"), a.n))
    elif a.cmd == "watch-all": watch_all(a.acct, a.group)
    elif a.cmd == "log-outbound": log_outbound(a.acct, a.target.lstrip("@"), a.permalink, a.text)
    elif a.cmd == "tags-seen": mark_tags_seen(a.acct)
    elif a.cmd == "done": mark(a.acct, a.kind, a.id); ig.out({"marked": a.id})
    elif a.cmd == "dm-send":
        t = text_of(a.text_file)
        if not a.send:
            ig.out({"dry_run": True, "to": a.to, "text": t}); return
        r = ig.call("POST", f"{ig.acct(a.acct)}/messages", {"recipient": {"id": a.to}, "message": {"text": t}})
        if a.msg_id: mark(a.acct, "dm", a.msg_id)
        ig.out({"sent": True, **r})
    elif a.cmd == "reply":
        t = text_of(a.text_file)
        if not a.send:
            ig.out({"dry_run": True, "comment": a.comment, "text": t}); return
        r = ig.call("POST", f"{a.comment}/replies", {"message": t})
        mark(a.acct, "comment", a.comment)
        ig.out({"sent": True, **r})


if __name__ == "__main__":
    main()
