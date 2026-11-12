# Acoustic Observatory UI refinement local delivery · 2026-11-12

This report records the original local implementation and verification snapshot.
Later release validation and deployment do not change its historical status;
GitHub deployment records identify the published revision.

## Source and publication status at local delivery

- Repository: `D:\spotify_music_cluster`.
- Implementation branch: `feat/observatory-ui-refinement`.
- Base/HEAD: `7fb39ef9e0221e84951c8e7d607c5c7469165f70`.
- Implementation is in the working tree; no new commit, push, merge or deployment
  was performed. The implementation therefore has no separate commit SHA yet.
- Existing Render service: observed loading page, then API ready, real points,
  Explorer controls and PCA 3D rendering. It still presents the previous UI.
  Its deployed commit SHA and the refined UI on Render are **NOT VERIFIED**.
  No service settings, artifact credentials or public-data policy were changed.

## Release preparation · 2026-11-13

Fresh verification of the reviewed working tree passed: 244 normal tests with
6 intentional skips, 3 opt-in real-model/browser integration tests, 26 points-mode
browser checks at 1440×900, 768×1024 and 375×812, responsive/touch/offline edge
checks, Ruff lint/format, diff whitespace, wheel/sdist build and dependency consistency.
The notebook, dataset and trusted artifacts retain all 14 protected hashes.

Release review additionally repaired unchanged-refresh selection clearing, indexed
terminal/stale selection errors and density clicks being mistaken for sample indices.
Actual browser checks preserve Plotly and constellation cameras across refresh;
constellation refresh also preserves the scene instance. The response fixture only
replaces a rendered card so Gradio's component mount remains intact.

Publication was subsequently authorized for the existing Render-linked `main` branch.
The report does not claim deployment success; GitHub deployment records provide the
published commit and provider status. Private fingerprints, point screenshots, local
handoffs and journals are excluded from the release.

## Before and after

| Surface | Before | Delivered |
|---|---|---|
| Overview | Full-width introduction, five identity tags, prominent caveat and duplicate status before map | Editorial introduction beside genuine map; one Explore action, secondary prediction entry, one readiness indicator and compact refresh; expandable Scientific Context |
| Explorer | Small controls; toggle ambiguity; inspector separated from map; hidden selection could persist | Explicit Both/Cluster 0/Cluster 1 visible-set choice; 44px controls; adjacent guide/inspector; cleared hidden selection; keyboard sample inspection; preserved camera and zoom |
| Prediction | Result, chart and exact table simultaneously compete; empty chart scaffold | Result and concise distance comparison lead; Distance Breakdown retains exact values and chart on demand; one scroll after response completion |
| Research | Data, representation, comparison, history and duplicate archived tables exposed together | Research Findings, Model Comparison, then expandable Methodology and Reproducibility; supporting figures and one exact archived table remain available |

Measured map-card top after automatic load, using the same local application and
viewports (CSS pixels):

| Viewport | Baseline | Final |
|---|---:|---:|
| 1440×900 | 818 | 184 |
| 768×1024 | 825 | 525 |
| 375×812 | 1200 | 565 |

The desktop plot is visible in the first viewport. Mobile exposes the map much
earlier and uses a visible 2×2 navigation grid. Serif/sans/mono typography,
charcoal surfaces, teal/violet cluster colors and amber findings are retained.
Technical labels are larger. Dense mobile neighbor tables become labeled entries;
the population table has a visible horizontal-scroll hint and tested scroller.
Chart tools occupy a reserved strip, away from titles and legends.

## Interaction decisions and defects repaired

- Filtering keeps a selected sample only when its cluster remains visible.
  Reset and projection changes clear selection; reset preserves cluster filters.
- Plotly uses projection/reset UI revisions. Because wheel zoom can update its
  rendered camera ahead of layout/event state, the compatible renderer camera is
  captured before trace changes. Actual rotation, wheel zoom, filter continuity
  and reset were checked against the rendered camera, not only layout metadata.
- The inspector gates asynchronous cards by sample index; Gradio retains the
  latest selection/clear event. Tab changes retain the current map and selection.
