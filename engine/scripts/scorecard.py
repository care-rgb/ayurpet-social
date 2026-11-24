#!/usr/bin/env python3
"""Weekly scorecard for our own two Instagram accounts (@ayurpetofficial India, @ayurpet_global).

  python3 scripts/scorecard.py              # posts from the last 30 days
  python3 scripts/scorecard.py --days 60

For every post: views, reach, saves, shares, sends+saves per 100 reached, views against the account's own normal,
reel skip rate and average watch time, follows from the post (feed posts). Joins ledger/tags.csv so we can see
which format, hook and language won. Labels each post WINNER / ok / DUD against that account's own median.
Also logs followers per day to ledger/followers.csv and shows progress to 10,000 by 22 Dec 2026.

Writes ledger/SCORECARD_<date>.md and ledger/scorecard_<date>.csv. Read-only.
"""
import argparse, csv, datetime as dt, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta import ACCOUNTS, MARKET, MetaError, first_line, get, here, median, shortcode

GOAL, GOAL_DATE = 10000, dt.date(2026, 12, 22)
REEL_METRICS = ["views", "reach", "saved", "shares", "likes", "comments", "total_interactions",
                "ig_reels_avg_watch_time", "reels_skip_rate"]
FEED_METRICS = ["views", "reach", "saved", "shares", "likes", "comments", "total_interactions",
                "follows", "profile_visits"]
CORE = ["views", "reach", "saved", "shares"]


def insights(media_id, metrics):
    """Ask for all metrics; if Meta refuses one, drop the optional ones and retry with the core set."""
    for ms in (metrics, [m for m in metrics if m not in ("reels_skip_rate", "follows", "profile_visits")], CORE):
        try:
            r = get(f"{media_id}/insights", {"metric": ",".join(ms)})
            out = {}
            for d in r.get("data", []):
                v = d.get("values", [{}])[0].get("value") if d.get("values") else d.get("total_value", {}).get("value")
                out[d["name"]] = v
            return out
        except MetaError:
            continue
    return {}


def follows_unfollows(ig, since, until):
    try:
        r = get(f"{ig}/insights", {"metric": "follows_and_unfollows", "period": "day", "metric_type": "total_value",
                                   "breakdown": "follow_type", "since": int(since.timestamp()),
                                   "until": int(until.timestamp())})
        res = r["data"][0]["total_value"]["breakdowns"][0]["results"]
        d = {x["dimension_values"][0]: x["value"] for x in res}
        return d.get("FOLLOWER"), d.get("NON_FOLLOWER")
    except (MetaError, KeyError, IndexError):
        return None, None


def load_tags():
    p = here("ledger", "tags.csv")
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return {r["shortcode"].strip(): r for r in csv.DictReader(f) if r.get("shortcode")}


