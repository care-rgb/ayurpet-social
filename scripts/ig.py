#!/usr/bin/env python3
"""AyurPet Instagram + Facebook Page posting and reading, straight on Meta's Graph API (no Zapier).

Token: env META_IG_TOKEN, a Business system-user token for AyurPet's business with these permissions:
instagram_basic, instagram_content_publish, instagram_manage_insights, instagram_manage_comments, pages_show_list,
pages_read_engagement, pages_manage_posts. It is read from the environment only and never printed.
Python standard library only, so any routine or laptop can run it: python3 scripts/ig.py <command> ...

Accounts: ayurpetofficial (India), ayurpet_global, or a numeric Instagram id. Facebook page: theayurpet or an id.

Read:
  ig.py check                                   token works? permissions, both accounts' followers
  ig.py account <acct>                          username, followers, media count (JSON)
  ig.py media <acct> [--limit 25]               recent posts with likes/comments (JSON lines)
  ig.py insights <media_id>                     views, reach, shares (sends), saves, watch time (JSON)
  ig.py account-insights <acct> [--days 7]      follows/unfollows, reach, profile views over the last N days (JSON)
  ig.py status <container_id>                   container processing status
Write (a container is created and processed; nothing goes live without --publish):
  ig.py reel <acct> --video-url URL --caption-file F [--cover-url URL] [--thumb-offset MS] [--collab a,b]
            [--user-tag a,b] [--no-feed] [--publish]
  ig.py carousel <acct> --image-url URL [--image-url URL ...] --caption-file F [--collab a,b] [--publish]
  ig.py story <acct> (--video-url URL | --image-url URL) [--publish]
  ig.py publish <acct> <container_id>
  ig.py fb-photos <page> --image-url URL [...] --message-file F [--publish]    multi-photo Facebook Page post
Every command prints JSON on stdout. Errors go to stderr with Meta's message and exit code 2.
"""
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request

VER = os.environ.get("GRAPH_VERSION", "v23.0")
BASE = f"https://graph.facebook.com/{VER}"
ACCOUNTS = {"ayurpetofficial": "17841472849482734", "ayurpet_global": "17841465833626335"}
PAGES = {"theayurpet": "588374454353569"}


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr); sys.exit(2)


def token():
    t = os.environ.get("META_IG_TOKEN", "").strip()
    if not t:
        die("META_IG_TOKEN is not set (add it to this environment's variables; never paste it in chat)")
    return t


def call(method, path, params=None, tok=None):
    """One Graph API call; the token travels in the Authorization header, never in a printed URL."""
    params = {k: (json.dumps(v) if isinstance(v, (list, dict)) else str(v)) for k, v in (params or {}).items()
              if v is not None}
    url = f"{BASE}/{path.lstrip('/')}"
    data = None
    if method == "GET":
        url += ("?" + urllib.parse.urlencode(params)) if params else ""
    else:
        data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=method, headers={"Authorization": f"Bearer {tok or token()}"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read().decode()).get("error", {})
            except Exception:
                err = {"message": f"HTTP {e.code}"}
            transient = err.get("is_transient") or e.code >= 500
            if transient and attempt < 2:
                time.sleep(20 * (attempt + 1)); continue
            die(f"{method} {path}: {err.get('message')} (code {err.get('code')}, subcode {err.get('error_subcode')}, "
                f"trace {err.get('fbtrace_id')})")
        except urllib.error.URLError as e:
            if attempt < 2:
                time.sleep(20); continue
            die(f"{method} {path}: network error {e.reason}")


def acct(a):
    return ACCOUNTS.get(a.lstrip("@"), a) if not a.isdigit() else a


def out(obj):
    print(json.dumps(obj, ensure_ascii=False))