- A keyboard sample-number form reaches the same real inspector and neighbors.
  Indices are sample-local, never Spotify track IDs. Hidden-cluster samples are
  rejected with a helpful message rather than producing a mismatched highlight.
- Narrow Plotly legends reserve space above marks: an actual touch diagnosis
  proved the previous upper-point tap hit the legend instead of the mark.
- Coarse-pointer 2D permits native vertical scrolling. 3D starts in page-scrolling
  mode; Enable rotation explicitly takes gesture ownership, and Resume page
  scrolling releases it. Actual emulated touch rotation and scrolling were tested.
- Constellation filters reuse a scene; leaving it disposes GPU resources. Generation
  guards discard late imports; a sample chosen while loading is highlighted once
  the scene becomes ready. Bundle/WebGL failures retain density/SVG alternatives.
- Prediction inputs, F9 order, HTTP inference, validation and exact distances are
  unchanged. Errors and example loading clear stale results. Gradio completion
  controls result scrolling; fixed polling timers were removed.

## Verification

| Check | Result | Evidence |
|---|---|---|
| Complete normal suite | **PASS: 244 passed, 6 skipped** | [pytest.txt](pytest.txt) |
| Real-model API inference | **PASS: 2 passed** | `pytest tests/test_api_real_model.py --run-real-api -q` |
| Existing opt-in aggregate browser integration | **PASS: 1 passed** | `pytest tests/test_web_integration.py --run-real-web -q` |
| Final points browser matrix | **PASS** | [points-browser.json](points-browser.json) |
| Aggregate browser workflow and captures | **PASS** | [aggregate-browser.json](aggregate-browser.json) |
| Reflow, text scaling, touch orbit/scroll, offline state | **PASS** | [edges.json](edges.json) |
| Console, runtime and HTTP error check | **PASS: zero errors** | [console-network.json](console-network.json) |
| Ruff lint/format and diff whitespace | **PASS** | `ruff check .`, `ruff format --check .`, `git diff --check` |
| Wheel and sdist build | **PASS** | [build.txt](build.txt) |
| Rebuilt Three.js bundle parity | **PASS** | [bundle.json](bundle.json) |
| Protected files and source boundary | **PASS: 14 hashes unchanged** | [integrity-security.json](integrity-security.json) |
| Independent code/security review | **PASS after repaired findings** | [integrated-review.md](integrated-review.md) |
| Independent visual review | **PASS: 23/24, no High findings remain** | [final-visual-review.md](final-visual-review.md) |

Required browser viewports: 1440×900, 768×1024, 375×812. Additional reflow checks:
320×640, 480×640, 1024×768, 812×375; root text scaling to 125% was also checked.
Chromium ran locally on Windows with software WebGL. No physical touch device,
Safari, Firefox or field screen-reader audit was available; those are **NOT VERIFIED**.

The points matrix covers four-tab navigation, 2D/3D, pointer hover, real clicks/taps,
selection/neighbor responses, keyboard sample selection, tab continuity, filtering,
density, reset, camera rotation/zoom, constellation picking/reuse/disposal, prediction
success/validation/recovery, research disclosure, focus and reduced motion. Ordinary
Gradio event-stream cancellations appear as `data / net::ERR_ABORTED`; these were
distinguished from failed resources. A separate console/network walk found no HTTP
failures. Bundle failure was intentionally induced only in the fallback check.

## Accessibility and performance

Twenty-four foreground/surface token pairs were calculated: minimum contrast
**5.18:1** ([contrast.json](contrast.json)). Keyboard prediction, sample inspection,
visible focus, disclosure and reduced motion were exercised. Exact population data
remain available independently of a canvas; color is supplemented by labels/shapes.
Native Plotly modebar targets remain third-party controls; this is not a blanket
WCAG certification.

Final local points-mode map-ready timings were approximately **2.2–3.3 seconds**
in the recorded three-viewport run. These measure local navigation to a visible
loaded plot, with existing backend readiness and software WebGL; they are not
field Core Web Vitals or a claimed speedup. No benchmark improvement is asserted.
Tab changes no longer request redundant Explorer payloads; constellation loading
remains lazy, and filtering reuses the scene. No new runtime dependency was added.

