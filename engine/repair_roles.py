"""Repair role assignments in data/palettes.json:
- Secondary Data must not duplicate Primary Data and must have 2 entries,
  picked from the coolest remaining palette colors.
Rewrites both palettes.json copies.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from extract import rgb_to_lab, lch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def hex_lch(h):
    rgb = np.array([int(h[i:i+2], 16) for i in (1, 3, 5)]) / 255.0
    return lch(rgb_to_lab(rgb))

def coolness(h):
    L, C, H = hex_lch(h)
    d = min(abs(H - 230) % 360, 360 - abs(H - 230) % 360)   # hue distance to blue
    return d - C * 0.15                                     # prefer blue-ish, chromatic

def main():
    pal = json.load(open(f"{ROOT}/data/palettes.json"))
    fixed = 0
    for slug, v in pal.items():
        roles = v["roles"]
        prim = [h.upper() for h in roles["Primary Data (Warm)"]]
        seco = [h.upper() for h in roles["Secondary Data (Cool)"]]
        used_elsewhere = set(prim) | {h.upper() for h in roles["Backgrounds"]} \
                         | {h.upper() for h in roles["Text / Lines"]}
        bad = any(s in prim for s in seco) or len(set(seco)) < 2
        if not bad:
            continue
        cand = [h.upper() for _, h in v["colors"] if h.upper() not in used_elsewhere]
        keep = [s for s in dict.fromkeys(seco) if s not in prim and s in [h.upper() for _, h in v["colors"]]]
        pool = [c for c in sorted(cand, key=coolness) if c not in keep]
        new = (keep + pool)[:2]
        if len(new) == 2 and set(new) != set(seco):
            roles["Secondary Data (Cool)"] = new
            fixed += 1
            print(f"{slug:40s} seco {seco} -> {new}")
    json.dump(pal, open(f"{ROOT}/data/palettes.json", "w"), indent=1, ensure_ascii=False)
    json.dump(pal, open(f"{ROOT}/masterpalettes/data/palettes.json", "w"), indent=1, ensure_ascii=False)
    print("repaired:", fixed)

if __name__ == "__main__":
    main()
