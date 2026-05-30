# -*- coding: utf-8 -*-
"""
Fetch one stock photo per DISH for the Khmer menu — with a relevance gate.

- One attempt per recipe (slug-keyed), so protein variants don't share misleading
  photos. A photo is only accepted if its alt-text or page URL contains a clearly
  Cambodian/Khmer term ("cambodian", "khmer", "amok", "lok lak", "kuy teav",
  "prahok", "samlor", "kreung", etc.). Otherwise the dish keeps the page's emoji
  placeholder — honest is better than wrong.
- Resumable: skips dishes that already have a file at images/dishes/<slug>.jpg.
- Writes attribution.json and credits.html (required by both providers' terms).

Get a FREE API key (2 min):
  Pexels   -> https://www.pexels.com/api/   (simplest, generous quota)
  Unsplash -> https://unsplash.com/developers (50 req/hour on demo)

Usage:
  python fetch_images.py --dry-run                       # show per-dish queries, no network
  python fetch_images.py --source pexels   --key YOUR_KEY --limit 10   # test
  python fetch_images.py --source pexels   --key YOUR_KEY              # full run
  python fetch_images.py --source unsplash --key YOUR_KEY
  (or set env PEXELS_API_KEY / UNSPLASH_ACCESS_KEY instead of --key)
"""

import os
import sys
import json
import time
import argparse
import urllib.parse
import urllib.request
import urllib.error

MENU_FILE = "khmer_menu.json"
OUT_DIR = os.path.join("images", "dishes")

# Per-dish curated queries for well-known dishes where the obvious phrasing
# isn't what stock sites tag the photo as.
QUERY_OVERRIDES = {
    "fish-amok":                          "fish amok cambodian banana leaf",
    "beef-loc-lac":                       "lok lak cambodian beef",
    "prahok-ktis-pork-coconut-dip":       "prahok ktis cambodian",
    "phnom-penh-noodle-soup":             "kuy teav cambodian noodle soup",
    "sour-lemongrass-beef-soup":          "samlor machu cambodian sour soup",
}

# Relevance gate: a returned photo is only accepted if its alt-text or page
# URL contains at least one of these terms. The intent: avoid showing
# unrelated stock photos that confuse users. Better to placeholder than mislead.
KHMER_TERMS = [
    # geographic / cuisine markers — primary signal
    "cambodia", "cambodian", "khmer", "phnom penh", "siem reap", "kampot",
    # iconic Khmer dish names — accept if mentioned (very specific)
    "amok", "lok lak", "lok-lak", "loc lac", "loklak",
    "kuy teav", "kuyteav", "kuyteav",
    "num banh chok", "num banh", "nom banh chok",
    "prahok", "samlor", "kreung", "kralan", "sankhya",
    "bai sach", "num pang", "bobor", "babor", "saraman",
]


def build_per_dish(recipes):
    """Return {slug: {'query':..., 'name':...}} — one entry per unique dish."""
    out = {}
    for r in recipes:
        slug = r["slug"]
        if slug in out:
            continue
        q = QUERY_OVERRIDES.get(slug) or (r["name"]["en"] + " Cambodian Khmer food")
        out[slug] = {"query": q, "name": r["name"]["en"]}
    return out


def is_relevant(hit):
    """Decide whether a search hit is actually a Cambodian/Khmer dish photo."""
    text = ((hit.get("alt") or "") + " " + (hit.get("page_url") or "")).lower()
    return any(term in text for term in KHMER_TERMS)


# Use a real browser-like UA. Pexels/Unsplash sit behind Cloudflare, which
# blocks the default "Python-urllib/X.Y" fingerprint with a 403.
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")

def http_json(url, headers):
    h = dict(headers)
    h.setdefault("User-Agent", USER_AGENT)
    h.setdefault("Accept", "application/json")
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # Surface the actual API error body so 403/401 reasons are visible.
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:400]
        except Exception:
            pass
        raise RuntimeError("HTTP {} {} — {}".format(e.code, e.reason, body or "(no body)"))


def search_pexels(query, key):
    # Pull the top 3 candidates so the relevance gate has something to choose from.
    url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
        {"query": query, "per_page": 3, "orientation": "landscape"})
    data = http_json(url, {"Authorization": key})
    photos = data.get("photos") or []
    out = []
    for p in photos:
        out.append({
            "img": p["src"].get("large") or p["src"].get("medium"),
            "alt": p.get("alt", ""),
            "page_url": p.get("url", ""),
            "photographer": p.get("photographer", "Unknown"),
            "photographer_url": p.get("photographer_url", ""),
            "source": "Pexels",
            "source_url": p.get("url", ""),
        })
    return out


