# Final visual review

## Scope and evidence

This is a read-only visual review of the final UI captures. I reviewed the
aggregate states in `reports/aggregate/` at 1440, 768, and 375 widths, the
post-submit captures found under `reports/aggregate/workflow/`, and the
sampled-point captures in `reports/points/` for 3D, constellation, and selected
inspector states. The requested workflow files were present under the
`aggregate/workflow` subdirectory rather than a sibling `reports/workflow`
directory.

The aggregate captures are API-ready, aggregate-density mode; the sampled-point
captures provide the real 2D/3D/constellation and inspector evidence. I did not
read data, model bundles, notebooks, or artifacts, and I did not make product
changes.

Compared with the baseline, the strongest gains are visible and substantial:
the map now enters the 1440 first viewport beside the introduction, the phone
header has one readiness indicator and a 2x2 tab grid, the Explorer has an
explicit guide or selected-sample inspector, empty prediction distances are
collapsed, and Research presents findings/comparison before methodology and
archived evidence. The accepted charcoal/teal/violet + serif/sans/mono system
remains coherent.

This follow-up uses the refreshed captures from 23:15-23:17 on 2026-11-12.
The two previously High findings were rechecked after the mobile inspector,
table-scroll hint, reserved chart-toolbar strips, compact overview toolbar
behavior, and bordered disclosures were updated.

## Frontend-design rubric

Scores follow the existing 12-item rubric: 0 = not met, 1 = partially met,
2 = strong. The total is intentionally not a perfect score because narrow
tables and chart controls still create visible mobile friction.

| Item | Score / 2 | Evidence |
|---|---:|---|
| Brief fidelity | **2** | `aggregate/1440-overview-viewport.png` pairs the editorial introduction with the genuine density map; all views retain the restrained scientific-instrument tone and accepted palette. |
| Hierarchy | **2** | Overview leads with map and one primary Explore action; `aggregate/1440-research.png` leads with Research Findings; workflow captures put the assigned cluster before details. |
| Spacing | **2** | Card padding, gutters, tab rows, and stacked phone sections have a consistent rhythm. The tall form is expected for nine descriptors; the desktop prediction right column has some unavoidable empty height while the form is taller. |
| Alignment | **2** | Desktop grids align well, and refreshed `points/375-selected-inspector.png` uses one aligned key/value row per descriptor and stacked nearest-track entries. The comparison table remains bounded and initially shows only part of its wide schema, but the explicit horizontal-scroll hint makes that behavior understandable. |
| Typography | **2** | Serif display headings, sans explanatory text, and mono technical labels are legible and distinctive across widths. Long mobile headings wrap intentionally; only compressed table labels become difficult to scan. |
| Color discipline | **2** | Charcoal surfaces, teal Cluster 0, violet Cluster 1, and amber finding accents are consistent. Marker shape, labels, and status copy supplement color. |
| Depth and shape | **2** | Hairlines, surface tints, one radius system, and restrained elevation keep the interface editorial rather than glossy. The map remains the visual signature. |
| States and feedback | **2** | API-ready status, active tabs, selected map mode, selected sample, prediction-received state, and open/closed evidence sections are all visible in the captures. Disclosure affordances are weaker than the content states (see concerns). |
| Responsiveness | **2** | The 2x2 mobile tabs, stacked hero/map, stacked form, reserved chart-toolbar strips, and no page-level overflow are good. The comparison table is locally scrollable with an explicit hint; the selected inspector is long, but its mobile entries remain readable. |
| Decorative restraint | **2** | There is no cover art, ornamental animation, neon decoration, or invented content. The small finding glow is subordinate to the evidence. |
| Content | **2** | Aggregate-only limitations, model boundaries, `NOT VERIFIED`, distance semantics, and historical/deployment separation remain visible and correctly prioritized. |
| Craft | **1** | The custom composition is considered and memorable, but native chart chrome and the narrow mobile tables remain visibly unfinished at the final polish level. |

**Follow-up total: 23/24.** Craft remains 1 because the native chart toolbars are
visually dense and the selected inspector is still a long evidence surface; this
is intentionally not a perfect score.

## UX areas

Scores use 0 = absent/broken, 1 = high friction, 2 = usable with material
friction, and 3 = clear and strong. Baseline comparisons refer to the five
1/3 findings in `reports/design-critique.md`.

