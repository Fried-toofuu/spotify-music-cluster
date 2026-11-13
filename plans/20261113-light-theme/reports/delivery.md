# Permanent light theme delivery — 2026-11-13

## Implementation

Repository: `D:\spotify_music_cluster`; branch: `feat/observatory-ui-refinement`.
Base revision: `54f6f0166b84711522c34bfd74c9e489022eb0d2`.
This report records local verification before publication. Git history identifies
the theme commit; GitHub deployment records identify the current Render release.

**PASS:** one permanent Light Scientific Editorial appearance across Overview,
Cluster Explorer, Predict Cluster and Research & Methodology. No theme control,
stored preference, alternate palette, inference change or new dependency was added.

## Files and ownership

- `src/spotify_cluster/web/theme.py`: authoritative palette, generated CSS tokens,
  Gradio configuration, light enforcement and component states.
- `web/app.py`: passes the light head through supported Gradio launch options.
- `web/components.py`: token-colored SVG mark and semantic error styling hook.
- `web/explorer.py`: shared embedded palette, white Plotly paper/plots/3D scene,
  readable density colors, selection and disabled controls; small 3D label margins.
- `web/figures.py`: shared white chart surfaces, readable inside-bar labels and
  wrapped prediction-axis title. Data, ranges and calculations are unchanged.
- `scripts/constellation/entry.js` and built `web/static/constellation.js`: shared
  light scene/point colors, white filtered marks and charcoal selection marker.
- `tests/test_web_app.py`, `tests/test_web_charts.py`: accepted light expectations,
  explicit chart backgrounds and parity of Gradio compatibility slots.
- `docs/DESIGN.md`, `docs/WEB.md`, five `docs/screenshots/` images: current light
  design authority, repeatable checks and actual aggregate-mode screenshots.
- `.gitignore`, this plan, verification script and reports: keep point screenshots,
  logs and private fingerprints local; retain reproducible acceptance evidence.

## Tokens before and after

| Role | Previous | Delivered |
|---|---|---|
| Page | `#080d0f` | `#F7F9FC` |
| Surfaces 1 / 2 / 3 | `#0e1719 / #132326 / #193033` | `#FFFFFF / #F0F3F7 / #E8EDF3` |
| Primary / secondary / muted text | `#eef7f4 / #c4d6d2 / #8ba39e` | `#17212B / #556270 / #596775` |
| Divider / interactive boundary | `#22383a / #35565a` | `#E0E6ED / #7B8896` |
| Cluster 0 / Cluster 1 | `#5eead4 / #b7a4ff` | `#147D73 / #7055B9` |
| Primary hover | `#2dd4bf` | `#10665E` |
| Warning / error / success | `#f5c76a / #ff9b9b / #6ee7b7` | `#8A5B10 / #B42335 / #147D59` |
| Action text | `#04110f` | `#FFFFFF` |
| Density stops | dark charcoal to bright teal | `#5D9F96 / #3D9589 / #247F74 / #10665E` |

Spacing, typography, dimensions and interaction structure remain established.
Minor readability adjustments wrap the mobile prediction badge and distance-axis
title. Busy cards retain full text contrast with dashed boundaries rather than
fading the entire content. Sliders and distance rails have neutral outlines.

## Gradio and visualization behavior

Verified Gradio **6.31.0**, Plotly **6.9.0**, pinned Three.js **0.187.0**.
`theme.py` supplies the palette to every renderer. Gradio receives one `.set()`
call; all **84** explicit/inherited dark compatibility slots mirror light values.
They are framework compatibility slots, not a maintained alternate theme.

