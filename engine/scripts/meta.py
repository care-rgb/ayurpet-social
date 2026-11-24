"""Shared Meta Graph API helper for the social engine. Python standard library only (works on Mac, Windows, cloud).

Token: env META_IG_TOKEN (the same AyurPet system-user token scripts/ig.py in care-rgb/ayurpet-social uses).
- Laptop: set META_IG_TOKEN to the token itself (from the password manager). Never paste it in a chat or a file here.
- Cloud environment "AyurPet Reels": META_IG_TOKEN=proxy, and the network secret adds the header on the way out.
Read-only: nothing in this engine posts, edits or deletes anything.
"""
import http.client, json, os, sys, time, urllib.error, urllib.parse, urllib.request

VER = os.environ.get("GRAPH_VERSION", "v23.0")
BASE = f"https://graph.facebook.com/{VER}"
ACCOUNTS = {"ayurpetofficial": "17841472849482734", "ayurpet_global": "17841465833626335"}
MARKET = {"ayurpetofficial": "in", "ayurpet_global": "gl"}
# business_discovery is asked through one of our own accounts; either works.
ASKER = ACCOUNTS["ayurpet_global"]


class MetaError(Exception):
    pass


def _token():
    t = os.environ.get("META_IG_TOKEN", "").strip()
    if not t:
        sys.exit("META_IG_TOKEN is not set. Laptop: set it to the token from the password manager. "
                 "Cloud: the 'AyurPet Reels' environment sets it to 'proxy'. Never paste the token in chat.")
    if t.lower() == "proxy":
        return None
    if not t.isascii() or any(c.isspace() for c in t) or len(t) < 100:
        sys.exit("META_IG_TOKEN does not look like a Meta token (spaces, wrong characters or too short).")
    return t


def get(path, params=None):
    """GET one Graph API path. Raises MetaError with Meta's message; retries transient errors twice."""
    params = {k: str(v) for k, v in (params or {}).items() if v is not None}
    headers = {}
    tok = _token()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    url = f"{BASE}/{path.lstrip('/')}" + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read().decode()).get("error", {})
            except Exception:
                err = {"message": f"HTTP {e.code}"}
            if (err.get("is_transient") or e.code >= 500) and attempt < 2:
                time.sleep(15 * (attempt + 1)); continue
            raise MetaError(err.get("message") or f"HTTP {e.code}")
        except urllib.error.URLError as e:
            if attempt < 2:
                time.sleep(15); continue
            raise MetaError(f"network error: {e.reason}")
        except (http.client.HTTPException, ConnectionError, TimeoutError) as e:
            # dropped or cut-short responses happen on big pages; try again
            if attempt < 2:
                time.sleep(5 * (attempt + 1)); continue
            raise MetaError(f"network error: {type(e).__name__}")


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def shortcode(permalink):
    """https://www.instagram.com/reel/ABC123/ -> ABC123"""
    parts = [p for p in (permalink or "").split("/") if p]
    return parts[-1] if parts else ""


def first_line(caption, n=90):
    line = (caption or "").strip().split("\n")[0]
    return (line[:n] + "...") if len(line) > n else line


def here(*p):
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), *p)
