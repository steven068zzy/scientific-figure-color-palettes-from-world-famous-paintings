export const meta = {
  name: 'name-palettes-fixup',
  description: 'Name colors, write blurbs, fine-tune hexes for each painting palette',
  phases: [{ title: 'Name', detail: 'one agent per 6 paintings, vision on palette strips' }],
}

const ITEMS = [{"slug": "night_revels_of_han_xizai", "title": "The Night Revels of Han Xizai", "artist": "Gu Hongzhong (Song copy)", "year": "Song copy of 10th c. original", "mode": "vivid", "colors": ["#C15227", "#8D5F22", "#26241D", "#574416", "#381E00", "#D2BF86", "#8D7E41", "#E9DCBB"], "accent": "#D53D13"}, {"slug": "five_oxen", "title": "Five Oxen", "artist": "Han Huang", "year": "8th century", "mode": "vivid", "colors": ["#CA943B", "#BD6339", "#422E1D", "#945D16", "#634B2A", "#5E3300", "#72563E", "#F7D8AC"], "accent": "#D37202"}, {"slug": "bunian_tu", "title": "Emperor Taizong Receiving the Tibetan Envoy", "artist": "Yan Liben", "year": "7th century (Song copy)", "mode": "vivid", "colors": ["#D72416", "#A40F0C", "#381C11", "#AE611F", "#882D0F", "#8C673B", "#642F14", "#FFD5AF"], "accent": "#DB1812"}, {"slug": "court_ladies_preparing_silk", "title": "Court Ladies Preparing Newly Woven Silk", "artist": "Zhang Xuan (Huizong copy)", "year": "12th century copy of 8th c. original", "mode": "vivid", "colors": ["#A36921", "#C49158", "#AEAB6C", "#92834C", "#282220", "#683D22", "#E4C18D", "#EEDBAF"], "accent": "#BC5A00"}, {"slug": "court_ladies_adorning_with_flowers", "title": "Court Ladies Adorning Their Hair with Flowers", "artist": "Zhou Fang", "year": "8th century", "mode": "vivid", "colors": ["#922E1E", "#623400", "#292315", "#936739", "#DEB181", "#5C4221", "#524834", "#F1DAAC"], "accent": "#C83825"}, {"slug": "one_hundred_horses", "title": "One Hundred Horses", "artist": "Giuseppe Castiglione (Lang Shining)", "year": "1728", "mode": "muted", "colors": ["#AC9873", "#5C5037", "#3F382D", "#DEC9A2", "#6A6256", "#888073", "#6A6256", "#ECDBBB"], "accent": "#AD835B"}]

const RESULT = {
  type: 'object',
  properties: {
    results: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          slug: { type: 'string' },
          colors: {
            type: 'array', minItems: 8, maxItems: 8,
            items: {
              type: 'object',
              properties: {
                name: { type: 'string', description: '1-2 evocative words tied to the painting, <=14 chars, Title Case' },
                hex: { type: 'string', pattern: '^#[0-9A-Fa-f]{6}$' },
              },
              required: ['name', 'hex'],
            },
          },
          accent_hex: { type: 'string', pattern: '^#[0-9A-Fa-f]{6}$' },
          blurb: { type: 'string', description: '2 sentences, 150-260 chars' },
          palette_poor: { type: 'boolean', description: 'true only if the palette badly misrepresents the painting' },
          notes: { type: 'string' },
        },
        required: ['slug', 'colors', 'accent_hex', 'blurb', 'palette_poor'],
      },
    },
  },
  required: ['results'],
}

const mkPrompt = (batch) => `You are the color curator for "masterpiece-palettes": scientific figure palettes extracted from famous paintings. Your taste defines the collection's soul.

Handle EVERY painting below (one result per slug, same order). For each:

1. LOOK: Read /Users/ziyuanzhao/masterpiece-palettes/strips/<slug>_strip.png — left is the painting, right is its extracted 8-color palette (order: warm pair, cool pair, dark, supports, light background last) plus role chips and the diverging gradient. Also Read /Users/ziyuanzhao/masterpiece-palettes/paintings/<slug>.jpg if you need a closer look at the artwork.

2. NAME all 8 colors in order: 1-2 evocative words rooted in THAT painting's imagery and story (like "Star Gold", "Cypress", "Moon Cream" for The Starry Night). <=14 characters, Title Case, no color-word repeats within one palette (one "Gold" max, etc.).

3. FINE-TUNE (optional but encouraged where it helps): you may adjust any hex to make the palette sing — typical fixes: brighten a muddy gold, enrich a weak blue, warm up a gray. Keep each color recognizably from the painting, keep neighbors distinguishable (the first 6 are categorical data colors), keep slot 8 very light (background) and slot 5 dark. Return the final hex for every color (unchanged ones verbatim). Also return accent_hex: the current accent is given; adjust if it clashes or is too dull — it should be a saturated warm callout color that pops against the palette.

4. BLURB: exactly 2 sentences, 150-260 chars, English. Sentence 1: evoke the painting's palette poetically but concretely. Sentence 2: state the scientific role logic. Model: "Swirling nocturnal blues and radiant golden light, refined into a publication-ready palette. Warm hues carry primary signals and emphasis; cool tones provide context and structure across multi-panel figures." Vary the phrasing — do not copy that example verbatim for every painting.

5. palette_poor: set true ONLY if the extracted palette fundamentally fails the painting (wrong dominant hues, all mud). Explain in notes.

Paintings for you:
${JSON.stringify(batch, null, 1)}

Return everything via StructuredOutput.`

phase('Name')
const batches = []
for (let i = 0; i < ITEMS.length; i += 6) batches.push(ITEMS.slice(i, i + 6))
log(`${ITEMS.length} palettes in ${batches.length} batches`)
const out = await parallel(batches.map((b, i) => () =>
  agent(mkPrompt(b), { label: `name:${b[0].slug}+${b.length - 1}`, phase: 'Name', schema: RESULT })
))
const dropped = out.filter(x => !x).length
if (dropped) log(`WARNING: ${dropped} naming agents returned nothing`)
const results = out.filter(Boolean).flatMap(r => r.results || [])
const poor = results.filter(r => r.palette_poor).map(r => r.slug)
log(`named=${results.length} palette_poor=${poor.length}`)
return { results, poor }
