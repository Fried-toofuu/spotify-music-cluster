# Local REST API

The backend serves one operator-trusted deployment-v1 bundle and optional
checksummed visualization/research artifacts through the existing
[InferenceService](../src/spotify_cluster/inference.py). It does not train, read
the CSV, serve the dataset or expose arbitrary files. The
[Gradio web application](WEB.md) is an HTTP client of these endpoints.

## Install and run

Use Python 3.12 and the environment in [README](../README.md); exact runtime
pins are in [constraints.txt](../constraints.txt).

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[api,web,dev]"
$env:SPOTIFY_MODEL_DIR = (Resolve-Path "artifacts/deployment-v1").Path
$env:SPOTIFY_VISUALIZATION_DIR = (Resolve-Path "artifacts/visualization-v1").Path
$env:SPOTIFY_RESEARCH_DIR = (Resolve-Path "artifacts/research-v1").Path
.\.venv\Scripts\python.exe -m uvicorn spotify_cluster.api.app:app --host 127.0.0.1 --port 8000
```

The source checkout defaults to its own artifacts; an installed wheel requires
explicit absolute `SPOTIFY_MODEL_DIR` and optional `SPOTIFY_VISUALIZATION_DIR`/
`SPOTIFY_RESEARCH_DIR` paths. The factory `model_dir`/`visualization_dir`/
`research_dir` arguments are the explicit test/operator seam. No HTTP input can
select a path. The model loader enforces the recorded environment and provenance.

## Endpoints and schemas

Swagger: <http://127.0.0.1:8000/docs>. Machine-readable contract:
<http://127.0.0.1:8000/openapi.json>. Explicit models live in
[schemas.py](../src/spotify_cluster/api/schemas.py); adapters in
[routes.py](../src/spotify_cluster/api/routes.py).

| Method | Path | Contract |
|---|---|---|
| GET | `/api/v1/health` | Readiness, service/version, `model_loaded`; 200 only with serving state |
| GET | `/api/v1/model` | Verified identity/profile, KMeans/K2, RobustScaler, F9 order, population, PCA, origin, historical status |
| GET | `/api/v1/clusters` | Model ID, raw-unit cluster statistics, scaled-space feature contributions, interpretation |
| POST | `/api/v1/predict` | One raw F9 object → one prediction |
| POST | `/api/v1/predict/batch` | `{"tracks": [...]}` → predictions in order, 1–100 records |
| GET | `/api/v1/visualization/meta` | `{available: true, ...}` with mode/PCA/sample/views/license, or `{available: false, reason}` |
| GET | `/api/v1/visualization/points` | Points view + occupancy; only when a **points** artifact is mounted |
| GET | `/api/v1/visualization/occupancy` | Aggregate density view |
| GET | `/api/v1/visualization/neighbors?index=<int>&k=<1-12>` | Selected point + nearest sampled tracks in fitted scaled F9 space |
| GET | `/api/v1/research/comparison` | Labeled controlled comparisons + archived evidence, or `{available: false, reason}` |

Predictions contain `model_id`, `cluster_id`, two `distances` in centroid order
[0,1], `distance_definition`, the current aggregate `profile`, `limitation`,
`reconstruction_status`, `deployment_profile` and `historical_equivalence`
(`not_verified`). Bounded descriptors are [0,1], tempo is finite nonnegative,
loudness is finite dB. Inputs are never clipped or imputed. Batch inputs are
bounded to 100 records.

With `SPOTIFY_PUBLIC_MODE=1`, the API refuses a per-track visualization artifact;
only the aggregate artifact is served, and the points/neighbors routes return
404 even if a private directory is mounted. The compose public configuration
sets this mode.

The visualization endpoints are additive and optional. The frontend checks
`model_id` on every artifact response; mismatched or stale artifacts are
discarded, and the UI shows an honest unavailable/aggregate state. The API
compresses responses over 1 KB with gzip (the 6,000-point payload is ~574 KB
uncompressed / ~207 KB gzip). Artifacts are loaded once per worker, not per
request. The API never serves the model bundle, dataset, notebook, verification
sample or file paths.

## Errors and privacy

| Situation | Result |
|---|---|
| Valid request | 200 |
| Invalid body/domain/JSON/batch or neighbors index | 422 with sanitized locations/types/messages |
| Request body over 64 KiB | 413 `{"detail":"Request body too large"}` |
| Optional artifact absent | 404 for its data route; `/meta` and `/research/comparison` return `available: false` |
| Serving dependency absent | 503 `{"detail":"Model service unavailable"}` |
| Invalid model artifact at startup | Startup aborts; no ready server |
| Unexpected internal failure | 500 `{"detail":"Internal server error"}` |

Validation responses omit input values and exception context. Internal errors
log the exception type without feature payloads. Startup logs retain loader
diagnostics for operators. Debug responses are disabled. CORS is not enabled.
The API offers no raw dataset, upload, model URL, retraining or filesystem
endpoint. The local API has no authentication or rate limiting; a public
deployment must terminate TLS and enforce request/rate limits at a reverse
proxy (see [DEPLOYMENT.md](DEPLOYMENT.md)).

Only operator-trusted local joblib bundles may be configured. Checksums detect
corruption; they are not signatures and cannot make an untrusted pickle safe.
The visualization/research JSON artifacts are checksummed and identity-paired,
but the same trust boundary applies: only operator-provided local directories.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q tests/test_api_real_model.py --run-real-api
.\.venv\Scripts\python.exe -m pytest -q tests/test_api_visualization.py
```

Normal tests use clearly labelled deterministic doubles and temporary software
bundles; they need neither the private data nor deployment artifacts.
`--run-real-api` requires the trusted bundle and checks real HTTP predictions
without reconstruction. The visualization tests cover availability, mode
privacy, identity mismatch, neighbors, gzip and response validation. Do not use
the older `--run-real-model` for an integration-only run; that separate historical
test includes a dataset load and reconstruction.

## Interpretation

This is unsupervised acoustic grouping, not genre or mood classification. Label
numbers have no fixed musical meaning. The deployed model's separation is
primarily along instrumentalness (97.30% of between-cluster SS in the current
artifact). Distances are Euclidean in fitted RobustScaler F9 space, not
probabilities or confidence percentages. The deployment refit is not verified
equivalent to the historical estimator and has no independent deployment Holdout
score. The historical Holdout remains closed. PCA visualization coordinates are
not model training coordinates and are not used for assignment. Aggregate
density cells are never individual tracks.
