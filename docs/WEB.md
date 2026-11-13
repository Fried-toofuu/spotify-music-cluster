# Web application

The browser uses Gradio Blocks and custom HTML components; Gradio sends
HTTP/JSON requests through HTTPX to the existing FastAPI backend. Only FastAPI
loads the trusted model and artifacts. The frontend never reads the CSV,
notebook, verification inputs or joblib bundle, fits a model, assigns clusters or
computes model distances.

## Install and run

Use Python 3.12 and the environment in [README](../README.md). Scientific pins
are exact; frontend dependencies are the `web` extra and `constraints.txt` for
reproducible installs. The supported Gradio range is 6.31 through 6.x; this
implementation verifies **6.31.0** with Plotly 6.9.0.

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[api,web,dev]"
```

Terminal 1:

```powershell
$env:SPOTIFY_MODEL_DIR = (Resolve-Path "artifacts/deployment-v1").Path
$env:SPOTIFY_VISUALIZATION_DIR = (Resolve-Path "artifacts/visualization-v1").Path
$env:SPOTIFY_RESEARCH_DIR = (Resolve-Path "artifacts/research-v1").Path
.\.venv\Scripts\python.exe -m uvicorn spotify_cluster.api.app:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
$env:SPOTIFY_API_BASE_URL = "http://127.0.0.1:8000"
.\.venv\Scripts\python.exe -m spotify_cluster.web.app
```

Open <http://127.0.0.1:7860>. The frontend binds loopback by default. For a
container/reverse proxy, `SPOTIFY_WEB_HOST=0.0.0.0` and `SPOTIFY_WEB_PORT` are
accepted; arbitrary host names are rejected. No public sharing tunnel is used.

The backend URL is operator configuration only; visitors cannot change it. HTTPX
uses a 3-second connect and 15-second operation timeout, disables environment
proxies and does not follow redirects. There is no browser-to-FastAPI request or
CORS requirement. The screen is one Gradio frontend and one FastAPI service.

Charts are Plotly figures rendered through `gr.Plot`; the interactive Explorer is
a custom Gradio HTML component with locally served Plotly.js. Gradio 6.31's
native `BarPlot` is not used. The launcher strips bracketed IPv6 `NO_PROXY`
entries before Gradio imports because httpx 0.28 rejects them.

## The four tabs

### Overview

A compact two-column introduction beside the interactive **cluster space preview** (every
fourth verified sample point, with 2D/3D/density controls), a compact model fact
sheet, the dominant instrumentalness finding, population balance and model identity
below. One primary Explore Acoustic Space action enters the Explorer; Live
Prediction is secondary. Scientific Context keeps caveats available on demand.
The header consolidates readiness and optional-data warnings into one status
with a compact refresh utility; initial loading remains automatic. The preview is explicitly labeled and never claims to be
the full sample. In aggregate fallback mode no individual points exist; the
preview renders the density grid with a disclosure. The approved public points
mode enables the same 2D/3D/density preview as the local points artifact.

### Cluster Explorer

- **2D / 3D Plotly views:** PCA coordinates with explained variance on the axes;
  zoom, pan, rotation, hover and Plotly's modebar. Colors are stable teal/violet
  for Clusters 0/1; 2D markers also use circle/diamond symbols; legends include
  sample counts.
- **Cluster filtering:** Both / Cluster 0 / Cluster 1 is a mutually exclusive choice of
  visible sets. Both compares both clusters; each numbered choice isolates one.
  Filtering preserves Plotly camera/zoom and an eligible selection. Hiding the
  selected cluster clears both the highlight and inspector.
- **Selection:** click or tap a point, or enter a zero-based sample number and
  choose Inspect sample by keyboard, to highlight it and load its permitted acoustic
  descriptors plus up to eight nearest **sampled** tracks. Neighbor distance is
  Euclidean in fitted RobustScaler F9 space, not screen distance.
- **Density:** a log-color-scaled 40×40 aggregate grid over the full training
  population; cells with fewer than 10 tracks are omitted. This is the public
  fallback and never labels a cell as a track.
- **Constellation:** an optional Three.js GPU point scene using the same PCA
  coordinates. Drag to orbit, scroll to zoom, hover for details, click to inspect
  and filter clusters. It loads lazily; if WebGL or the bundle is unavailable the
  view falls back to aggregate density and the Plotly views stay available.
- **Reset view** restores camera/zoom and clears selection while preserving filters.
  Changing projection clears selection and may reset the camera. A guide explains
  the active mode when no point is selected; density shows population guidance.
  Inspector responses are gated by the selected sample index, and rapid events
  retain the latest selection/clear request. Tab changes retain the current map.
- **Touch 3D:** Enable rotation explicitly opts into canvas gestures. Resume page
  scrolling returns vertical scrolling; each projection change starts unlocked
  for page scrolling. Hover is supplementary, not required for inspection.
- The exact nine-feature comparison table, raw-unit mean/median/std/Q1/Q3/IQR
  table and disclosure text remain available for verification and accessibility.

The model's cluster assignments come from the deployed F9 representation. PCA
display coordinates are not model training distances. Stratified sample
proportions are not population proportions.

### Predict Cluster

Enter all nine raw F9 descriptors (sliders for the seven [0,1] features; number
fields for tempo BPM and loudness dB). The form is grouped into core acoustic
character and rhythm/energy/dynamics; a synthetic illustrative vector can be
loaded into the form but produces no result until submitted to the real API.

The result card shows the assigned cluster, population count/share, both
centroid distances in exact numeric form, normalized distance meters, the current
cluster profile and the two most distinguishing raw-unit means. The smaller
distance determines the assignment; distances are **not probabilities** and are
never converted to confidence. Model identity and the historical-equivalence
limit live in a disclosure. Failed predictions clear stale output. Distance Breakdown holds the secondary
chart, exact numerical table and units. The result component scrolls into view
once after the Gradio response completes (motion respects the
user preference). The example is explicitly synthetic and is not research
evidence.

### Research & Methodology

Research Findings leads with the unsupervised question and feature dominance.
Model Comparison groups the controlled F5/F9 and K-Means/GMM results; Methodology
and Reproducibility discloses data preparation, representation, historical identity
and limits. Supporting figures and exact archived evidence exposes the Plotly
figures and one exact historical table. Each number keeps its original provenance;
ARI is partition agreement, not accuracy. No cross-geometry leaderboard or fresh
Holdout score is created. See [RESEARCH.md](RESEARCH.md).

## Accessibility, responsiveness and states

- Verified at 1440×900, 768×1024 and 375×812. Overview/Explorer/Predict rows
  stack at ≤900px; the four tabs form a visible two-column mobile grid; no page-level horizontal
  overflow. Wide tables scroll inside bounded containers.
- Keyboard: native controls, custom Explorer buttons with `aria-pressed` and
  `role="status"`, visible 2px teal focus outlines. The sample-number form provides keyboard access to point
  descriptors and neighbors; exact tables expose population aggregates. Plotly modebar buttons are focusable.
- Contrast: text token pairs meet AA; measured permanent-light values are in
  [DESIGN.md](DESIGN.md#accessibility). Cluster identity also uses labels/symbols.
- Reduced motion: CSS transitions/animations are removed; Plotly transitions are
  disabled; the constellation has no auto-rotation or animation loop.
- States: loading, API ready, backend offline, partial visualization, aggregate
  only, empty prediction, invalid input, prediction error with stale clear, no
  selection, WebGL failure with density fallback and reduced-motion mode.

Measurements and screenshot comparisons are stateful evidence in the
[refinement delivery report](../plans/20261112-ui-refinement/reports/delivery.md).
Local timings are not Render cold-start or field Core Web Vitals guarantees.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q tests/test_api_real_model.py --run-real-api
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m build
```

