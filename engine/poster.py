"""Poster renderer — adapted from the original single-painting palette_engine.py.

make_poster(P, out) renders one poster; P carries all painting-specific content.
Chart data is seeded identically for every poster so the collection stays uniform.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.gridspec as gridspec
from PIL import Image
import textwrap

F = dict(ptitle=12, tick=8.5, axlab=10.5, legend=7.5,
         sw_name=10.5, sw_hex=9, sec_head=14.5,
         collection=11, title=27, subtitle=17.5, blurb=10, meta=11.5,
         role=10.5, desc=8.5, footer=9.5)

def cmap_from(c, n="c"): return LinearSegmentedColormap.from_list(n, c)
def _ct(ax, t, pad=5): ax.set_title(t, fontsize=F["ptitle"], fontweight="bold", loc="left", pad=pad)

# ---------------- science panels A-I ----------------
def panel_heatmap(ax, P):
    div = cmap_from(P["diverging"], "d")
    base = np.zeros((9, 200))
    for a, b in [(0, 3), (3, 6), (6, 9)]:
        sig = np.random.randn(200)
        for i in range(a, b): base[i] = sig + .6 * np.random.randn(200)
    im = ax.imshow(np.corrcoef(base), cmap=div, vmin=-1, vmax=1)
    L = [f"V{i+1}" for i in range(9)]
    ax.set_xticks(range(9)); ax.set_yticks(range(9))
    ax.set_xticklabels(L, fontsize=F["tick"]); ax.set_yticklabels(L, fontsize=F["tick"])
    cb = plt.colorbar(im, ax=ax, fraction=.046, pad=.03); cb.ax.tick_params(labelsize=F["tick"])
    _ct(ax, "A · Heatmap / Correlation")

def panel_scatter(ax, P):
    cats = [c for _, c in P["colors"]][:5]
    for (cx, cy), col in zip([(-2, 2), (2, 2), (0, -.3), (-2, -2), (2, -2)], cats):
        ax.scatter(np.random.randn(70)*.55+cx, np.random.randn(70)*.55+cy,
                   s=16, color=col, alpha=.75, edgecolors="white", linewidths=.3)
    ax.set_xlabel("Component 1", fontsize=F["axlab"]); ax.set_ylabel("Component 2", fontsize=F["axlab"])
    ax.tick_params(labelsize=F["tick"]); _ct(ax, "B · Clustered Scatter")

def panel_violin(ax, P):
    cats = [c for _, c in P["colors"]][:6]
    data = [np.random.randn(200)*(.4+.1*i)+.1*np.sin(i) for i in range(6)]
    parts = ax.violinplot(data, showmedians=True)
    for pc, col in zip(parts["bodies"], cats):
        pc.set_facecolor(col); pc.set_edgecolor("black"); pc.set_alpha(.8); pc.set_linewidth(.6)
    for k in ("cbars", "cmins", "cmaxes", "cmedians"):
        parts[k].set_color("black"); parts[k].set_linewidth(.9)
    ax.set_xticks(range(1, 7)); ax.set_xticklabels([f"G{i}" for i in range(1, 7)], fontsize=F["tick"])
    ax.set_ylabel("Value", fontsize=F["axlab"]); ax.tick_params(labelsize=F["tick"]); _ct(ax, "C · Violin Plot")

def panel_spectral(ax, P):
    cats = [c for _, c in P["colors"]]
    x = np.linspace(400, 800, 400); total = np.zeros_like(x)
    for i, (mu, sd, amp) in enumerate([(470, 12, 1.4), (540, 18, 1.), (600, 15, 1.6), (670, 20, .9)]):
        g = amp*np.exp(-((x-mu)**2)/(2*sd**2)); total += g
        ax.plot(x, g, "--", color=cats[i % len(cats)], lw=1.2, label=f"Peak {i+1}")
    ax.scatter(x[::10], (total+np.random.randn(len(x))*.03)[::10], s=8,
               color=P["roles"]["Text / Lines"][0], alpha=.6, label="Exp.")
    ax.plot(x, total, "-", color=P["roles"]["Text / Lines"][0], lw=1.5, label="Fit")
    ax.set_xlabel("Wavelength (nm)", fontsize=F["axlab"]); ax.set_ylabel("Intensity", fontsize=F["axlab"])
    ax.tick_params(labelsize=F["tick"]); ax.legend(fontsize=F["legend"], loc="upper right", framealpha=.6)
    _ct(ax, "D · Spectral & Peak Fit")

def panel_dualaxis(ax, P):
    cats = [c for _, c in P["colors"]][:5]; xs = np.arange(5); bottoms = np.zeros(5)
    for i in range(5):
        v = np.random.rand(5)*15+8
        ax.bar(xs, v, bottom=bottoms, color=cats[i], width=.62, edgecolor="white", linewidth=.5)
        bottoms += v
    ax.set_xticks(xs); ax.set_xticklabels([f"Q{i}" for i in range(1, 6)], fontsize=F["tick"])
    ax.set_ylabel("Amount", fontsize=F["axlab"]); ax.tick_params(labelsize=F["tick"])
    ax2 = ax.twinx(); hl = P["roles"]["Highlight / Accent"][0]
    ax2.plot(xs, [42, 58, 74, 88, 80], "-o", color=hl, lw=1.5, ms=4.5)
    ax2.set_ylabel("Rate (%)", fontsize=F["axlab"], color=hl); ax2.tick_params(labelsize=F["tick"], colors=hl)
    ax2.set_ylim(0, 100); _ct(ax, "E · Dual-Axis Chart")

def panel_polar(ax, P):
    cats = [c for _, c in P["colors"]]; N = 24
    th = np.linspace(0, 2*np.pi, N, endpoint=False)
    r = np.abs(np.sin(th*2))*1.2 + np.random.rand(N)*.6 + .3
    for i in range(N):
        ax.bar(th[i], r[i], width=2*np.pi/N*.9, color=cats[i % len(cats)],
               alpha=.85, edgecolor="white", linewidth=.3)
    ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
    ax.tick_params(labelsize=F["tick"]); ax.set_yticklabels([])
    ax.set_title("F · Polar / Rose Plot", fontsize=F["ptitle"], fontweight="bold", loc="left", pad=14)

def panel_surface(ax, P):
    div = cmap_from(P["diverging"], "d2")
    xx = np.linspace(-3, 3, 55); X, Y = np.meshgrid(xx, xx)
    Z = (np.sin(X)*np.cos(Y)*1.5 + np.exp(-((X-1)**2+(Y-1)**2)/2)*1.2
         - np.exp(-((X+1)**2+(Y+1)**2)/2)*1.)
    ax.plot_surface(X, Y, Z, cmap=div, linewidth=0, antialiased=True)
    ax.set_xlabel("x", fontsize=F["tick"], labelpad=-8); ax.set_ylabel("y", fontsize=F["tick"], labelpad=-8)
    ax.set_zlabel("h", fontsize=F["tick"], labelpad=-8)
    ax.tick_params(labelsize=F["tick"]-2, pad=-2); ax.view_init(elev=34, azim=-58)
    try: ax.set_box_aspect((1, 1, .65), zoom=1.35)
    except TypeError: ax.set_box_aspect((1, 1, .65))
    ax.set_title("G · 3D Surface Plot", fontsize=F["ptitle"], fontweight="bold", loc="left", pad=-2, y=1.0)

def panel_series(ax, P):
    cats = [c for _, c in P["colors"]][:5]; t = np.linspace(0, 10, 120)
    for i, col in enumerate(cats):
        y = (1+i*.5)*(1-np.exp(-t/(1.2+i*.6))) + np.random.randn(120)*.03
        ax.plot(t, y, color=col, lw=1.6)
    ax.set_xlabel("Time (s)", fontsize=F["axlab"]); ax.set_ylabel("Response", fontsize=F["axlab"])
    ax.tick_params(labelsize=F["tick"]); _ct(ax, "H · Kinetic Time Series")

def panel_bar(ax, P):
    cats = [c for _, c in P["colors"]][:5]
    means = np.random.rand(5)*5+3; err = np.random.rand(5)*.6+.2
    ax.bar(range(5), means, yerr=err, color=cats, edgecolor="white",
           linewidth=.5, capsize=4, error_kw={"lw": 1})
    ax.set_xticks(range(5)); ax.set_xticklabels(list("ABCDE"), fontsize=F["tick"])
    ax.set_ylabel("Mean ± SD", fontsize=F["axlab"]); ax.tick_params(labelsize=F["tick"]); _ct(ax, "I · Grouped Bar")

# ---------------- header ----------------
def _cover(img, aspect):
    w, h = img.size; cur = w / h
    if cur > aspect:
        nw = int(h * aspect); x = (w - nw) // 2; img = img.crop((x, 0, x + nw, h))
    else:
        # top-weighted crop for tall portraits so faces stay in frame
        nh = int(w / aspect); y = int((h - nh) * 0.18); img = img.crop((0, y, w, y + nh))
    return img

def _title_font(title):
    n = len(title)
    if n <= 22: return F["title"], [title]
    if n <= 26: return 22, [title]
    lines = textwrap.wrap(title, 24, max_lines=2, placeholder="…")
    return 19, lines

def draw_header(fig, cell, P):
    figW, figH = fig.get_size_inches()
    ax = fig.add_subplot(cell); ax.axis("off")
    pos = ax.get_position(); hw_in, hh_in = pos.width * figW, pos.height * figH

    inset_h = 0.90
    box_aspect_wh = 1.35
    inset_w = (inset_h * hh_in * box_aspect_wh) / hw_in
    tax = ax.inset_axes([0.0, 0.06, inset_w, inset_h])
    img = Image.open(P["artwork_path"]).convert("RGB")
    real_aspect = (inset_w * hw_in) / (inset_h * hh_in)
    tax.imshow(np.asarray(_cover(img, real_aspect)), aspect="auto")
    tax.set_xticks([]); tax.set_yticks([])
    for s in tax.spines.values(): s.set_edgecolor("#999"); s.set_linewidth(.8)
    tax.text(0.5, -0.10, P["caption"], transform=tax.transAxes, ha="center", fontsize=8, color="#666")

    xt = inset_w + 0.025
    ax.text(xt, 0.97, P["collection"], fontsize=F["collection"], color="#888", fontweight="bold", va="top")
    tf, tlines = _title_font(P["title"])
    ax.text(xt, 0.87, "\n".join(tlines) + " —", fontsize=tf, color="#1a1a1a",
            family="serif", fontweight="bold", va="top", linespacing=1.05)
    ax.text(xt, 0.46, P["subtitle"], fontsize=F["subtitle"], color="#333", family="serif", va="top")
    ax.text(xt, 0.24, "\n".join(textwrap.wrap(P["blurb"], 66)), fontsize=F["blurb"], color="#444", va="top")

    y = 0.97
    for k, v in [("ARTIST", P["artist"]), ("YEAR", P["year"]),
                 ("MEDIUM", P["medium"]), ("SOURCE", P["source"])]:
        vw = textwrap.wrap(str(v), 26, max_lines=3, placeholder="…")
        ax.text(0.75, y, k, fontsize=F["meta"], fontweight="bold", color="#222", va="top")
        ax.text(0.845, y, "\n".join(vw), fontsize=F["meta"] - (1.5 if len(vw) > 1 else 0),
                color="#444", va="top", linespacing=1.1)
        y -= (0.11, 0.155, 0.20)[len(vw) - 1]

def draw_swatches(fig, cell, P):
    ax = fig.add_subplot(cell); ax.axis("off")
    ax.text(0.0, 1.04, "CORE PALETTE — Extracted & Refined", fontsize=F["sec_head"], fontweight="bold", va="top")
    cols = P["colors"]; n = len(cols); w = 1.0/n
    for i, (name, hexc) in enumerate(cols):
        x0 = i*w
        ax.add_patch(FancyBboxPatch((x0, 0.34), w*0.90, 0.44,
                     boxstyle="round,pad=0.004,rounding_size=0.02",
                     facecolor=hexc, edgecolor="none", transform=ax.transAxes))
        ax.text(x0+w*0.45, 0.22, name, ha="center",
                fontsize=F["sw_name"] if len(name) <= 12 else F["sw_name"]-1.5, fontweight="bold")
        ax.text(x0+w*0.45, 0.10, hexc.upper(), ha="center", fontsize=F["sw_hex"], color="#555")

def draw_usage(fig, cell, P):
    ax = fig.add_subplot(cell); ax.axis("off")
    ax.text(0.0, 1.06, "PALETTE USAGE GUIDE — Scientific Application", fontsize=F["sec_head"], fontweight="bold", va="top")
    descs = {
        "Primary Data (Warm)": "Encode primary signals\n& key contrasts.",
        "Secondary Data (Cool)": "Supporting groups &\ncategories.",
        "Tertiary / Support": "Context, baselines,\nsubtle fills.",
        "Highlight / Accent": "Sparingly for callouts\n& thresholds.",
        "Backgrounds": "Very light tones for\npanels & grids.",
        "Text / Lines": "Dark neutrals for axes\n& annotations.",
    }
    roles = P["roles"]; n = len(roles); w = 1.0/n
    for i, (role, cols) in enumerate(roles.items()):
        x0 = i*w
        ax.text(x0+0.008, 0.84, role, fontsize=F["role"], fontweight="bold", va="top")
        for j, c in enumerate(cols):
            ax.add_patch(FancyBboxPatch((x0+0.008+j*0.055, 0.42), 0.049, 0.18,
                         boxstyle="round,pad=0.002,rounding_size=0.01",
                         facecolor=c, edgecolor="#ccc", linewidth=.5, transform=ax.transAxes))
        ax.text(x0+0.008, 0.30, descs.get(role, ""), fontsize=F["desc"], color="#555", va="top")
        if i < n-1: ax.axvline(x0+w-0.004, 0.02, 0.92, color="#e5e5e5", lw=.7)

# ---------------- assembly ----------------
def make_poster(P, out="poster.png"):
    np.random.seed(42)          # identical demo data across the whole collection
    fig = plt.figure(figsize=(14, 18), facecolor="white")
    outer = gridspec.GridSpec(4, 1, height_ratios=[1.15, 0.5, 3.5, 0.72],
                              hspace=0.13, left=0.04, right=0.97, top=0.99, bottom=0.012)
    draw_header(fig, outer[0], P)
    draw_swatches(fig, outer[1], P)
    g = gridspec.GridSpecFromSubplotSpec(3, 3, subplot_spec=outer[2], hspace=0.42, wspace=0.30)
    panel_heatmap(fig.add_subplot(g[0, 0]), P)
    panel_scatter(fig.add_subplot(g[0, 1]), P)
    panel_violin(fig.add_subplot(g[0, 2]), P)
    panel_spectral(fig.add_subplot(g[1, 0]), P)
    panel_dualaxis(fig.add_subplot(g[1, 1]), P)
    panel_polar(fig.add_subplot(g[1, 2], projection="polar"), P)
    panel_surface(fig.add_subplot(g[2, 0], projection="3d"), P)
    panel_series(fig.add_subplot(g[2, 1]), P)
    panel_bar(fig.add_subplot(g[2, 2]), P)
    draw_usage(fig, outer[3], P)
    fig.text(0.04, 0.003, "Art informs science.  Colors communicate discovery.",
             fontsize=F["footer"], style="italic", color="#999")
    fig.text(0.97, 0.003, P.get("footer_right", ""), fontsize=F["footer"], color="#bbb", ha="right")
    fig.savefig(out, dpi=150, facecolor="white")
    plt.close(fig)
    return out