def rate(a, b):
    return round(a / b * 100, 2) if a is not None and b else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=30)
    a = ap.parse_args()
    today = dt.date.today()
    now = dt.datetime.now(dt.timezone.utc)
    tags = load_tags()
    rows, acct = [], []

    for name, ig in ACCOUNTS.items():
        info = get(ig, {"fields": "username,followers_count,media_count"})
        fol = info.get("followers_count")
        new_f, lost_f = follows_unfollows(ig, now - dt.timedelta(days=28), now)
        acct.append({"date": today.isoformat(), "account": name, "followers": fol,
                     "follows_28d": new_f, "unfollows_28d": lost_f})
        media = get(f"{ig}/media", {"fields": "id,caption,media_type,media_product_type,timestamp,permalink,"
                                              "like_count,comments_count", "limit": 50}).get("data", [])
        for m in media:
            ts = dt.datetime.strptime(m["timestamp"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
            age = (now - ts).days
            if age > a.days:
                continue
            reel = m.get("media_product_type") == "REELS"
            k = "reel" if reel else ("carousel" if m.get("media_type") == "CAROUSEL_ALBUM" else "photo")
            ins = insights(m["id"], REEL_METRICS if reel else FEED_METRICS)
            time.sleep(0.2)
            sc = shortcode(m.get("permalink"))
            t = tags.get(sc, {})
            reach = ins.get("reach")
            watch = ins.get("ig_reels_avg_watch_time")
            rows.append({"account": name, "market": MARKET[name], "posted": m["timestamp"][:10], "age_days": age,
                         "type": k, "shortcode": sc, "views": ins.get("views"), "reach": reach,
                         "likes": ins.get("likes", m.get("like_count")), "comments": ins.get("comments", m.get("comments_count")),
                         "saves": ins.get("saved"), "shares": ins.get("shares"),
                         "shares_per_100": rate(ins.get("shares"), reach), "saves_per_100": rate(ins.get("saved"), reach),
                         "keep_per_100": rate((ins.get("shares") or 0) + (ins.get("saved") or 0), reach),
                         "avg_watch_s": round(watch / 1000, 1) if watch else None,
                         "skip_rate": ins.get("reels_skip_rate"), "follows": ins.get("follows"),
                         "profile_visits": ins.get("profile_visits"),
                         "format": t.get("format", ""), "hook": t.get("hook", ""), "language": t.get("language", ""),
                         "lane": t.get("lane", ""), "replica_of": t.get("replica_of", ""),
                         "permalink": m.get("permalink", ""), "caption_line1": first_line(m.get("caption"), 70)})

    # Judge each post against its own account and type (reels vs reels, carousels vs carousels).
    for r in rows:
        peers = [x for x in rows if x["account"] == r["account"] and x["type"] == r["type"] and x is not r]
        mv = median([x["views"] for x in peers])
        mk = median([x["keep_per_100"] for x in peers])
        r["x_views"] = round(r["views"] / mv, 1) if r["views"] is not None and mv else None
        xk = (r["keep_per_100"] / mk) if r["keep_per_100"] is not None and mk else None
        if r["age_days"] < 3:
            r["verdict"] = "too new"
        elif (r["x_views"] or 0) >= 2 or (xk or 0) >= 2:
            r["verdict"] = "WINNER"
        elif r["x_views"] is not None and r["x_views"] <= 0.5 and (xk is None or xk < 1):
            r["verdict"] = "DUD"
        else:
            r["verdict"] = "ok"

    led = here("ledger"); os.makedirs(led, exist_ok=True)
    ff = os.path.join(led, "followers.csv"); new = not os.path.exists(ff)
    with open(ff, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(acct[0])); new and w.writeheader(); w.writerows(acct)
    if rows:
        with open(os.path.join(led, f"scorecard_{today}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    total = sum(x["followers"] or 0 for x in acct)
    days_left = (GOAL_DATE - today).days
    need = round((GOAL - total) / days_left) if days_left > 0 else None
    L = [f"# Scorecard {today}", "",
         f"Followers: {total:,} combined (" + ", ".join(f"@{x['account']} {x['followers']:,}" for x in acct) + ").",
         f"Goal {GOAL:,} by {GOAL_DATE:%d %b %Y}: {GOAL - total:,} to go in {days_left} days = about {need} a day."
         if need else "Goal date passed.", ""]
    for x in acct:
        if x["follows_28d"] is not None:
            L.append(f"@{x['account']} last 28 days: +{x['follows_28d']} follows, -{x['unfollows_28d']} unfollows.")
    L += ["", "Keep = shares + saves per 100 people reached. WINNER = 2x the account's normal on views or keep. "
          "DUD = half the normal views or less.", ""]
    for name in ACCOUNTS:
        rs = sorted([r for r in rows if r["account"] == name], key=lambda r: r["posted"], reverse=True)
        if not rs:
            continue
        L += [f"## @{name}", "",
              "| posted | type | verdict | views | x normal | reach | keep/100 | shares/100 | watch s | skip | follows | format / hook | first line |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in rs:
            fh = " / ".join(v for v in (r["format"], r["hook"]) if v) or "untagged"
            L.append(f"| {r['posted']} | {r['type']} | {r['verdict']} | {r['views'] or ''} | {r['x_views'] or ''} "
                     f"| {r['reach'] or ''} | {r['keep_per_100'] or ''} | {r['shares_per_100'] or ''} "
                     f"| {r['avg_watch_s'] or ''} | {r['skip_rate'] or ''} | {r['follows'] or ''} | {fh} "
                     f"| {r['caption_line1'].replace('|', '/')} |")
        L.append("")
    untagged = [r for r in rows if not r["format"]]
    if untagged:
        L += [f"{len(untagged)} posts have no tag yet. Add them to ledger/tags.csv (shortcode is the code in the link) "
              "so next week's scorecard can say which format and hook won.", ""]
    md = os.path.join(led, f"SCORECARD_{today}.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"wrote {md}: {len(rows)} posts, {total:,} followers, need ~{need}/day")


if __name__ == "__main__":
    main()
