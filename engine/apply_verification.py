"""Apply Workflow-1 verification results to data/paintings.json.

Usage: python apply_verification.py results.json
results.json = [{slug, corrections{}, pd_ok, pd_note, image_ok, image_url, image_note}, ...]
"""
import json, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main(results_path):
    results = json.load(open(results_path))
    if isinstance(results, dict):
        results = results["results"]
    paintings = json.load(open(f"{ROOT}/data/paintings.json"))
    by_slug = {p["slug"]: p for p in paintings}
    refetch = []
    for r in results:
        p = by_slug.get(r["slug"])
        if not p:
            print("?? unknown slug", r["slug"]); continue
        for k, v in (r.get("corrections") or {}).items():
            if k in ("title", "artist", "year", "medium", "museum") and v and v != p.get(k):
                print(f"{r['slug']:40s} {k}: {p.get(k)!r} -> {v!r}")
                p[k] = v
        if not r.get("pd_ok", True):
            p["pd_flag"] = r.get("pd_note", "flagged")
            print(f"{r['slug']:40s} PD CONCERN: {r.get('pd_note')}")
        if not r.get("image_ok", True):
            url = (r.get("image_url") or "").strip()
            if url.startswith("https://upload.wikimedia.org"):
                p["image_url"] = url
                refetch.append(r["slug"])
            else:
                print(f"{r['slug']:40s} image bad but NO usable url: {r.get('image_note')}")
    json.dump(paintings, open(f"{ROOT}/data/paintings.json", "w"), indent=1, ensure_ascii=False)
    print("\nrefetch needed:", ",".join(refetch) if refetch else "(none)")

if __name__ == "__main__":
    main(sys.argv[1])
