"""Palette extraction: K-means in CIELab + adaptive refinement + role assignment.

Produces data/palettes_draft.json and strips/<slug>_strip.png for reviewer agents.
"""
import json, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- sRGB <-> CIELab (D65) ----------
_M = np.array([[0.4124564, 0.3575761, 0.1804375],
               [0.2126729, 0.7151522, 0.0721750],
               [0.0193339, 0.1191920, 0.9503041]])
_WN = np.array([0.95047, 1.0, 1.08883])

def rgb_to_lab(rgb):
    rgb = np.asarray(rgb, float)
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    xyz = lin @ _M.T / _WN
    f = np.where(xyz > (6/29)**3, np.cbrt(xyz), xyz / (3*(6/29)**2) + 4/29)
    L = 116*f[..., 1] - 16
    a = 500*(f[..., 0] - f[..., 1])
    b = 200*(f[..., 1] - f[..., 2])
    return np.stack([L, a, b], axis=-1)

def lab_to_rgb(lab):
    lab = np.asarray(lab, float)
    fy = (lab[..., 0] + 16) / 116
    fx = fy + lab[..., 1] / 500
    fz = fy - lab[..., 2] / 200
    f = np.stack([fx, fy, fz], axis=-1)
    xyz = np.where(f > 6/29, f**3, 3*(6/29)**2*(f - 4/29)) * _WN
    lin = xyz @ np.linalg.inv(_M).T
    rgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.clip(lin, 0, None) ** (1/2.4) - 0.055)
    return np.clip(rgb, 0, 1)

def lch(lab):
    L, a, b = lab
    return L, float(np.hypot(a, b)), float(np.degrees(np.arctan2(b, a)) % 360)

def from_lch(L, C, H):
    h = np.radians(H)
    return np.array([L, C*np.cos(h), C*np.sin(h)])

def hexc(lab):
    r, g, b = (lab_to_rgb(lab) * 255).round().astype(int)
    return f"#{r:02X}{g:02X}{b:02X}"

def de(l1, l2):  # ΔE76 — sufficient for spacing decisions
    return float(np.linalg.norm(np.asarray(l1) - np.asarray(l2)))

def is_warm(H):
    return H < 100 or H > 335

# ---------- extraction ----------
def dominant_colors(img_path, k=14, sample=60000):
    from sklearn.cluster import KMeans
    img = Image.open(img_path).convert("RGB")
    img.thumbnail((300, 300))
    px = np.asarray(img).reshape(-1, 3) / 255.0
    if len(px) > sample:
        px = px[np.random.default_rng(0).choice(len(px), sample, replace=False)]
    lab = rgb_to_lab(px)
    km = KMeans(n_clusters=k, n_init=4, random_state=0).fit(lab)
    w = np.bincount(km.labels_, minlength=k) / len(lab)
    cands = [{"lab": c, "w": float(wi)} for c, wi in zip(km.cluster_centers_, w)]
    # merge near-duplicates (ΔE < 10), weight-averaged
    merged = []
    for c in sorted(cands, key=lambda x: -x["w"]):
        for m in merged:
            if de(c["lab"], m["lab"]) < 10:
                t = m["w"] + c["w"]
                m["lab"] = (m["lab"]*m["w"] + c["lab"]*c["w"]) / t
                m["w"] = t
                break
        else:
            merged.append(dict(c))
    return merged

def select_eight(cands):
    """Pick 8: bg (lightest), txt (darkest), warm & cool chromatic pairs, diversity fill."""
    for c in cands:
        c["L"], c["C"], c["H"] = lch(c["lab"])
    pool = sorted(cands, key=lambda c: -c["w"])
    bg = max(pool, key=lambda c: c["L"] - 0.3*c["C"])
    txt = min(pool, key=lambda c: c["L"] + 0.2*c["C"])
    chosen = [bg, txt]
    def free(): return [c for c in pool if not any(c is s for s in chosen)]
    warm = sorted([c for c in free() if is_warm(c["H"]) and c["C"] > 15],
                  key=lambda c: -(c["C"]**1.4 * (0.2 + np.sqrt(c["w"]))))
    cool = sorted([c for c in free() if not is_warm(c["H"]) and c["C"] > 15],
                  key=lambda c: -(c["C"]**1.4 * (0.2 + np.sqrt(c["w"]))))
    chosen += warm[:2] + cool[:2]
    while len(chosen) < 8 and free():
        best = max(free(), key=lambda c: min(de(c["lab"], s["lab"]) for s in chosen) * (0.3 + np.sqrt(c["w"])))
        chosen.append(best)
    return chosen[:8], warm, cool