def wait(container, minutes=15):
    """Poll until Instagram has processed the container (FINISHED) or give up with its status."""
    deadline = time.time() + minutes * 60
    while True:
        s = call("GET", container, {"fields": "status_code,status"})
        if s.get("status_code") == "FINISHED":
            return s
        if s.get("status_code") in ("ERROR", "EXPIRED") or time.time() > deadline:
            die(f"container {container} {s.get('status_code')}: {s.get('status')}")
        time.sleep(15)


def publish(ig, container):
    m = call("POST", f"{ig}/media_publish", {"creation_id": container})
    info = call("GET", m["id"], {"fields": "id,permalink,media_product_type,timestamp"})
    try:  # the collaborator invite status, where Instagram reports it
        info["collaborators"] = call("GET", f"{m['id']}/collaborators").get("data")
    except SystemExit:
        pass
    return info


def caption(path):
    if not path:
        return None
    with open(path, encoding="utf-8") as f:
        return f.read().rstrip("\n")


def finish(ig, container, do_publish, kind):
    wait(container)
    if do_publish:
        out({"result": "POSTED", "kind": kind, **publish(ig, container)})
    else:
        out({"result": "READY_NOT_PUBLISHED", "kind": kind, "container": container,
             "note": "processed fine; run again with --publish (or ig.py publish) to post. Unpublished containers expire in 24 h"})


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("check")
    x = sp.add_parser("account"); x.add_argument("acct")
    x = sp.add_parser("media"); x.add_argument("acct"); x.add_argument("--limit", type=int, default=25)
    x = sp.add_parser("insights"); x.add_argument("media_id")
    x = sp.add_parser("account-insights"); x.add_argument("acct"); x.add_argument("--days", type=int, default=7)
    x = sp.add_parser("status"); x.add_argument("container")
    x = sp.add_parser("publish"); x.add_argument("acct"); x.add_argument("container")
    x = sp.add_parser("reel"); x.add_argument("acct"); x.add_argument("--video-url", required=True)
    x.add_argument("--caption-file", required=True); x.add_argument("--cover-url"); x.add_argument("--thumb-offset", type=int)
    x.add_argument("--collab", default=""); x.add_argument("--user-tag", default=""); x.add_argument("--no-feed", action="store_true")
    x.add_argument("--publish", action="store_true")
    x = sp.add_parser("carousel"); x.add_argument("acct"); x.add_argument("--image-url", action="append", required=True)
    x.add_argument("--caption-file", required=True); x.add_argument("--collab", default=""); x.add_argument("--publish", action="store_true")
    x = sp.add_parser("story"); x.add_argument("acct"); x.add_argument("--video-url"); x.add_argument("--image-url")
    x.add_argument("--publish", action="store_true")
    x = sp.add_parser("fb-photos"); x.add_argument("page"); x.add_argument("--image-url", action="append", required=True)
    x.add_argument("--message-file", required=True); x.add_argument("--publish", action="store_true")
    a = p.parse_args()
    names = lambda s: [u.strip().lstrip("@") for u in s.split(",") if u.strip()]

    if a.cmd == "check":
        me = call("GET", "me", {"fields": "id,name"})
        try:
            perms = [q["permission"] for q in call("GET", "me/permissions").get("data", []) if q.get("status") == "granted"]
        except SystemExit:
            perms = ["(could not list; system-user tokens may not expose me/permissions)"]
        accts = {n: call("GET", i, {"fields": "username,followers_count,media_count"}) for n, i in ACCOUNTS.items()}
        need = {"instagram_basic", "instagram_content_publish", "instagram_manage_insights", "pages_manage_posts"}
        out({"token_for": me.get("name"), "permissions": perms,
             "missing": sorted(need - set(perms)) if perms and not perms[0].startswith("(") else "unknown", "accounts": accts})
    elif a.cmd == "account":
        out(call("GET", acct(a.acct), {"fields": "username,followers_count,follows_count,media_count"}))
    elif a.cmd == "media":
        r = call("GET", f"{acct(a.acct)}/media", {"limit": a.limit, "fields":
                 "id,timestamp,media_product_type,media_type,permalink,like_count,comments_count,caption"})
        for m in r.get("data", []):
            out(m)
    elif a.cmd == "insights":
        kind = call("GET", a.media_id, {"fields": "media_product_type"}).get("media_product_type")
        metrics = "views,reach,shares,saved,likes,comments,total_interactions"
        if kind == "REELS":
            metrics += ",ig_reels_avg_watch_time,ig_reels_video_view_total_time"
        r = call("GET", f"{a.media_id}/insights", {"metric": metrics})
        out({"media_id": a.media_id, "type": kind, **{m["name"]: m["values"][0]["value"] for m in r.get("data", [])}})
    elif a.cmd == "account-insights":
        until = int(time.time()); since = until - a.days * 86400
        r = call("GET", f"{acct(a.acct)}/insights", {"metric": "follows_and_unfollows,reach,profile_views,accounts_engaged",
                 "period": "day", "metric_type": "total_value", "since": since, "until": until})
        res = {}
        for m in r.get("data", []):
            tv = m.get("total_value", {})
            res[m["name"]] = tv.get("value") if not tv.get("breakdowns") else tv["breakdowns"]
        out({"account": a.acct, "days": a.days, **res})
    elif a.cmd == "status":
        out(call("GET", a.container, {"fields": "status_code,status"}))
    elif a.cmd == "publish":
        wait(a.container); out({"result": "POSTED", **publish(acct(a.acct), a.container)})
    elif a.cmd == "reel":
        ig = acct(a.acct)
        c = call("POST", f"{ig}/media", {"media_type": "REELS", "video_url": a.video_url, "caption": caption(a.caption_file),
                 "cover_url": a.cover_url, "thumb_offset": a.thumb_offset, "share_to_feed": "false" if a.no_feed else "true",
                 "collaborators": names(a.collab) or None,
                 "user_tags": [{"username": u} for u in names(a.user_tag)] or None})["id"]
        finish(ig, c, a.publish, "REELS")
    elif a.cmd == "carousel":
        ig = acct(a.acct)
        if not 2 <= len(a.image_url) <= 20:
            die(f"a carousel needs 2 to 20 images, got {len(a.image_url)}")
        kids = [call("POST", f"{ig}/media", {"image_url": u, "is_carousel_item": "true"})["id"] for u in a.image_url]
        for k in kids:
            wait(k, 5)
        c = call("POST", f"{ig}/media", {"media_type": "CAROUSEL", "children": ",".join(kids),
                 "caption": caption(a.caption_file), "collaborators": names(a.collab) or None})["id"]
        finish(ig, c, a.publish, "CAROUSEL")
    elif a.cmd == "story":
        if bool(a.video_url) == bool(a.image_url):
            die("give exactly one of --video-url or --image-url")
        ig = acct(a.acct)
        c = call("POST", f"{ig}/media", {"media_type": "STORIES", "video_url": a.video_url, "image_url": a.image_url})["id"]
        finish(ig, c, a.publish, "STORIES")
    elif a.cmd == "fb-photos":
        page = PAGES.get(a.page, a.page)
        ptok = call("GET", page, {"fields": "access_token,name"})
        if "access_token" not in ptok:
            die("no page token: the system user needs the page as an asset with pages_manage_posts")
        if not a.publish:
            out({"result": "READY_NOT_PUBLISHED", "page": ptok.get("name"), "photos": len(a.image_url),
                 "note": "page token works; run with --publish to post"}); return
        ids = [call("POST", f"{page}/photos", {"url": u, "published": "false"}, tok=ptok["access_token"])["id"]
               for u in a.image_url[:10]]
        params = {"message": caption(a.message_file)}
        for i, fid in enumerate(ids):
            params[f"attached_media[{i}]"] = {"media_fbid": fid}
        post = call("POST", f"{page}/feed", params, tok=ptok["access_token"])
        out({"result": "POSTED", "page": ptok.get("name"), "post_id": post.get("id")})


if __name__ == "__main__":
    main()
