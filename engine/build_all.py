"""Batch driver: paintings.json + palettes.json -> posters/, thumbs/.

Usage: python build_all.py [--only slug1,slug2] [--procs 6]
"""
import json, os, sys
from multiprocessing import Pool
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def build_one(task):
    idx, meta, pal = task
    import poster
    slug = meta["slug"]
    P = {
        "artwork_path": f"{ROOT}/paintings/{slug}.jpg",
        "collection": f"COLOR INSPIRATION FROM ART · No. {idx:03d}",
        "title": meta["title"],
        "subtitle": "Scientific Color Inspiration",
        "blurb": pal["blurb"],
        "artist": meta["artist"], "year": meta["year"],
        "medium": meta["medium"], "source": meta["museum"] + " · Public Domain",
        "caption": (meta["title"] if len(meta["title"]) <= 36
                    else meta["title"][:35].rsplit(" ", 1)[0] + "…")
                   + f" ({meta['year']})" + ("" if "original" in meta["year"] else " · original"),
        "colors": [tuple(c) for c in pal["colors"]],
        "roles": pal["roles"],
        "diverging": pal["diverging"],
        "footer_right": f"Scientific Figure Color Palettes from World-Famous Paintings · {slug}",
    }
    out = f"{ROOT}/posters/{slug}.png"
    try:
        poster.make_poster(P, out)
        img = Image.open(out)
        img.convert("RGB").save(out.replace(".png", ".jpg"), "JPEG", quality=88)
        os.remove(out)
        img.thumbnail((480, 480 * img.height // img.width))
        img.convert("RGB").save(f"{ROOT}/thumbs/{slug}.jpg", "JPEG", quality=85)
        return slug, "ok"
    except Exception as e:
        return slug, f"FAIL {type(e).__name__}: {e}"

def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    paintings = json.load(open(f"{ROOT}/data/paintings.json"))
    palettes = json.load(open(f"{ROOT}/data/palettes.json"))
    only = set(sys.argv[sys.argv.index("--only")+1].split(",")) if "--only" in sys.argv else None
    procs = int(sys.argv[sys.argv.index("--procs")+1]) if "--procs" in sys.argv else 6
    tasks = []
    for i, p in enumerate(paintings, 1):
        if only and p["slug"] not in only:
            continue
        if p["slug"] not in palettes:
            print("skip (no palette):", p["slug"]); continue
        tasks.append((i, p, palettes[p["slug"]]))
    with Pool(procs) as pool:
        for slug, status in pool.imap_unordered(build_one, tasks):
            print(f"{slug:45s} {status}")

if __name__ == "__main__":
    main()
