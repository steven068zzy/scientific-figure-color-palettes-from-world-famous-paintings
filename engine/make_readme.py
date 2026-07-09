"""Generate README.md: intro + quickstart + auto-built gallery grouped by movement."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HEAD = '''# masterpiece-palettes

**Scientific figure color palettes extracted from 102 masterpiece paintings.**

Every palette is machine-extracted from a public-domain masterpiece (K-means in CIELab),
refined for publication use (chroma boost, lightness spacing, guaranteed ΔE separation
between categorical colors), and assigned scientific roles: warm primaries carry your
main signal, cool secondaries carry structure, an accent highlights thresholds, light
neutrals form backgrounds, dark neutrals draw text and axes.

Each painting ships with a poster showing the palette applied to nine common figure
types — heatmap, clustered scatter, violin, spectral fit, dual-axis, polar, 3D surface,
time series, grouped bar — so you can judge at a glance how it behaves on real charts.

![The Starry Night poster](posters/starry_night.jpg)

## Install

```bash
pip install "git+https://github.com/stevenZYzhao/masterpiece-palettes.git"
```

## Quick start

```python
import masterpalettes as mp
import matplotlib.pyplot as plt

mp.list_palettes()                    # 102 names
mp.colors("starry_night")            # 8 hex colors in data-plotting order
mp.roles("starry_night")             # role -> colors (primary/secondary/accent/...)

# Use as the default color cycle
mp.apply("great_wave")
plt.plot(x, y1); plt.plot(x, y2)     # lines take Hokusai's blues automatically

# Diverging colormap for heatmaps / surfaces
plt.imshow(corr, cmap=mp.cmap("starry_night"), vmin=-1, vmax=1)

# Or register everything and refer to cmaps by name
mp.register_matplotlib()
plt.imshow(corr, cmap="mp.the_scream")

# seaborn
import seaborn as sns
sns.set_palette(mp.colors("water_lilies", 6))
```

Every palette is also a plain JSON record in
[`masterpalettes/data/palettes.json`](masterpalettes/data/palettes.json) —
usable from R, Julia, MATLAB, or by copy-pasting hex codes.

## How palettes are made

1. **Extract** — K-means (k=14) over the painting in CIELab; merge near-duplicates.
2. **Refine** — adaptive: oil paintings get a chroma boost and lightness clamping;
   ink/silk works keep their restrained "muted mode" aesthetic. The first six colors
   are seated with guaranteed perceptual spacing (ΔE ≥ ~10).
3. **Assign roles** — fixed logic across the collection: warm high-chroma pair =
   primary data; cool pair = secondary; accent = warmest color pushed toward
   red-orange; lightest = backgrounds; darkest = text/lines. Diverging maps run
   cool-dark → paper-light → warm-accent.
4. **Review** — every palette and poster passed an AI review pass (color naming,
   metadata fact-check, visual QA) plus human curation.

Full pipeline in [`engine/`](engine/), design notes in [`docs/DESIGN.md`](docs/DESIGN.md).

## Gallery

*Click any thumbnail for the full poster with hex codes and usage guide.*
'''

TAIL = '''
## Related projects

[MetBrewer](https://github.com/BlakeRMills/MetBrewer) and
[MoMAColors](https://github.com/BlakeRMills/MoMAColors) offer R palettes inspired by
museum collections. masterpiece-palettes differs in scope (100 named paintings with
posters demonstrating each palette on nine chart types), in its role-based usage
system, and in shipping as both Python API and plain JSON.

## License & attribution

- **Code** (engine + package): MIT.
- **Palette data**: CC0 — use freely, attribution appreciated.
- **Paintings**: all works are in the public domain (artists deceased 70+ years;
  works published before 1931). Faithful photographic reproductions of public-domain
  paintings are themselves public domain (*Bridgeman v. Corel*). Images sourced from
  Wikimedia Commons; each poster credits artist, year, and holding museum.

*Art informs science. Colors communicate discovery.*
'''

def main():
    paintings = json.load(open(f"{ROOT}/data/paintings.json"))
    palettes = json.load(open(f"{ROOT}/data/palettes.json"))
    groups = {}
    for p in paintings:
        if p["slug"] in palettes and os.path.exists(f"{ROOT}/thumbs/{p['slug']}.jpg"):
            groups.setdefault(p["group"], []).append(p)
    order = ["Renaissance & Baroque", "Romanticism & Realism", "Impressionism",
             "Post-Impressionism", "Modern", "Japanese Ukiyo-e", "Chinese Classical"]
    out = [HEAD]
    total = 0
    for g in order:
        items = groups.get(g, [])
        if not items:
            continue
        total += len(items)
        out.append(f"\n### {g} ({len(items)})\n")
        out.append("<table>")
        for row in range(0, len(items), 4):
            out.append("<tr>")
            for p in items[row:row+4]:
                s = p["slug"]
                out.append(
                    f'<td align="center" width="25%"><a href="posters/{s}.jpg">'
                    f'<img src="thumbs/{s}.jpg" width="180"></a><br>'
                    f'<sub><b>{p["title"]}</b><br>{p["artist"]}, {p["year"]}</sub></td>')
            out.append("</tr>")
        out.append("</table>\n")
    out.append(TAIL)
    open(f"{ROOT}/README.md", "w").write("\n".join(out))
    print(f"README.md written — {total} paintings in gallery")

if __name__ == "__main__":
    main()
