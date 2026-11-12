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

A research-oriented hero, the interactive **cluster space preview** (every
fourth verified sample point, with 2D/3D/density controls), a compact model fact
sheet, the dominant instrumentalness finding, population balance, entry cards
and model identity. The preview is explicitly labeled and never claims to be
the full sample. In public aggregate mode no individual points exist; the
preview renders the density grid with a disclosure.

### Cluster Explorer

- **2D / 3D Plotly views:** PCA coordinates with explained variance on the axes;
  zoom, pan, rotation, hover and Plotly's modebar. Colors are stable teal/violet
  for Clusters 0/1; 2D markers also use circle/diamond symbols; legends include
  sample counts.
- **Cluster filtering:** Both / Cluster 0 / Cluster 1; the view updates without a
  page reload.
- **Selection:** click a point to highlight it and load its permitted acoustic
  descriptors plus up to eight nearest **sampled** tracks. Neighbor distance is
  Euclidean in fitted RobustScaler F9 space, not screen distance.
- **Density:** a log-color-scaled 40×40 aggregate grid over the full training
  population; cells with fewer than 10 tracks are omitted. This is the public
  fallback and never labels a cell as a track.
- **Constellation:** an optional Three.js GPU point scene using the same PCA
  coordinates. Drag to orbit, scroll to zoom, hover for details, click to inspect
  and filter clusters. It loads lazily; if WebGL or the bundle is unavailable the
  view falls back to aggregate density and the Plotly views stay available.
- **Reset view** resets the camera/zoom, not the scientific filters.
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
limit live in a disclosure. Failed predictions clear stale output; the result
component scrolls into view after a successful response (motion respects the
user preference). The example is explicitly synthetic and is not research
evidence.

### Research & Methodology

The page explains the unsupervised question, authorized data preparation, F5/F9
representations, RobustScaler geometry, the dominant instrumentalness finding,
the historical-vs-deployment identity split, archived historical evidence,
controlled F5/F9 and K-Means/GMM comparisons, interactive figures and limits.
Each number is labeled as archived, deployment training-population or a new
development comparison. The historical Holdout is shown as closed and is never
recomputed; no cross-geometry leaderboard is created. See
[RESEARCH.md](RESEARCH.md).

## Accessibility, responsiveness and states

- Verified at 1440×900, 768×1024 and 375×812. Overview/Explorer/Predict rows
  stack at ≤900px; the tab bar scrolls horizontally; no page-level horizontal
  overflow. Wide tables scroll inside bounded containers.
- Keyboard: native controls, custom Explorer buttons with `aria-pressed` and
  `role="status"`, visible 2px teal focus outlines. The Plotly canvas is
  pointer-based; exact tables and the density view are the keyboard-accessible
  data equivalents. Plotly modebar buttons are focusable.
- Contrast: all text token pairs tested at ≥4.5:1 (primary 17.9, secondary 12.9,
  muted 7.3 on the page). The cluster identity never depends only on color.
- Reduced motion: CSS transitions/animations are removed; Plotly transitions are
  disabled; the constellation has no auto-rotation or animation loop.
- States: loading, API ready, backend offline, partial visualization, aggregate
  only, empty prediction, invalid input, prediction error with stale clear, no
  selection, WebGL failure with density fallback and reduced-motion mode.

Measured on this checkout: first contentful paint ~100 ms, Overview map ready
~2.0 s, Explorer plot ~1.2 s after tab selection, 3D switch ~1.3 s, JS heap
~39 MB after load / ~115 MB after 18 view switches. These are local
measurements, not universal budgets.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q tests/test_api_real_model.py --run-real-api
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m build
```

The repeatable live check is:

```powershell
.\.venv\Scripts\python.exe plans/20261112-acoustic-observatory/verify-live.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_web_integration.py --run-real-web
```

It starts owned API/web processes on 8010/7871 in aggregate mode, checks all
three viewports, keyboard focus, reduced motion and the prediction flow, writes
`plans/20261112-acoustic-observatory/reports/browser.json`, and stops both
processes. Browser verification used Playwright 1.65.1 with Chromium against the live API
and Gradio services. It checked all four tabs, point selection and neighbors,
cluster filtering, 3D/density/constellation rendering, prediction success and
stale clearing, invalid input, keyboard tab order, focus outline, reduced motion,
and the 1440/768/375 viewports. Screenshots in `docs/screenshots/` were captured
from the real aggregate-mode application; they are not mockups.

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
separate publication decision; see [DEPLOYMENT.md](DEPLOYMENT.md). Actual public
publication is **BLOCKED** for this implementation.