def search_unsplash(query, key):
    url = "https://api.unsplash.com/search/photos?" + urllib.parse.urlencode(
        {"query": query, "per_page": 3, "orientation": "landscape"})
    data = http_json(url, {"Authorization": "Client-ID " + key, "Accept-Version": "v1"})
    out = []
    for p in (data.get("results") or []):
        page = p["links"].get("html", "") + "?utm_source=khmer_chief&utm_medium=referral"
        out.append({
            "img": p["urls"].get("regular"),
            "alt": p.get("alt_description") or p.get("description") or "",
            "page_url": p["links"].get("html", ""),
            "photographer": p["user"].get("name", "Unknown"),
            "photographer_url": p["user"]["links"].get("html", "") + "?utm_source=khmer_chief&utm_medium=referral",
            "source": "Unsplash",
            "source_url": page,
        })
    return out


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp, open(path, "wb") as f:
        f.write(resp.read())


def write_credits(attribution):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "attribution.json"), "w", encoding="utf-8") as f:
        json.dump(attribution, f, ensure_ascii=False, indent=2)
    rows = []
    for fam, a in sorted(attribution.items()):
        rows.append(
            '<li><code>{fam}</code> — Photo by <a href="{pu}" target="_blank" rel="noopener">{p}</a> '
            'on <a href="{su}" target="_blank" rel="noopener">{s}</a></li>'.format(
                fam=fam, p=a["photographer"], pu=a["photographer_url"],
                s=a["source"], su=a["source_url"]))
    html = (
        "<!doctype html><meta charset='utf-8'><title>Image Credits</title>"
        "<style>body{font-family:system-ui,sans-serif;max-width:760px;margin:40px auto;padding:0 16px;line-height:1.6}"
        "li{margin:4px 0;font-size:14px}code{background:#f3eee5;padding:1px 5px;border-radius:4px}</style>"
        "<h1>Image Credits</h1><p>Dish photos courtesy of their photographers via Pexels / Unsplash.</p>"
        "<ul>" + "".join(rows) + "</ul>")
    with open("credits.html", "w", encoding="utf-8") as f:
        f.write(html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["pexels", "unsplash"], default="pexels")
    ap.add_argument("--key", default=None, help="API key (or set PEXELS_API_KEY / UNSPLASH_ACCESS_KEY)")
    ap.add_argument("--dry-run", action="store_true", help="list per-dish queries, no network calls")
    ap.add_argument("--limit", type=int, default=0, help="max dishes to fetch this run (0 = all)")
    ap.add_argument("--delay", type=float, default=1.5, help="seconds between requests (rate limiting)")
    args = ap.parse_args()

    doc = json.load(open(MENU_FILE, encoding="utf-8"))
    dishes = build_per_dish(doc["recipes"])
    print("Dishes: {} (one image attempt per dish)".format(len(dishes)))

    if args.dry_run:
        for slug in sorted(dishes):
            info = dishes[slug]
            print("  {:48s} query: {}".format(slug, info["query"]))
        print("\nDry run only — no images fetched. Re-run with --source/--key to download.")
        return

    key = args.key or os.environ.get(
        "PEXELS_API_KEY" if args.source == "pexels" else "UNSPLASH_ACCESS_KEY")
    if not key:
        print("ERROR: no API key. Pass --key or set the env var. See header for free signup links.")
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)
    search = search_pexels if args.source == "pexels" else search_unsplash
    attribution = {}
    attr_path = os.path.join(OUT_DIR, "attribution.json")
    if os.path.exists(attr_path):
        attribution = json.load(open(attr_path, encoding="utf-8"))

    fetched = skipped = missed = rejected = errored = 0
    for slug in sorted(dishes):
        path = os.path.join(OUT_DIR, slug + ".jpg")
        if os.path.exists(path):
            skipped += 1
            continue
        if args.limit and fetched >= args.limit:
            break
        query = dishes[slug]["query"]
        try:
            hits = search(query, key) or []
            if not hits:
                print("  no match  : {:48s} ({})".format(slug, query))
                missed += 1
            else:
                # Take the first hit that is Khmer/Cambodian-tagged.
                # Better an honest placeholder than a misleading photo.
                relevant = next((h for h in hits if h.get("img") and is_relevant(h)), None)
                if not relevant:
                    top = hits[0]
                    print("  not Khmer : {:48s} (top alt: {})".format(
                        slug, (top.get("alt") or "")[:60]))
                    rejected += 1
                else:
                    download(relevant["img"], path)
                    attribution[slug] = {k: relevant[k] for k in
                                         ("photographer", "photographer_url", "source", "source_url")}
                    print("  saved     : {:48s} <- {} ({})".format(
                        slug, relevant["source"], (relevant.get("alt") or "")[:40]))
                    fetched += 1
        except Exception as e:
            print("  ERROR     : {:48s} {}".format(slug, str(e)[:240]))
            errored += 1
            if errored >= 3 and fetched == 0:
                print("\nAborting: 3 consecutive failures with no successes. "
                      "The error message above is from the API itself — "
                      "check your key, account status, and quota.")
                break
        time.sleep(args.delay)

    write_credits(attribution)
    print("\nDone. fetched={} skipped={} no-match={} rejected={} errors={}".format(
        fetched, skipped, missed, rejected, errored))
    print("'rejected' = photo found but not Khmer/Cambodian-tagged — kept the placeholder instead.")
    print("Images in {}/ ; credits in credits.html".format(OUT_DIR))


if __name__ == "__main__":
    main()
