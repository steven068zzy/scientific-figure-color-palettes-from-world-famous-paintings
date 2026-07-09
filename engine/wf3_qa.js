export const meta = {
  name: 'qa-posters',
  description: 'Visual QA of rendered palette posters',
  phases: [{ title: 'QA', detail: 'one agent per 6 posters' }],
}
const SLUGS = ["mona_lisa", "last_supper", "birth_of_venus", "primavera", "creation_of_adam", "school_of_athens", "sistine_madonna", "venus_of_urbino", "bacchus_and_ariadne", "arnolfini_portrait", "garden_of_earthly_delights", "hunters_in_the_snow", "tower_of_babel", "the_ambassadors", "young_hare", "vertumnus", "view_of_toledo", "las_meninas", "calling_of_saint_matthew", "night_watch", "girl_with_a_pearl_earring", "the_milkmaid", "the_blue_boy", "the_swing", "napoleon_crossing_the_alps", "oath_of_the_horatii", "grande_odalisque", "liberty_leading_the_people", "raft_of_the_medusa", "third_of_may_1808", "the_parasol", "wanderer_above_the_sea_of_fog", "fighting_temeraire", "rain_steam_and_speed", "the_hay_wain", "the_gleaners", "ophelia", "lady_of_shalott", "flaming_june", "the_kiss_hayez", "whistlers_mother", "carnation_lily_lily_rose", "the_ninth_wave", "barge_haulers_on_the_volga", "morning_in_a_pine_forest", "breezing_up", "american_gothic", "impression_sunrise", "woman_with_a_parasol", "water_lilies", "japanese_footbridge", "luncheon_of_the_boating_party", "bal_du_moulin_de_la_galette", "two_sisters_on_the_terrace", "the_ballet_class", "paris_street_rainy_day", "boulevard_montmartre_at_night", "the_childs_bath", "a_sunday_on_la_grande_jatte", "bathers_at_asnieres", "starry_night", "sunflowers", "cafe_terrace_at_night", "irises", "the_bedroom", "tahitian_women_on_the_beach", "the_card_players", "mont_sainte_victoire", "the_basket_of_apples", "at_the_moulin_rouge", "the_sleeping_gypsy", "the_scream", "the_kiss_klimt", "adele_bloch_bauer", "four_trees", "jeanne_hebuterne", "senecio", "composition_viii", "composition_red_blue_yellow", "dance", "goldfish", "large_blue_horses", "great_wave", "red_fuji", "kirifuri_waterfall", "plum_park_in_kameido", "sudden_shower_over_shin_ohashi", "naruto_whirlpools", "evening_snow_at_kanbara", "three_beauties", "beauty_looking_back", "jakuchu_rooster", "thousand_li_of_rivers_and_mountains", "along_the_river_qingming", "dwelling_in_the_fuchun_mountains", "nymph_of_the_luo_river"]
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
