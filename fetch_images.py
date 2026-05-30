# -*- coding: utf-8 -*-
"""
Fetch one stock photo per dish-family for the Khmer menu (hybrid strategy).

- Collapses the 1000+ dishes to ~164 image families (protein variants share an image).
- Searches a free stock provider (Pexels or Unsplash) for each family and saves
  images/dishes/<family>.jpg. Dishes with no good match keep the page's emoji placeholder.
- Resumable: skips families that already have a file.
- Writes attribution.json and credits.html (required by both providers' terms).

Get a FREE API key (2 min):
  Pexels   -> https://www.pexels.com/api/   (200 req/hour, simplest)
  Unsplash -> https://unsplash.com/developers (50 req/hour on demo)

Usage:
  python fetch_images.py --dry-run                       # show what it would fetch, no network
  python fetch_images.py --source pexels   --key YOUR_KEY
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

# Better queries for the iconic / well-known families than the auto-derived ones.
QUERY_OVERRIDES = {
    "fish-amok": "fish amok cambodian curry banana leaf",
    "beef-loc-lac": "beef lok lak cambodian",
    "prahok-ktis-pork-coconut-dip": "cambodian pork coconut dip vegetables",
    "kuy-teav-phnom-penh": "cambodian rice noodle soup kuy teav",
    "samlor-machu-kreung-sach-ko": "cambodian sour beef soup",
    "rice-bai-cha": "khmer fried rice",
    "noodles-num-banh-chok": "num banh chok khmer noodles",
}

# Protein words to strip from a dish name to get a family-level search query.
PROTEIN_WORDS = [
    "Mixed Vegetables", "Chicken", "Pork", "Beef", "Duck", "Frog", "Fish",
    "Shrimp", "Squid", "Crab", "Clams", "Tofu", "Egg", "Mushroom", "Vegetables",
]


def derive_query(name_en):
    q = name_en
    for w in PROTEIN_WORDS:
        q = q.replace(w, "")
    # clean dangling connectors / punctuation left behind
    q = q.replace("()", " ").replace("with &", "").replace("with ", " ")
    q = q.replace(" & ", " ").replace("&", " ")
    q = " ".join(q.split()).strip(" -(),")
    if not q:
        q = name_en
    return q + " Cambodian Khmer food dish"


def build_families(recipes):
    """Return {family: {'query':..., 'example':..., 'count':int}} keyed by image family."""
    fams = {}
    for r in recipes:
        fam = r["imageFamily"]
        if fam not in fams:
            q = QUERY_OVERRIDES.get(fam) or derive_query(r["name"]["en"])
            fams[fam] = {"query": q, "example": r["name"]["en"], "count": 0}
        fams[fam]["count"] += 1
    return fams


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
    url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
        {"query": query, "per_page": 1, "orientation": "landscape"})
    data = http_json(url, {"Authorization": key})
    photos = data.get("photos") or []
    if not photos:
        return None
    p = photos[0]
    return {
        "img": p["src"].get("large") or p["src"].get("medium"),
        "photographer": p.get("photographer", "Unknown"),
        "photographer_url": p.get("photographer_url", ""),
        "source": "Pexels",
        "source_url": p.get("url", ""),
    }


def search_unsplash(query, key):
    url = "https://api.unsplash.com/search/photos?" + urllib.parse.urlencode(
        {"query": query, "per_page": 1, "orientation": "landscape"})
    data = http_json(url, {"Authorization": "Client-ID " + key, "Accept-Version": "v1"})
    results = data.get("results") or []
    if not results:
        return None
    p = results[0]
    return {
        "img": p["urls"].get("regular"),
        "photographer": p["user"].get("name", "Unknown"),
        "photographer_url": p["user"]["links"].get("html", "") + "?utm_source=khmer_chief&utm_medium=referral",
        "source": "Unsplash",
        "source_url": p["links"].get("html", "") + "?utm_source=khmer_chief&utm_medium=referral",
    }


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
    ap.add_argument("--dry-run", action="store_true", help="list families + queries, no network calls")
    ap.add_argument("--limit", type=int, default=0, help="max families to fetch this run (0 = all)")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between requests (rate limiting)")
    args = ap.parse_args()

    doc = json.load(open(MENU_FILE, encoding="utf-8"))
    families = build_families(doc["recipes"])
    print("Dishes: {} -> image families: {}".format(len(doc["recipes"]), len(families)))

    if args.dry_run:
        for fam in sorted(families):
            info = families[fam]
            print("  [{:>2} dishes] {:34s} query: {}".format(info["count"], fam, info["query"]))
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

    fetched = skipped = missed = errored = 0
    for fam in sorted(families):
        path = os.path.join(OUT_DIR, fam + ".jpg")
        if os.path.exists(path):
            skipped += 1
            continue
        if args.limit and fetched >= args.limit:
            break
        query = families[fam]["query"]
        try:
            hit = search(query, key)
            if not hit or not hit.get("img"):
                print("  no match: {:34s} ({})".format(fam, query))
                missed += 1
            else:
                download(hit["img"], path)
                attribution[fam] = {k: hit[k] for k in
                                    ("photographer", "photographer_url", "source", "source_url")}
                print("  saved   : {:34s} <- {}".format(fam, hit["source"]))
                fetched += 1
        except Exception as e:
            print("  ERROR   : {:34s} {}".format(fam, str(e)[:240]))
            errored += 1
            # If the very first request is failing, bail early — almost certainly
            # an auth/quota issue, no point hammering the API.
            if errored >= 3 and fetched == 0:
                print("\nAborting: 3 consecutive failures with no successes. "
                      "The error message above is from the API itself — "
                      "check your key, account status, and quota.")
                break
        time.sleep(args.delay)

    write_credits(attribution)
    print("\nDone. fetched={} skipped={} no-match={} errors={}".format(
        fetched, skipped, missed, errored))
    print("Images in {}/ ; credits in credits.html".format(OUT_DIR))


if __name__ == "__main__":
    main()
