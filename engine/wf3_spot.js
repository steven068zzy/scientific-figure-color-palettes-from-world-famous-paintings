export const meta = {
  name: 'qa-spotcheck',
  description: 'Visual QA of rendered palette posters',
  phases: [{ title: 'QA', detail: 'one agent per 6 posters' }],
}
const SLUGS = ["girl_with_a_pearl_earring", "the_blue_boy", "bunian_tu", "flaming_june", "jakuchu_rooster", "whistlers_mother"]
const RESULT = {
  type: 'object',
  properties: {
    results: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          slug: { type: 'string' },
          pass: { type: 'boolean' },
          issues: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                kind: { type: 'string', description: 'crop|text-overlap|text-cutoff|palette-mismatch|chart-legibility|name-problem|other' },
                detail: { type: 'string' },
                severity: { type: 'string', enum: ['minor', 'major'] },
              },
              required: ['kind', 'detail', 'severity'],
            },
          },
        },
        required: ['slug', 'pass', 'issues'],
      },
    },
  },
  required: ['results'],
}
const mkPrompt = (batch) => `You are the final visual QA reviewer for "masterpiece-palettes" posters (repo /Users/ziyuanzhao/masterpiece-palettes). These posters will be published on GitHub, so judge like a picky design reviewer.

For EACH slug below, Read /Users/ziyuanzhao/masterpiece-palettes/posters/<slug>.jpg and inspect carefully:
1. HEADER: painting thumbnail shows the right artwork, crop is representative (center-crop of very wide scrolls is expected and fine), no distortion; title/metadata/blurb text not overlapping, not cut off (watch the right-side SOURCE column and long titles).
2. PALETTE ROW: 8 swatches with names+hex all visible; names evocative, no duplicated names; no two adjacent swatches looking identical.
3. CHARTS: series distinguishable in scatter/violin/bars; heatmap diverging gradient smooth (dark to light to warm); nothing garishly clashing.
4. USAGE GUIDE row intact.
Report pass=false only for problems worth fixing before publication (majors: wrong painting, unreadable/overlapping text, twin swatches, illegible charts). Cosmetic nitpicks = minor issues on a passing poster.
Slugs: ${JSON.stringify(batch)}
Return via StructuredOutput.`
phase('QA')
const batches = []
for (let i = 0; i < SLUGS.length; i += 6) batches.push(SLUGS.slice(i, i + 6))
log(`${SLUGS.length} posters in ${batches.length} batches`)
const out = await parallel(batches.map((b) => () =>
  agent(mkPrompt(b), { label: `qa:${b[0]}+${b.length - 1}`, phase: 'QA', schema: RESULT })
))
const results = out.filter(Boolean).flatMap(r => r.results || [])
const fails = results.filter(r => !r.pass)
log(`qa=${results.length} fails=${fails.length}`)
return { results, failed: fails.map(f => f.slug) }
