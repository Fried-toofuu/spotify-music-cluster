# Local REST API

The backend serves an operator-trusted deployment-v1 bundle through the existing
[InferenceService](../src/spotify_cluster/inference.py). It does not train or read
the CSV. The [Gradio web application](WEB.md) is an HTTP client of these endpoints;
no remote deployment is configured.

## Install and run

Use the Python 3.12 environment described in [README](../README.md). Scientific
pins are unchanged; API and development dependencies are declared in
[pyproject.toml](../pyproject.toml).

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[api,dev]"
$env:SPOTIFY_MODEL_DIR = "D:\spotify_music_cluster\artifacts\deployment-v1"
.\.venv\Scripts\python.exe -m uvicorn spotify_cluster.api.app:app --host 127.0.0.1 --port 8000
```

Stop with Ctrl+C. The source checkout defaults to its own
`artifacts/deployment-v1`, independently of the shell working directory.
`SPOTIFY_MODEL_DIR` and the factory's explicit `model_dir` must be absolute
operator-selected local paths. An installed wheel requires explicit configuration;
it does not search the working directory for a model. Explicit factory configuration
takes precedence over the environment. No HTTP input can select a path.

The [application factory](../src/spotify_cluster/api/app.py) loads one service per
lifespan and clears its reference on shutdown. Missing files, checksum failures,
incompatible environments, invalid fitted state, wrong provenance or mismatched
profiles fail startup. Inspect server logs for the operational cause. There is
no automatic reconstruction or fixture fallback. Each worker process would load
its own service; the local command starts one worker.

## Endpoints and schemas

Swagger: <http://127.0.0.1:8000/docs>. Machine-readable contract:
<http://127.0.0.1:8000/openapi.json>. Explicit request/response models live in
[schemas.py](../src/spotify_cluster/api/schemas.py); adapters live in
[routes.py](../src/spotify_cluster/api/routes.py).

| Method | Path | Contract |
|---|---|---|
| GET | `/api/v1/health` | Readiness, service/version and `model_loaded`; 200 only with serving state |
| GET | `/api/v1/model` | Verified identity/profile, KMeans/K2, RobustScaler, ordered features, population, PCA, origin and historical status |
| GET | `/api/v1/clusters` | Model ID, raw-unit cluster statistics, scaled-space feature contributions and interpretation |
| POST | `/api/v1/predict` | One raw F9 object → one prediction |
| POST | `/api/v1/predict/batch` | `{"tracks": [...]}` → `{"predictions": [...]}` in the same order, 1–100 records |

Input must contain exactly `acousticness`, `danceability`, `energy`, `valence`,
`tempo`, `loudness`, `speechiness`, `instrumentalness`, `liveness`. Key order may
vary; inference uses that exact F9 order. Integers and floating-point numbers are
accepted. Strings, booleans, nulls, NaN/infinities, missing/extra keys and nested
feature values are rejected. Audio domains reuse the
[inference validator](../src/spotify_cluster/inference.py): all descriptors except
tempo/loudness are in [0,1], tempo is nonnegative (zero allowed), loudness is finite
without an additional bound. Inputs are never clipped, normalized or imputed.

Illustrative input, **not** a stored research record or verified output example:

```powershell
$track = @{
  acousticness = 0.72; danceability = 0.61; energy = 0.38; valence = 0.44
  tempo = 118.5; loudness = -9.2; speechiness = 0.05
  instrumentalness = 0.81; liveness = 0.13
}
$base = "http://127.0.0.1:8000/api/v1"
Invoke-RestMethod "$base/predict" -Method Post -ContentType "application/json" -Body ($track | ConvertTo-Json)
Invoke-RestMethod "$base/predict/batch" -Method Post -ContentType "application/json" -Body (@{tracks = @($track, $track)} | ConvertTo-Json -Depth 3)
```

A prediction contains `model_id`, `cluster_id`, two `distances` in centroid order
[0,1], `distance_definition`, the associated aggregate `profile`, `limitation`,
`reconstruction_status`, `deployment_profile` and `historical_equivalence`.
Profiles retain the artifact's `count`, `share`, `mean`, `median`, sample `std`,
`q1`, `q3` and `iqr`; aggregate features use raw units. `/clusters` also exposes
the artifact's feature contributions in fitted scaled space. Model responses select
reviewed fields rather than exporting arbitrary metadata. HTTP historical status
is `not_verified`, mapped from the artifact's unchanged `NOT VERIFIED` spelling.

## Errors and privacy

| Situation | Result |
|---|---|
| Valid request | 200 |
| Invalid body, domain, JSON or batch size | 422 with `detail` error locations/types/messages |
| Serving dependency absent at runtime | 503, `{"detail":"Model service unavailable"}` |
| Invalid artifact at startup | Startup aborts; no ready server |
| Unexpected internal failure | 500, `{"detail":"Internal server error"}` |

Validation responses omit input values and exception context. Internal errors
log the exception type without feature payloads. Startup logs retain loader
diagnostics for operators. Debug responses are disabled. The API offers no raw
dataset, verification sample, upload, model URL, retraining or filesystem endpoint.
CORS is not enabled. No authentication or internet-facing rate limiting is added;
this is a loopback local MVP. A public service would require a separate deployment
and access-control decision, request-size/rate controls and reviewed logging.

Only operator-trusted local joblib bundles may be configured. Checksums detect
corruption; they are not signatures and cannot make an untrusted pickle safe.
See [model trust](MODEL_SERVING.md). Keep model files, CSV, notebook and private
verification sample ignored and outside public distributions.

## Interpretation

This is unsupervised acoustic grouping, not genre or mood classification. Label
numbers have no fixed musical meaning. Interpret the current model's profiles;
its separation is primarily along instrumentalness, as measured by its stored
between-cluster SS contributions. Distances are Euclidean in fitted RobustScaler
F9 space, not squared distances, probabilities or confidence percentages.
Single/batch distance arithmetic may differ in the last floating-point bits.
The deployment refit is not verified equivalent to the historical estimator and
has no independent deployment Holdout score. The historical Holdout remains closed.

## Verification

Normal software tests use clearly labelled deterministic doubles and temporary
software bundles; they require neither private data nor deployment artifacts.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q tests/test_api_real_model.py --run-real-api
.\.venv\Scripts\python.exe plans/20261112-fastapi-backend/verify-http.py
```

`--run-real-api` requires the existing trusted `artifacts/deployment-v1` bundle.
It checks private stored inputs against verified labels/distances through the
actual application, with fitting and raw-data reads blocked. It never exports
the sample. Do not use the older `--run-real-model` for an integration-only run:
that separate historical delivery test includes a dataset load and reconstruction.

The HTTP smoke script refuses an occupied port 8000, tracks its child PID, serves
on loopback, checks endpoints/Swagger/OpenAPI and invalid inputs, and requests
graceful Uvicorn shutdown in `finally`. It stores only sanitized result evidence.
Packaging and executed results are in the
[backend verification report](../plans/20261112-fastapi-backend/reports/verification.md).

Gradio sends raw F9 records over these HTTP contracts without loading another
pipeline or seeing private artifacts. Authentication, remote hosting and deployment
remain future work; [WEB.md](WEB.md) owns the local frontend workflow.