The render checker found no errors. Its remaining clipped-text warnings concern
Gradio's intentionally screen-reader-only loading element, not visible content.
Loaded screenshots and manual visual review supplement this early-load checker.

## Scientific and security integrity

No backend/scientific source changed. Dataset, notebook, deployment model,
visualization/research artifacts and stored evidence retain their original hashes.
The historical Holdout was not reopened or evaluated. No refit, retraining,
archived-metric recalculation or synthetic research observation was performed.
PCA remains display-only; fitted scaler and centroids remain paired in the trusted
Pipeline. Population summaries still use full counts, not stratified sample shares.

Structured credential scan found no secrets in changed source and no tracked dotenv
files. The scoped review found no new URL/path/command/upload/auth boundary.
Only permitted sample indices/descriptors and existing aggregate values are displayed.
Points captures stay ignored; distributable docs screenshots use aggregate mode.

**Known pre-existing dependency issue:** pip-audit reports 40 Pillow 12.3.0
advisories, with fixes in 13.0.0. Installed Gradio requires Pillow below 13. The app
has no image/file input and this change adds none; dependency remediation remains
outside this UI patch rather than forcing an incompatible upgrade. See the existing
[deployment dependency guidance](../../../docs/DEPLOYMENT.md#dependency-audit) and
[audit output](dependency-audit.json). The constellation build's npm audit found
zero vulnerabilities in its four-package dependency tree.

The optional discovery scan remains **FAIL with pre-existing findings**: the
Gradio service has no sitemap, server title or meta description, plus optional
discovery-surface warnings. Baseline and final findings are equivalent
([baseline](discovery-baseline.json), [final](discovery-final.json)). No SEO framework,
public-content route or data audience was added to satisfy an unrelated scanner.

## Screenshots and modified files

Distributable actual screenshots: [Overview desktop](../../../docs/screenshots/overview-1440.png),
[Overview phone](../../../docs/screenshots/overview-375.png),
[Explorer](../../../docs/screenshots/explorer-density-1440.png),
[Prediction](../../../docs/screenshots/predict-result-1440.png),
[Research](../../../docs/screenshots/research-1440.png).
The complete aggregate three-viewport captures are in [aggregate](aggregate/).
Local ignored points captures include PCA 3D, selected inspector and constellation
in `reports/points/`; they were visually inspected, not generated mockups.

Product/source: `web/app.py`, `web/components.py`, `web/explorer.py`,
`web/theme.py`, `web/figures.py`, `web/static/constellation.js` under
`src/spotify_cluster/`, and `scripts/constellation/entry.js`.
Tests/tooling: `tests/test_web_components.py`, the existing
`plans/20261112-acoustic-observatory/verify-live.py`, `.gitignore`, and the new
refinement plan, verification scripts and evidence under this directory's parent.
Docs: `AGENTS.md`, `README.md`, `docs/DESIGN.md`, `docs/WEB.md`,
`docs/DEPLOYMENT.md`, and the five `docs/screenshots/` files linked above.

## Remaining publication and validation limits

- **NOT VERIFIED:** refinement on Render, deployed source SHA, physical touch device,
  Safari/Firefox, field performance and full assistive-technology certification.
- **FAIL (pre-existing):** optional discovery scan and dependency audit described above.
- **No push/deployment:** requires a separate release decision; existing public service
  was left operational. Rollback was documented against provider guidance, not exercised.
- **PASS:** local implementation, required viewport/interaction checks, scientific
  integrity, and owned verification-process cleanup (recorded at final handoff).

All owned verification ports are released; pre-existing services on 8000/7860
were left running. Final hashes remain unchanged:
[cleanup and integrity](cleanup-integrity.json). The automatic local journal is
in `plans/journals/2026-11-12-refine-acoustic-observatory-ui.md`; AgentWiki
publication was skipped. No external publication was requested or performed.
