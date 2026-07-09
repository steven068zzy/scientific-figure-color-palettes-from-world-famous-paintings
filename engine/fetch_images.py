"""Resolve each painting's lead image via the Wikipedia API and download it.

Usage: python fetch_images.py [--only slug1,slug2]
Writes paintings/<slug>.jpg and data/image_report.json
"""
import json, os, sys, time, io
import requests
from PIL import Image
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "masterpiece-palettes/0.1 (https://github.com/; ziyuanzhao.steven@gmail.com) requests"}
TARGET_W = 1600           # request thumbnail at this width
MIN_W, MIN_H = 500, 350   # reject tiny images (portrait prints may be narrow)

def _get(url, **kw):
    """GET with backoff on 429/5xx (Wikimedia rate limits)."""
    for attempt in range(5):
        r = requests.get(url, **kw)
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(6 * (attempt + 1))
            continue
        r.raise_for_status()
        return r
    r.raise_for_status()

def resolve(wiki_title):
    """Return (image_url, resolved_page, original_size) via pageimages API."""
    r = _get(
        "https://en.wikipedia.org/w/api.php",
        params=dict(action="query", titles=unquote(wiki_title.replace("_", " ")),
                    prop="pageimages", piprop="thumbnail|original|name",
                    pithumbsize=TARGET_W, redirects=1, format="json"),
        headers=UA, timeout=30)
    pages = r.json().get("query", {}).get("pages", {})
    for pid, page in pages.items():
        if int(pid) < 0:
            return None, page.get("title", wiki_title), None
        thumb = page.get("thumbnail", {})
        orig = page.get("original", {})
        url = thumb.get("source") or orig.get("source")
        size = (orig.get("width"), orig.get("height"))
        return url, page.get("title", wiki_title), size
    return None, wiki_title, None

def download(url, dest):
    r = _get(url, headers=UA, timeout=60)
    img = Image.open(io.BytesIO(r.content)).convert("RGB")
    w, h = img.size
    ok_size = max(w, h) >= 500 and min(w, h) >= 250
    img.save(dest, "JPEG", quality=92)
    return w, h, ok_size

def main():
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    paintings = json.load(open(f"{ROOT}/data/paintings.json"))
    report = {}
    rpath = f"{ROOT}/data/image_report.json"
    if os.path.exists(rpath):
        report = json.load(open(rpath))
    for p in paintings:
        slug = p["slug"]
        if only and slug not in only:
            continue
        dest = f"{ROOT}/paintings/{slug}.jpg"
        if os.path.exists(dest) and report.get(slug, {}).get("status") == "ok" and not only:
            continue
        entry = {"wiki": p["wiki"]}
        try:
            url = p.get("image_url")  # manual override wins
            if not url:
                url, resolved, size = resolve(p["wiki"])
                entry["resolved_page"] = resolved
            if not url:
                entry["status"] = "no_image"
            else:
                entry["url"] = url
                w, h, ok = download(url, dest)
                entry.update(width=w, height=h, status="ok" if ok else "too_small")
        except Exception as e:
            entry["status"] = "error"
            entry["error"] = f"{type(e).__name__}: {e}"
        report[slug] = entry
        print(f"{slug:45s} {entry['status']:10s} {entry.get('width','-')}x{entry.get('height','-')}")
        time.sleep(1.2)
    json.dump(report, open(rpath, "w"), indent=1)
    bad = {k: v for k, v in report.items() if v["status"] != "ok"}
    print(f"\nOK: {len(report)-len(bad)}/{len(report)}  problems: {list(bad)}")

if __name__ == "__main__":
    main()