The repeatable aggregate-mode live check is:

```powershell
.\.venv\Scripts\python.exe plans/20261112-acoustic-observatory/verify-live.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_web_integration.py --run-real-web
```

It starts owned API/web processes on 8010/7871 with `SPOTIFY_PUBLIC_MODE=1`,
checks all four tabs, aggregate density, profile updates, prediction success and
stale clearing, keyboard tab order, focus outline, reduced motion and the
1440/768/375 viewports, writes
`plans/20261112-acoustic-observatory/reports/browser.json`, and stops both
processes. The private points mode, Plotly 3D, point selection and neighbors,
Three.js constellation and the WebGL-disabled SVG fallback were exercised in
Chromium against the points artifact during the upgrade; the committed script
mounts the aggregate artifact so per-track coordinates never enter committed
evidence. The points artifact is served only from the private deployment
dataset. Screenshots in `docs/screenshots/` were captured from the real
aggregate-mode application; they are not mockups.

The refinement's points-mode checks reuse a trusted local backend and a separately
owned verification frontend on port 7872. Run
`plans/20261112-ui-refinement/verify-browser.py` against that frontend to exercise
real picking, neighbors, camera/filter continuity, touch opt-in, prediction errors,
keyboard controls, reduced motion and WebGL/bundle fallbacks. Its points screenshots
stay ignored; screenshots distributed in docs must use aggregate mode. Record
console/network failures, manually inspect all four tabs at 1440x900, 768x1024 and
375x812, and check shorter/intermediate layouts. Do not infer a pass from a Python
figure update alone.

## Privacy and local file serving

The entry point binds loopback, disables public sharing, browser auto-launch,
telemetry, run history, monitoring and MCP, and exposes no file input/output.
Gradio file serving uses a reviewed asset directory in the temporary filesystem;
the working tree is explicitly blocked and `GRADIO_ALLOWED_PATHS` is rejected.
Plotly is served from the installed package; the constellation bundle is a
vendored, pinned Three.js build with its MIT notice. The browser-visible asset
URL contains the operator-local absolute path of that reviewed file (Gradio's
file route); it contains no dataset, notebook or model data and the route is
restricted to the asset directory. This is a low-information path disclosure,
not a data-access path. The raw CSV, notebook,
model bundle, verification sample and private points artifact are not served.

Public hosting requires TLS, access/rate controls, provider permissions and a
separate publication decision; see [DEPLOYMENT.md](DEPLOYMENT.md). The existing public service remains an operator-owned deployment; UI refinement
does not itself authorize a push or redeployment.

## Permanent light verification

The application always renders the light palette, including a dark OS preference
and `?__theme=dark`. There is no theme control or stored preference. See
[design ownership](DESIGN.md#permanent-light-implementation) for Gradio compatibility.
With the trusted local API and frontend on 8000/7872, run:

```powershell
.\.venv\Scripts\python.exe plans/20261113-light-theme/verify-light.py
```

This checks all four tabs, all Explorer modes, explicit white 3D scenes, refresh,
reload and changing color preference at the three required widths. It writes
ignored points screenshots; retain aggregate mode for published documentation
screenshots. The full refinement interaction script above remains the regression
check for picking, camera, neighbors, filtering, prediction and fallback behavior.