def refine_and_assign(chosen, warm, cool):
    Cs = [c["C"] for c in chosen]
    muted = float(np.mean(sorted(Cs)[-4:])) < 26        # top-4 chroma mean low -> ink/silk mode
    bg, txt = chosen[0], chosen[1]
    data = chosen[2:]

    def polish(c, lo_L, hi_L, min_C, max_C):
        L = float(np.clip(c["L"], lo_L, hi_L))
        C = float(np.clip(c["C"] * (1.0 if muted else 1.28), min_C, max_C))
        return {"lab": from_lch(L, C, c["H"]), "L": L, "C": C, "H": c["H"], "w": c["w"]}

    # backgrounds & text
    bgp = polish(bg, 88, 95, 2, 18 if muted else 26)
    txtp = polish(txt, 13, 24, 0, 30)
    datap = [polish(c, 30, 74, (6 if muted else 24), 88) for c in data]

    # enforce spacing among data colors: nudge L apart when a pair is too close
    for _ in range(3):
        for i in range(len(datap)):
            for j in range(i+1, len(datap)):
                if de(datap[i]["lab"], datap[j]["lab"]) < 17:
                    a, b = (i, j) if datap[i]["L"] <= datap[j]["L"] else (j, i)
                    datap[a] = polish({**datap[a], "L": datap[a]["L"]-7, "C": datap[a]["C"]}, 26, 74,
                                      datap[a]["C"], datap[a]["C"]+1)
                    datap[b] = polish({**datap[b], "L": datap[b]["L"]+7, "C": datap[b]["C"]}, 30, 80,
                                      datap[b]["C"], datap[b]["C"]+1)

    warm_d = sorted([c for c in datap if is_warm(c["H"]) and c["C"] > (10 if muted else 20)], key=lambda c: -c["C"])
    cool_d = sorted([c for c in datap if not is_warm(c["H"]) and c["C"] > (10 if muted else 20)], key=lambda c: -c["C"])

    def partner(c, dl, dh):
        """Synthesize a light/dark sibling of a hue (e.g. amber -> gold)."""
        L = float(np.clip(c["L"] + dl, 30, 78))
        C = float(np.clip(c["C"] * 0.95, 20 if not muted else 8, 86))
        H = (c["H"] + dh) % 360
        return {"lab": from_lch(L, C, H), "L": L, "C": C, "H": H, "w": c["w"]}

    if not muted:  # vivid palettes want warm & cool PAIRS like amber/gold + cobalt/cerulean
        if len(warm_d) == 1:
            w0 = warm_d[0]
            warm_d.append(partner(w0, 14 if w0["L"] < 56 else -14, 12 if w0["H"] < 60 else -12))
        if len(cool_d) == 1:
            c0 = cool_d[0]
            cool_d.append(partner(c0, 14 if c0["L"] < 56 else -14, -10))
    keep = warm_d[:2] + cool_d[:2]
    rest = [c for c in datap if not any(c is k for k in keep)]

    # ordered swatch list: warm pair, cool pair, dark, supports..., light bg last
    ordered = (warm_d[:2] + cool_d[:2] + [txtp] + rest)[:7] + [bgp]
    while len(ordered) < 8:                       # very reduced palettes: synthesize a tint
        basis = ordered[len(ordered) % max(len(ordered)-2, 1)]
        ordered.insert(-1, polish({**basis, "L": min(basis["L"]+18, 82)}, 30, 84, basis["C"]*0.6, 88))

    # final spacing: seat colors one by one, trying L offsets until clear of everyone seated
    seated = []
    for idx, c in enumerate(ordered):
        if idx >= 6:
            seated.append(c); continue
        best, best_min = c, -1
        for off in (0, 12, -12, 24, -24, 36):
            L = float(np.clip(c["L"] + off, 14, 90))
            cand = {"lab": from_lch(L, c["C"], c["H"]), "L": L, "C": c["C"], "H": c["H"], "w": c["w"]}
            m = min((de(cand["lab"], s["lab"]) for s in seated), default=99)
            if m >= 10:
                best = cand; break
            if m > best_min:
                best, best_min = cand, m
        seated.append(best)
    ordered = seated

    # accent: warmest chromatic pushed toward red-orange
    src = (warm_d or cool_d or datap)[0]
    H = src["H"] if is_warm(src["H"]) else 38
    acc_H = H + (38 - H) * 0.35
    accent = from_lch(min(58, max(46, src["L"])), min(88, src["C"] + (8 if muted else 18)), acc_H)

    prim = [hexc(c["lab"]) for c in (warm_d[:2] or datap[:2])]
    seco = [hexc(c["lab"]) for c in (cool_d[:2] or datap[2:4] or datap[:2])]
    tert = [hexc(polish(bgp, 78, 88, 4, 24)["lab"]), hexc(bgp["lab"])]
    bg2 = lab_to_rgb(bgp["lab"]) * 0.35 + 0.65     # blend toward white
    dark2 = rest[0] if rest else cool_d[2] if len(cool_d) > 2 else txtp
    roles = {
        "Primary Data (Warm)": prim,
        "Secondary Data (Cool)": seco,
        "Tertiary / Support": tert,
        "Highlight / Accent": [hexc(accent)],
        "Backgrounds": [hexc(bgp["lab"]), "#%02X%02X%02X" % tuple((bg2*255).round().astype(int))],
        "Text / Lines": [hexc(txtp["lab"]), hexc(from_lch(min(34, dark2["L"]), min(28, dark2["C"]), dark2["H"]))],
    }
    diverging = [hexc(from_lch(max(16, txtp["L"]), max(txtp["C"], 14), (cool_d[0]["H"] if cool_d else txtp["H"]))),
                 hexc(bgp["lab"]), hexc(accent)]
    min_de = min(de(a["lab"], b["lab"]) for i, a in enumerate(ordered[:6]) for b in ordered[i+1:6])
    return ordered, roles, diverging, ("muted" if muted else "vivid"), round(min_de, 1)

