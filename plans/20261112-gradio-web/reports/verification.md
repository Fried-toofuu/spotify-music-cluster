# Gradio web milestone verification — 2026-11-12

Delivered locally in `D:\spotify_music_cluster`. The existing FastAPI backend and
deployment-v1 artifact remain the inference authority. No model load, refit,
training, notebook execution, Holdout reopening, remote deployment or publication
occurred. The browser talks only to Gradio; Gradio talks only to the configured
FastAPI URL over HTTP.

## A. Implementation

Created:

- `src/spotify_cluster/web/{__init__,app,api_client,components,charts}.py`: package
  boundary, four-tab Blocks app, HTTPX client with sanitized errors, presentation
  handlers and aggregate-only table/figure builders.
- `tests/test_web_{client,components,charts,app,integration}.py`: contract, handler,
  chart, construction/import-isolation and opt-in local integration checks.
- `docs/WEB.md`: install, startup, tabs, input domains, verification and hosting
  boundaries.
- This plan's verification scripts and reports: delivery gates, wheel install,
  real HTTP/browser smoke and screenshots.

Modified:

- `pyproject.toml`: `web` extra adds `matplotlib>=3.9,<4` next to Gradio and HTTPX.
  Scientific pins, API/dev extras, build backend and discovery are unchanged.
- `tests/test_web_app.py`: added the NO_PROXY regression test; web chart/component
  tests follow the figure outputs.
- `docs/ARCHITECTURE.md`, `README.md`: frontend ownership and operational links.

### Chart engine decision

Gradio 6.31's native `BarPlot` renders correctly only on first paint. A minimal
reproduction outside this application showed that subsequent updates changed the
title and axis labels but kept the first bars; shrinking or regrowing the data left
stale categories. The milestone therefore uses Matplotlib figures through `gr.Plot`,
which was re-verified to change bars, labels and titles on every event. Charts are
static PNGs, so hover tooltips and zoom are not available; the exact tables beside
each chart carry the same aggregates.

### Startup compatibility

`import gradio` builds an HTTPX client, and HTTPX 0.28.1 rejects bracketed IPv6
entries such as `[::1]` in `NO_PROXY`. Windows tooling in this environment exports
that value, which made the frontend fail before construction. `spotify_cluster.web`
now strips only those brackets before Gradio imports; a subprocess regression test
covers it. No proxy or network behavior changes beyond that parse fix.

### Architecture boundaries

The web package imports shared feature config, Gradio, HTTPX, Pandas and Matplotlib
only. It never imports `training`, `model_store`, `inference` or `data`, never reads
the CSV, notebook or joblib bundle, and never assigns clusters. Consumed response
fields are validated before use. Refresh combines metadata and profiles only when
model identity and population agree. Predictions require the loaded dashboard's
model ID. Any failure clears the affected outputs.

## B. Real integration

- Artifact: `artifacts/deployment-v1`; model ID
  `spotify-f9-robust-k2-0828777db6924fe39e47335c19cc9363`.
- Training population 89,741; cluster counts 72,211 and 17,530; measured
  instrumentalness between-cluster SS share 0.9730218110901931 (97.302%).
- Through real loopback HTTP, model metadata and profiles loaded, the distribution
  figure patches matched the API counts, and the exact table matched shares.
- The private verification sample was used only in memory. Frontend prediction text
  and distance figure/table agreed with a direct API call and the stored expected
  values (rtol 1e-9, atol 1e-7). No raw sample values appear in reports or
  screenshots.
- The explicitly synthetic example submitted through the live Gradio event produced
  the same cluster and distances as a direct API call.
- Invalid input produced the visible `Loudness must be a finite number.` message
  and no stale result. Stopping the backend produced `Cannot connect` feedback and
  cleared prediction outputs; no offline success is fabricated.
- Gradio file-serving probes for the dataset, notebook and model bundle returned
  403/404. Both servers exited 0 and released ports 8000 and 7860.

## C. Executed gates

Commands ran from the project root with the project `.venv`, 2026-11-12.

