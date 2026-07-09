# masterpiece-palettes — Design

*2026-07-08 · design settled interactively with the owner; this document records it.*

## Goal

An open-source collection that turns 100 public-domain masterpiece paintings into
publication-ready scientific color palettes. Each painting gets:

1. a **poster** (PNG/JPG): the original artwork, an 8-color refined palette with names +
   hex codes, nine demo charts (heatmap, scatter, violin, spectra, dual-axis, polar,
   3D surface, time series, grouped bar) all drawn with that palette, and a role-based
   usage guide;
2. a **palette record** (JSON): named colors in data-plotting order, role assignments,
   and diverging colormap stops;
3. a **Python API** (`pip install masterpalettes`): `colors() / roles() / cmap() /
   apply() / register_matplotlib()`.

## Decisions

| Decision | Choice |
|---|---|
| Painting mix | ~80 Western + 10 Chinese classical + 10 Japanese ukiyo-e |
| Copyright | Artist dead ≥ 70 years AND work published before 1931 (US 95-year rule); 1930 works (American Gothic, Mondrian Composition II) entered US PD on 2026-01-01 |
| Image source | Wikipedia/Wikimedia Commons lead images (faithful reproductions of PD paintings are PD, Bridgeman v. Corel); modest resolution acceptable |
| Language | All English (posters + README) |
| Distribution | GitHub public repo + pip-installable package |

## Pipeline (reproducible)

```
data/paintings.json  ──►  engine/fetch_images.py   (Wikipedia API → paintings/*.jpg)
                     ──►  engine/extract.py        (K-means in CIELab + adaptive refine
                                                    → data/palettes_draft.json + strips/)
        [agent pass: verify metadata, fix images, name colors, write blurbs]
                     ──►  data/palettes.json       (final: names + blurbs merged)
                     ──►  engine/build_all.py      (posters/*.jpg + thumbs/*.jpg)
        [agent pass: visual QA of every poster]
```

### Palette extraction rules

- K-means (k=14) in CIELab on a 300px thumbnail; near-duplicate clusters merged (ΔE<10).
- 8 swatches selected: lightest (background), darkest (text), top warm chromatic pair,
  top cool chromatic pair, then diversity-greedy fill. Small-but-vivid clusters
  (e.g. Van Gogh's moon gold) are favored by weighting chroma^1.4.
- **Adaptive refinement**: vivid mode boosts chroma ×1.28 and clamps lightness into
  data-friendly ranges; **muted mode** (ink/silk works, detected by low global chroma)
  preserves the restrained ink aesthetic and only spreads lightness.
- Missing warm/cool partners are synthesized (light/dark sibling of the same hue) so
  every vivid palette has an amber/gold-style pair structure.
- Colors are seated one-by-one with guaranteed ΔE ≥ ~10 spacing among the first six
  (the categorical data slots consumed by charts).
- Accent = warmest chromatic color pushed toward red-orange; diverging = cool dark →
  paper light → warm accent.

### Role logic (what makes palettes feel "designed")

Warm, high-chroma colors carry primary signals and emphasis; cool tones carry
secondary structure; near-neutrals support; the accent appears sparingly; very light
tones are backgrounds; dark neutrals are text/axes. The logic is fixed across the
collection — only the painting changes.

## Repository layout

```
masterpalettes/          pip package (palettes.json bundled)
engine/                  pipeline scripts (fetch, extract, poster, build_all)
data/                    paintings.json, palettes.json, reports
paintings/  posters/  thumbs/  strips/
docs/                    this file
```