| UX area | Score / 3 | Baseline -> final | Evidence and judgment |
|---|---:|---:|---|
| Map centrality and first-viewport orientation | **2** | 1 -> 2 | `aggregate/1440-overview-viewport.png` shows the map plot, controls, caveat, and Explore/Prediction actions in the first viewport. The 375 capture reaches the map card and plot at the bottom of the viewport, but only the upper plot is visible; mobile is improved, not fully dominant. |
| Compact header and mobile entry | **3** | 1 -> 3 | `aggregate/375-overview.png` shows one API-ready indicator, a compact refresh control, and all four tabs in a readable 2x2 grid with an obvious active underline. The same entry pattern is stable across Explorer, Predict, and Research. |
| Explorer filter clarity and inspector usefulness | **2** | 1 -> 2 | Aggregate `Explorer Guide` explains density mode and disabled individual-point controls; refreshed `points/1440-selected-inspector.png` and `points/375-selected-inspector.png` show selected cluster, nine descriptors, readable nearest-track key/value entries, and a keyboard sample picker. The inspector is now useful, but the phone surface is still vertically deep and the comparison table remains bounded. |
| Prediction result hierarchy and distance disclosure | **2** | 1 -> 2 | Empty captures show no empty plot/table scaffold; refreshed `aggregate/375-predict-empty.png` shows a bordered `DISTANCE BREAKDOWN` disclosure with a caret. `aggregate/workflow/768-predict.png` shows a clear nearest-centroid card with two distance meters and supporting disclosures. The 375 success slice still requires scroll to see the entire result card. |
| Research progressive evidence | **3** | 1 -> 3 | Refreshed `points/375-research.png` shows a visible bordered/careted supporting-evidence disclosure after the open finding and model-comparison layers, with Methodology separately collapsed. The three-layer path is now discoverable on mobile. |
| Mobile data readability | **2** | 1 -> 2 | Refreshed `points/375-selected-inspector.png` replaces the clipped nearest-track table with readable stacked entries, while `aggregate/375-explorer.png` explicitly says to scroll the comparison table horizontally for both clusters and units. Bounded scroll is still a step, but it is signposted and acceptable. |
| Scientific caveat and trust hierarchy | **3** | strong baseline -> 3 | Aggregate overview and Explorer explicitly state that cells are population summaries; prediction cards state distances are not probabilities; Research and model-boundary cards keep historical equivalence `NOT VERIFIED` visible. This is one of the strongest parts of the final hierarchy. |
| Active/disabled state clarity | **2** | 1 -> 2 | Active tabs, Density/PCA 3D/Constellation selection, cluster colors, selected sample ring, and prediction verdict are clear. Disabled aggregate controls use a crossed-out appearance that is recognizable but slightly cryptic without the adjacent guide. |

## Follow-up verdict on the previous High findings

### Resolved: mobile inspector and comparison evidence

The refreshed `points/375-selected-inspector.png` replaces the cramped nearest
track table with readable stacked entries: Sample, Cluster, Instrumentalness,
Energy, and Distance each have their own labeled value. The nine descriptors
also align one per row. The comparison table in `aggregate/375-explorer.png`
still requires a bounded horizontal scroll to reveal all clusters and units,
  but the new explicit horizontal-scroll hint makes that action
explicit. Because bounded scroll is signposted and accepted for this table,
the prior High readability finding is resolved and is now a Medium polish note
only.

### Resolved: chart toolbar overlap

The refreshed phone captures show the Explorer toolbar in a separate reserved
strip above the plot, while the compact Overview hides the native modebar. The
comparison figure toolbar is also reserved rather than painted over chart
content. The controls remain visually dense, but they no longer obscure titles,
legends, or selected points. The prior High overlay finding is resolved.

## Remaining medium-priority visual gaps

- **Bounded table access:** The comparison table initially exposes only the first
  columns on a 375px screen. Its explicit hint is sufficient for acceptance,
  but a subtle edge gradient or preserved scrollbar cue could make the hidden
  Cluster 1/Unit columns even more discoverable.
- **Inspector depth:** The refreshed key/value cards are readable, but eight
  nearest-track entries make the phone inspector a long scroll surface. A small
  count or "show more" affordance could improve scanability without hiding data.
- **Post-submit mobile framing:** `aggregate/workflow/375-predict.png` begins
  with the lower form and shows only the top of the result card in the 812px
  viewport. Verify the final scroll target leaves the nearest-centroid heading
  and both distance rows visible when possible; this is a framing refinement,
  not a clipping blocker.
- **Modebar density:** The reserved strips solve overlap, but the black native
  toolbar is visually dense against the dark theme. Keep its hit areas and
  keyboard access, while considering a quieter strip treatment in a later pass.
- **Disabled aggregate controls:** PCA/3D/Constellation and cluster toggles are
  visually crossed out in aggregate mode. The adjacent guide explains why, but
  a short inline "aggregate mode" label or a more conventional disabled style
  would reduce ambiguity.

## Final recommendation

The refinement is visually successful and materially better than the baseline:
the map is now an immediate product signal, mobile entry is discoverable,
prediction and research evidence are progressively disclosed, and the genuine
scientific caveats remain in the visual hierarchy. The two previous High
concerns are resolved in the refreshed captures. I would accept the direction;
the remaining bounded-scroll, inspector-depth, toolbar-density, and mobile
post-submit framing notes are Medium polish gaps rather than blockers.

This report is screenshot-based. It does not independently prove keyboard
focus order, reduced-motion behavior, contrast ratios, or browser compatibility
outside the captured environment.
