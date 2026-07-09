"""Merge Workflow-2 naming results with palette drafts -> data/palettes.json (final).

Usage: python merge_names.py naming_results.json
Propagates any hex fine-tuning into roles and diverging stops; validates everything.
"""
import json, re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

def main(results_path):
    results = json.load(open(results_path))
    if isinstance(results, dict):
        results = results["results"]
    paintings = {p["slug"]: p for p in json.load(open(f"{ROOT}/data/paintings.json"))}
    drafts = json.load(open(f"{ROOT}/data/palettes_draft.json"))
    final, problems = {}, []
    for r in results:
        slug = r["slug"]
        d, p = drafts.get(slug), paintings.get(slug)
        if not d or not p:
            problems.append((slug, "unknown slug")); continue
        cols = r.get("colors", [])
        if len(cols) != 8 or any(not HEX.match(c["hex"]) for c in cols):
            problems.append((slug, "bad colors")); continue
        names = [c["name"].strip()[:16] for c in cols]
        if len(set(n.lower() for n in names)) < 8:
            problems.append((slug, f"duplicate names {names}")); continue
        blurb = " ".join(r.get("blurb", "").split())
        if not (100 <= len(blurb) <= 320):
            problems.append((slug, f"blurb length {len(blurb)}")); continue
        old = [c["hex"].upper() for c in d["colors"]]
        new = [c["hex"].upper() for c in cols]
        mapping = dict(zip(old, new))
        accent = r.get("accent_hex", "").upper()
        if not HEX.match(accent):
            accent = d["roles"]["Highlight / Accent"][0].upper()
        roles = {role: [(accent if role == "Highlight / Accent" else mapping.get(h.upper(), h.upper()))
                        for h in hs] if role != "Highlight / Accent" else [accent]
                 for role, hs in d["roles"].items()}
        diverging = [mapping.get(h.upper(), h.upper()) for h in d["diverging"]]
        diverging[2] = accent  # warm end tracks the tuned accent
        final[slug] = {
            "title": p["title"], "artist": p["artist"], "year": p["year"],
            "group": p["group"], "museum": p["museum"], "mode": d["mode"],
            "colors": [[n, h] for n, h in zip(names, new)],
            "roles": roles, "diverging": diverging, "blurb": blurb,
        }
        if r.get("palette_poor"):
            problems.append((slug, "palette_poor: " + r.get("notes", "")))
    # keep collection order
    ordered = {p: final[p] for p in paintings if p in final}
    json.dump(ordered, open(f"{ROOT}/data/palettes.json", "w"), indent=1, ensure_ascii=False)
    json.dump(ordered, open(f"{ROOT}/masterpalettes/data/palettes.json", "w"), indent=1, ensure_ascii=False)
    print(f"final palettes: {len(ordered)}")
    for s, why in problems:
        print("PROBLEM:", s, "-", why)

if __name__ == "__main__":
    main(sys.argv[1])