| Gate | Command | Result |
|---|---|---|
| Full tests | `python -m pytest -q` | **PASS** — 196 passed, 6 skipped |
| Real API opt-in | `python -m pytest -q tests/test_api_real_model.py --run-real-api` | **PASS** — 2 passed |
| Lint | `python -m ruff check .` | **PASS** — exit 0 |
| Format | `python -m ruff format --check .` | **PASS** — exit 0 |
| Package build | `python -m build` | **PASS** — sdist and wheel built |
| Environment | `python -m pip check` | **PASS** — no broken requirements |
| Protected files | SHA-256 before/after | **PASS** — unchanged |
| Wheel install | `[api,web]` in isolated venv; import outside checkout | **PASS** — four tabs construct; no CSV/notebook/joblib/sample members |
| Real HTTP smoke | `verify-http.py` | **PASS** — real model, Gradio event, errors, offline, cleanup |
| Browser smoke | `verify-http.py --browser` | **PASS** — 3 viewports, 15 screenshots, no page errors |
| Render diagnostics | `render-check.mjs` | **PASS** — 0 errors, 3 known screen-reader-only warnings |
| Port cleanup | post-run probe | **PASS** — 8000 and 7860 released |

Evidence: [gates.json](gates.json), [pytest.txt](pytest.txt),
[pytest-real-api.txt](pytest-real-api.txt), [ruff-check.txt](ruff-check.txt),
[ruff-format.txt](ruff-format.txt), [build.txt](build.txt),
[wheel.json](wheel.json), [http-smoke-browser.json](http-smoke-browser.json),
[render-check.txt](render-check.txt), [protected-files.json](protected-files.json).

## D. Visual review

Performed with installed Chrome through Playwright, dark colour preference, at
1440×900, 768×1024 and 375×812. All four tabs were opened at each width; the
Explorer exercised Mean/Median, Instrumentalness/Tempo and both cluster selections,
and the Predict tab exercised invalid input and the synthetic example. Evidence:
12 tab screenshots plus 3 invalid-input screenshots in [screenshots](screenshots/).
No private feature values appear in them.

Issues found and repaired during this milestone:

- Stale native chart after any data change; replaced with Matplotlib `gr.Plot` and
  re-verified that selection/statistic/feature changes alter bars and titles.
- Mobile chart labels were unreadable with a wide figure; figures now use a compact
  4.6×2.9 layout with larger type and a 620px desktop cap, and were re-checked at
  375px.
- Earlier overflow fixes retained: wrapped tab navigation, stacked selectors,
  bounded tab panels, native labelled example button, zero-based magnitude axes.

Residual presentation limits: wide aggregate tables scroll horizontally on phones;
charts are static images without tooltips or zoom; only installed Chrome was
exercised; no formal WCAG or assistive-technology audit was performed. The tables
repeat all charted numbers as text.

## E. Final gate table

| Gate | Status |
|---|---|
| Frontend package imports | PASS |
| Gradio application constructs | PASS |
| Overview dashboard | PASS |
| Predict Cluster interface | PASS |
| Cluster Explorer | PASS |
| Research & Methodology | PASS |
| HTTP client error handling | PASS |
| Real FastAPI connection | PASS |
| Real-model frontend prediction | PASS |
| Cluster/profile chart accuracy | PASS |
| Local Gradio HTTP smoke | PASS |
| Full pytest | PASS |
| Ruff lint | PASS |
| Ruff format | PASS |
| Package build | PASS |
| Installed-wheel web imports | PASS |
| Model artifact preservation | PASS |
| Notebook preservation | PASS |
| Visual browser inspection | PASS |

## F. Preserved boundaries

- Notebook SHA-256 unchanged at
  `76a31ac55e385238761d7decbc5117cede6f1ad8a2c9285504e80c4a2526b178`.
- Model bundle SHA-256 unchanged at
  `9c23058262845f3efa2ac2acaf277a9e66ea90066561c893ab6844b586946435`.
- No refit, training, HTTP retraining, dataset read by the frontend, PCA/t-SNE
  scatterplot, probability conversion, genre claim or fabricated track content.
- Historical FULL/Holdout evidence stays archived; historical equivalence remains
  **NOT VERIFIED**; the Holdout stays closed.
- Local-only launch: loopback, `share=False`, no browser launch, analytics, run
  history, monitoring, MCP, file inputs/outputs or broad allowed paths.
- Remote hosting remains unauthorized and not implemented; requirements are listed
  in [WEB.md](../../../docs/WEB.md).

No unresolved blocking question remains for the local milestone. Browser-only
limitations above are recorded, not hidden.
