# Architecture

The application imports Python modules; it never executes notebook cells. The
original notebook remains methodological authority and is not a runtime
dependency. The runtime is one FastAPI backend and one Gradio frontend; no
database, queue, microservice, training endpoint or second inference
implementation exists.

## Offline preparation

| Module | Responsibility |
|---|---|
| [config.py](../src/spotify_cluster/config.py) | Research constants, immutable deployment-v1 recipe, historical gate, visualization/research constants and license disclosure. |
| [data.py](../src/spotify_cluster/data.py) | Authorized snapshot verification, canonical tracks and the separate genre bridge. Metadata never enters the F9 matrix. |
| [training.py](../src/spotify_cluster/training.py) | Offline fitting, raw-unit profiles and independent numerical checks. |
| [model_store.py](../src/spotify_cluster/model_store.py) | Bundle identity, checksums, fitted-state checks and environment compatibility. |
| [verification.py](../src/spotify_cluster/verification.py) | Deterministic private sample selection and independent centroid arithmetic. |
| [visualization.py](../src/spotify_cluster/visualization.py) | Visualization-only PCA, deterministic stratified sampling, occupancy aggregation, artifact writer/loader, integrity checks and scaled-space neighbors. |
| [research.py](../src/spotify_cluster/research.py) | Controlled F5/F9 and K-Means/GMM training-population comparisons; archived historical labels; aggregate artifact writer/loader. |
| [scripts/export_model.py](../scripts/export_model.py) | Model export orchestration; historical reconstruction remains gated. |
| [scripts/prepare_visualization.py](../scripts/prepare_visualization.py) | New-only private/public visualization artifact preparation. |
| [scripts/prepare_research.py](../scripts/prepare_research.py) | New-only controlled comparison artifact preparation. |

The visualization and research artifacts are separate from the model bundle and
from each other. Each records model ID, dataset SHA-256, prepared fingerprint,
software versions and a checksummed verification report. They are loaded only by
the backend.

## Backend

- [api/app.py](../src/spotify_cluster/api/app.py) owns the FastAPI factory,
  trusted directory resolution, lifespan state, optional artifact loading,
  GZip compression and sanitized error boundaries.
- [api/schemas.py](../src/spotify_cluster/api/schemas.py) owns HTTP contracts,
  including the visualization and research response unions.
- [api/routes.py](../src/spotify_cluster/api/routes.py) adapts service and
  artifact outputs; it does not fit models or read the CSV.
- [inference.py](../src/spotify_cluster/inference.py) owns strict input
  validation and single/batch inference. The model is loaded once per worker in
  the lifespan; prediction never fits.

Optional artifacts are loaded once per worker. A missing, mismatched or invalid
artifact marks only that feature unavailable; it does not fail model readiness.
`GET /api/v1/health` remains the readiness endpoint. The API never serves the
dataset, notebook, model bundle, verification sample or arbitrary paths.

## Frontend

- [web/app.py](../src/spotify_cluster/web/app.py) owns the Blocks shell, tab
  layout, event wiring, host/port policy and Gradio launch restrictions.
- [web/api_client.py](../src/spotify_cluster/web/api_client.py) owns HTTPX calls,
  timeouts, response validation, identity checks and sanitized errors.
- [web/components.py](../src/spotify_cluster/web/components.py) owns presentation
  HTML, payload validation and event handlers, independently testable without a
  Gradio server.
- [web/figures.py](../src/spotify_cluster/web/figures.py) builds Plotly figures
  over verified aggregate values; [web/charts.py](../src/spotify_cluster/web/charts.py)
  owns tables and units.
- [web/explorer.py](../src/spotify_cluster/web/explorer.py) owns the custom HTML
  Explorer: Plotly 2D/3D/density rendering, cluster filtering, point selection,
  tooltips, reset, lazy Three.js constellation import and density fallback.
- [web/assets.py](../src/spotify_cluster/web/assets.py) copies reviewed browser
  assets to a temporary Gradio-served directory outside the checkout. Plotly is
  served from the installed package; `constellation.js` is the vendored Three.js
  bundle.
- [web/theme.py](../src/spotify_cluster/web/theme.py) owns design tokens, the
  Gradio theme and application CSS.

The browser never assigns clusters, loads the model, or reads the dataset. It
calls Gradio events; Gradio calls FastAPI over HTTP. Stale visualization or
research state is cleared when model identities disagree. The points artifact
supports 2D/3D selection and nearest-neighbor details; the approved public
deployment serves it with no track identifiers. The aggregate fallback mode
shows density only and never exposes individual tracks.

## Three.js constellation

`scripts/constellation/entry.js` is bundled by the pinned `three@0.187.0` +
`esbuild` toolchain into `src/spotify_cluster/web/static/constellation.js`.
The browser imports it lazily only when the user selects **Constellation**. It
renders the same verified PCA coordinates and cluster assignments with GPU
points, orbit controls, raycast picking, hover details, cluster filtering and a
camera reset. Failure or missing WebGL falls back to aggregate density; Plotly
remains the primary scientific Explorer. The bundle and MIT license ship in the
wheel.

## Data flow and invariants

1. Offline: CSV (hash-verified) + trusted bundle → model profiles, visualization
   artifact, research artifact. No model is fitted during online requests.
2. FastAPI: one InferenceService + optional Visualization/Research payloads per
   worker. Identity checks pair profile/artifact data with the loaded model.
3. Gradio: HTTP client fetches public aggregates/visualization/research; passes
   raw F9 to prediction; validates model identity across responses.
4. Browser: Plotly/custom components render, hover, select and filter bounded
   payloads. No raw dataset or private bundle is reachable.

FastAPI initialization creates one InferenceService per lifespan and reuses it;
requests obtain it from application state. Model loading never happens at import
time. The loader checks model/profile identity and the HTTP layer selects safe
public fields. The historical Holdout is never reopened. There are no
retraining, model export or privileged file endpoints.
