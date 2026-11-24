#!/usr/bin/env python3
"""Weekly outlier pull: which posts on the watch-list pages beat their own page's normal by 3x or more.

  python3 scripts/outliers.py                 # all pages in watchlist.csv, posts 2-30 days old
  python3 scripts/outliers.py --days 60       # look further back (good for the first run)
  python3 scripts/outliers.py --check         # only check that every handle in watchlist.csv can be read

How it judges (Meta's business_discovery, free, read-only):
- Reels: views / the page's median reel views over its last 30 posts (the post itself left out).
- Carousels and photos: likes / the page's median feed likes (Meta does not give other pages' feed views).
- 3x = signal, 5x = strong, 10x = breakout. Posts under 2 days old are skipped (still climbing).
Only business and creator accounts can be read. Personal accounts show "cannot read" in --check.

Writes research/outliers/OUTLIERS_<date>.md (the list to watch) and OUTLIERS_<date>.csv (every post scored),
and appends page sizes to research/outliers/pages.csv.
"""
import argparse, csv, datetime as dt, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta import ASKER, MetaError, first_line, get, here, median

FIELDS = ("username,followers_count,media_count,"
          "media.limit({n}){{id,caption,media_type,media_product_type,like_count,comments_count,view_count,timestamp,permalink}}")


def read_watchlist(path):
    with open(path, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("handle") and not r["handle"].startswith("#")]
    return rows


def pull(handle, n=30):
    r = get(ASKER, {"fields": "business_discovery.username(%s){%s}" % (handle.lstrip("@"), FIELDS.format(n=n))})
    b = r["business_discovery"]
    return b, b.get("media", {}).get("data", [])


def kind(m):
    if m.get("media_product_type") == "REELS" or (m.get("media_type") == "VIDEO" and m.get("view_count")):
        return "reel"
    return "carousel" if m.get("media_type") == "CAROUSEL_ALBUM" else "photo"


def tier(x):
    return "breakout" if x >= 10 else "strong" if x >= 5 else "signal" if x >= 3 else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--watchlist", default=here("watchlist.csv"))
    ap.add_argument("--days", type=int, default=30, help="only score posts up to this many days old (default 30)")
    ap.add_argument("--min-age", type=int, default=2)
    ap.add_argument("--min-x", type=float, default=3.0, help="lowest multiple to list (default 3)")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    today = dt.date.today().isoformat()
    now = dt.datetime.now(dt.timezone.utc)
    pages, scored, unreadable = [], [], []
    for w in read_watchlist(a.watchlist):
        h = w["handle"].lstrip("@").strip()
        try:
            b, media = pull(h)
        except (MetaError, KeyError) as e:
            unreadable.append((h, str(e)[:90])); print(f"  cannot read @{h}: {str(e)[:90]}", file=sys.stderr)
            continue
        finally:
            time.sleep(0.5)
        reels = [m for m in media if kind(m) == "reel" and m.get("view_count") is not None]
        feed = [m for m in media if kind(m) != "reel"]
        med_v = median([m["view_count"] for m in reels])
        med_l = median([m.get("like_count") for m in feed])
        pages.append({"date": today, "handle": h, "market": w.get("market", ""), "lane": w.get("lane", ""),
                      "followers": b.get("followers_count"), "posts_read": len(media), "median_reel_views": med_v,
                      "median_feed_likes": med_l})
        print(f"  @{h}: {b.get('followers_count')} followers, {len(reels)} reels (median {med_v}), "
              f"{len(feed)} feed (median likes {med_l})", file=sys.stderr)
        if a.check:
            continue
        for m in media:
            ts = dt.datetime.strptime(m["timestamp"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
            age = (now - ts).days
            if age < a.min_age or age > a.days:
                continue
            k = kind(m)
            if k == "reel" and m.get("view_count") is not None:
                base = median([x["view_count"] for x in reels if x["id"] != m["id"]])
                val, metric = m["view_count"], "views"
            else:
                base = median([x.get("like_count") for x in feed if x["id"] != m["id"]])
                val, metric = m.get("like_count"), "likes"
            if not base or val is None:
                continue
            x = round(val / base, 1)
            eng = round(((m.get("like_count") or 0) + (m.get("comments_count") or 0)) / m["view_count"] * 100, 2) \
                if m.get("view_count") else ""
            scored.append({"date_pulled": today, "handle": h, "market": w.get("market", ""), "lane": w.get("lane", ""),
                           "followers": b.get("followers_count"), "type": k, "posted": m["timestamp"][:10],
                           "age_days": age, "metric": metric, "value": val, "page_median": round(base),
                           "x_median": x, "tier": tier(x), "likes": m.get("like_count"),
                           "comments": m.get("comments_count"), "eng_per_100_views": eng,
                           "permalink": m.get("permalink", ""), "caption_line1": first_line(m.get("caption"))})

    out = here("research", "outliers"); os.makedirs(out, exist_ok=True)
    pf = os.path.join(out, "pages.csv"); new = not os.path.exists(pf)
    if pages and not a.check:
        with open(pf, "a", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=list(pages[0])); new and wr.writeheader(); wr.writerows(pages)
    if a.check:
        print(f"\n{len(pages)} readable, {len(unreadable)} cannot be read: " +
              ", ".join(f"@{h}" for h, _ in unreadable))
        return
    scored.sort(key=lambda r: r["x_median"], reverse=True)
    if scored:
        with open(os.path.join(out, f"OUTLIERS_{today}.csv"), "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=list(scored[0])); wr.writeheader(); wr.writerows(scored)

    hits = [r for r in scored if r["x_median"] >= a.min_x]
    lines = [f"# Outliers {today}", "",
             f"{len(pages)} pages read, {len(scored)} posts scored (2 to {a.days} days old), "
             f"{len(hits)} at {a.min_x:g}x their page's normal or more.",
             "Reels are judged on views, carousels and photos on likes. Watch every one before deciding anything.", ""]
    for mk, label in (("in", "India"), ("gl", "Global"), ("ae", "UAE"), ("both", "Both markets")):
        rows = [r for r in hits if r["market"] == mk]
        if not rows:
            continue
        lines += [f"## {label}", "", "| x normal | page | type | views/likes | posted | first line | link |",
                  "|---|---|---|---|---|---|---|"]
        for r in rows[:25]:
            cap = r["caption_line1"].replace("|", "/")
            lines.append(f"| {r['x_median']}x {r['tier']} | @{r['handle']} | {r['type']} | {r['value']:,} {r['metric']} "
                         f"| {r['posted']} | {cap} | {r['permalink']} |")
        lines.append("")
    if unreadable:
        lines += ["## Could not read (fix or remove in watchlist.csv)", ""] + \
                 [f"- @{h}: {e}" for h, e in unreadable] + [""]
    md = os.path.join(out, f"OUTLIERS_{today}.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nwrote {md} ({len(hits)} outliers)")


if __name__ == "__main__":
    main()