The head selects `__theme=light`, declares light color-scheme, and enforces removal
of Gradio's body `dark` class when its mounted client responds to host/system
preferences. No local storage or cookies are used. A real dark-preference check
proved the mount timing issue and the final remedy. Supported theme/head/CSS APIs
were checked against the installed source and the official
[theming guide](https://gradio.app/guides/theming-guide) and
[custom CSS/JS guide](https://gradio.app/guides/custom-CSS-and-JS).

Plotly paper, plotting area and 3D scene/axis planes are explicitly white. Axes,
ticks, annotations, legends, hover text and colorbar use shared light tokens.
Density still uses the identical log-count grid, omissions and hover values.
Circle/diamond marks, labels and counts retain non-color cluster identity.

Three.js receives the same palette from Explorer. Geometry, camera, picking,
zoom, filters, transitions and reset code remain intact. The scene is white,
the selected point is charcoal, and hidden cluster marks match the background.
The existing bundle was rebuilt with the pinned toolchain; no dependency changed.

## Verification results

| Check | Result | Evidence |
|---|---|---|
| Normal tests | PASS — 245 passed, 6 intentional skips | `python -m pytest -q` |
| Real model API | PASS — 2 passed | `tests/test_api_real_model.py --run-real-api` |
| Existing point interaction walk | PASS — 26 checks | [points-browser.json](points-browser.json) |
| Permanent light / dark preference | PASS — 27 checks | [light-browser.json](light-browser.json), [script](../verify-light.py) |
| Aggregate browser checks | PASS — 12 checks | [aggregate-browser.json](aggregate-browser.json) |
| Real unavailable backend | PASS — light recovery state | [offline-browser.json](offline-browser.json) |
| Ruff lint / format | PASS | `ruff check .`, `ruff format --check .` |
| Wheel / sdist build | PASS | `python -m build` |
| Protected notebook/data/artifacts | PASS — all 14 prior hashes match | Private local fingerprint comparison; hashes excluded |
| Diff / security review | PASS | Scoped source diff; no data, secrets, model or backend changes |

The interaction walk covers automatic loading, readiness, refresh, PCA 2D/3D,
density, real hover/click/selection, neighbors, filters, camera rotation/zoom/reset,
camera continuity, constellation reuse/disposal, prediction success/error recovery,
research disclosures, keyboard inspection, focus, touch opt-in and fallback paths.
The permanent-light walk also captures every section and mode under dark OS
preference, explicit dark URLs, refresh, reload and preference changes.

Runtime page errors and failed HTTP responses in the light walk: **0**. Gradio
logs SSE `AbortError`/connection-close messages during deliberate page navigation;
these are retained separately in `navigation_console_errors`, not hidden or
reported as application errors. Aborted `data` requests accompany navigation.
Interaction-time console errors: **0**. The regression walk intentionally blocks
WebGL/bundle paths to prove fallback; those controlled failures are expected.

## Contrast, screenshots and visual review

Measured primary/secondary/muted text on page: **15.45 / 5.91 / 5.50:1**.
Muted on the deepest light surface: **4.93:1**. White on primary teal: **4.99:1**.
Interactive neutral boundaries: **3.07–3.62:1**. Density stops on white:
**3.06–6.81:1**. See [contrast.json](contrast.json).

| Viewport | All four tabs | Modes / dark preference | Actual screenshots |
|---|---|---|---|
| 1440 × 900 | PASS | PASS | [Overview](aggregate/1440-overview-full.png), [Explorer](aggregate/1440-explorer-full.png), [Predict](aggregate/1440-predict-full.png), [Research](aggregate/1440-research-full.png) |
| 768 × 1024 | PASS | PASS | [Overview](aggregate/768-overview-full.png), [Explorer](aggregate/768-explorer-full.png), [Predict](aggregate/768-predict-full.png), [Research](aggregate/768-research-full.png) |
| 375 × 812 | PASS | PASS | [Overview](aggregate/375-overview-full.png), [Explorer](aggregate/375-explorer-full.png), [Predict](aggregate/375-predict-full.png), [Research](aggregate/375-research-full.png) |

All linked public captures use real aggregate-mode services. Point-mode screenshots
are local and ignored under `reports/points/`; they include 2D, 3D, constellation,
density, inspector, prediction success/error and dark-preference section captures.
Baseline point captures remain ignored in the earlier refinement baseline folder.
Screenshots were inspected with native vision at all three widths, including
full pages and visualization modes. No page-level overflow was detected.

The frontend render checker reported **0 errors**; its only warnings concern
Gradio's intentionally clipped screen-reader-only Loading text. Loaded screenshots
and the explicit readiness waits are the authority for loaded-state assessment.
Keyboard focus, reduced motion, labels and existing live regions are preserved.
This is measured theme contrast and browser QA, not a full WCAG conformance audit.

Design rubric (0–2): brief 2, hierarchy 2, rhythm 2, alignment 2, typography 2,
color discipline 2, depth 2, states 2, responsiveness 2, slop 2, content 2, craft 1:
**23/24**. Remaining craft limitation: Plotly 3D can place an axis title near the
canvas edge with the established camera; it was given modest margins, without
changing camera behavior or scientific geometry. Other labels and the 2D view
retain explained variance. Physical-device and manual screen-reader testing are
**NOT VERIFIED**; Chromium emulation was used.

## Review and scope decisions

[Independent design review](design-review.md) raised busy opacity, pale density,
rail visibility, disabled labels, error accents and stale docs. All were repaired
or reconciled against the final source. Existing point opacity is retained:
2D composites on white remain at least 3.02:1 and 3D at least 3.61:1. The explicit
white plotting surface is part of that invariant.

The focused UX/AX discovery scan **FAILS** existing discovery checks: missing
sitemap, raw-response title/meta description, optional markdown/LLM surfaces and
server-rendered content. The app is a client-rendered Gradio instrument. These
are recorded outside the theme DONE contract; adding SEO infrastructure would
exceed the explicit visual scope. No SEO or discoverability improvement is claimed.

Code review found no remaining blocking theme regression. The threat boundary
remains trusted local artifacts and HTTP-only inference. Token JSON contains only
operator-owned static colors; no user input was added to scripts. Existing HTML
escaping, launch restrictions, asset serving and scientific gates are unchanged.

## Publication snapshot

Commit/push and Render release verification are pending at this report snapshot.
The public service was inspected and still rendered the old dark revision
`54f6f01`. Do not infer deployment success from the local checks. The final release
receipt and user-facing delivery must state the actual push and hosted result.