def make_strip(slug, img_path, ordered, roles, diverging, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    fig = plt.figure(figsize=(13, 4.6), facecolor="white")
    ax0 = fig.add_axes([0.02, 0.05, 0.30, 0.90]); ax0.axis("off")
    im = Image.open(img_path).convert("RGB"); im.thumbnail((560, 560))
    ax0.imshow(np.asarray(im)); ax0.set_title(slug, fontsize=10)
    ax1 = fig.add_axes([0.35, 0.52, 0.62, 0.40]); ax1.axis("off"); ax1.set_xlim(0, 8); ax1.set_ylim(0, 1)
    for i, c in enumerate(ordered):
        h = hexc(c["lab"])
        ax1.add_patch(plt.Rectangle((i+0.03, 0.25), 0.94, 0.72, color=h))
        ax1.text(i+0.5, 0.10, h, ha="center", fontsize=8.5)
        ax1.text(i+0.5, -0.12, f"L{c['L']:.0f} C{c['C']:.0f}", ha="center", fontsize=7, color="#888")
    ax2 = fig.add_axes([0.35, 0.28, 0.62, 0.13]); ax2.axis("off"); ax2.set_xlim(0, 10); ax2.set_ylim(0, 1)
    x = 0
    for role, cs in roles.items():
        ax2.text(x, 0.8, role.split(" (")[0], fontsize=6.5, color="#555")
        for c in cs:
            ax2.add_patch(plt.Rectangle((x, 0.05), 0.42, 0.6, color=c)); x += 0.48
        x += 0.42
    ax3 = fig.add_axes([0.35, 0.07, 0.62, 0.10])
    grad = np.linspace(0, 1, 256).reshape(1, -1)
    ax3.imshow(grad, cmap=LinearSegmentedColormap.from_list("d", diverging), aspect="auto")
    ax3.set_xticks([]); ax3.set_yticks([])
    fig.savefig(out, dpi=110, facecolor="white"); plt.close(fig)

def process(slug):
    img_path = f"{ROOT}/paintings/{slug}.jpg"
    cands = dominant_colors(img_path)
    chosen, warm, cool = select_eight(cands)
    ordered, roles, diverging, mode, min_de = refine_and_assign(chosen, warm, cool)
    make_strip(slug, img_path, ordered, roles, diverging, f"{ROOT}/strips/{slug}_strip.png")
    return {
        "colors": [{"hex": hexc(c["lab"]), "L": round(c["L"]), "C": round(c["C"]), "H": round(c["H"])} for c in ordered],
        "roles": roles, "diverging": diverging, "mode": mode, "min_delta_e_first6": min_de,
    }

if __name__ == "__main__":
    paintings = json.load(open(f"{ROOT}/data/paintings.json"))
    only = set(sys.argv[sys.argv.index("--only")+1].split(",")) if "--only" in sys.argv else None
    out_path = f"{ROOT}/data/palettes_draft.json"
    drafts = json.load(open(out_path)) if os.path.exists(out_path) else {}
    for p in paintings:
        slug = p["slug"]
        if only and slug not in only:
            continue
        if not os.path.exists(f"{ROOT}/paintings/{slug}.jpg"):
            print("skip (no image):", slug); continue
        try:
            drafts[slug] = process(slug)
            print(f"{slug:45s} {drafts[slug]['mode']:6s} minΔE={drafts[slug]['min_delta_e_first6']}")
        except Exception as e:
            print("FAIL", slug, type(e).__name__, e)
    json.dump(drafts, open(out_path, "w"), indent=1)
    print(f"\n{len(drafts)} palettes -> {out_path}")
