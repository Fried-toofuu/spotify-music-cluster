# Local Gradio web application

The browser uses Gradio Blocks; Gradio sends HTTP/JSON requests through HTTPX to
the existing FastAPI backend. Only FastAPI loads the trusted model. The frontend
never reads the CSV, notebook, verification inputs or joblib bundle, fits a model,
or assigns clusters itself. No remote deployment is configured.

## Install and run

Use Python 3.12 and the environment in [README](../README.md). Scientific pins stay
unchanged; frontend dependencies are the `web` extra in [pyproject](../pyproject.toml).
The supported range is Gradio 6.31 through 6.x; this milestone verifies 6.31.0.

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[api,web,dev]"
```

Terminal 1, from the project root:

```powershell
$env:SPOTIFY_MODEL_DIR = "D:\spotify_music_cluster\artifacts\deployment-v1"
.\.venv\Scripts\python.exe -m uvicorn spotify_cluster.api.app:app --host 127.0.0.1 --port 8000
```

Terminal 2, from the same root:

```powershell
$env:SPOTIFY_API_BASE_URL = "http://127.0.0.1:8000"
.\.venv\Scripts\python.exe -m spotify_cluster.web.app
```

Open <http://127.0.0.1:7860>. Stop both terminals with Ctrl+C. Ports are fixed:
inspect any occupied port's owner rather than starting duplicate servers elsewhere.
The backend URL defaults to the value above and is operator configuration only;
visitors cannot change it. HTTPX uses a 3-second connect and 15-second operation
timeout, disables environment proxies and does not follow redirects. There is no
browser-to-FastAPI request or CORS requirement.

An installed wheel can install `[api,web]` extras with pip. Configure the backend's
absolute model directory explicitly as described in [API operations](API.md).
The wheel contains web source; it does not contain data, notebook or fitted models.

Charts are Matplotlib figures delivered through `gr.Plot`. The milestone verified
that Gradio 6.31's native `BarPlot` keeps its first bars when an event changes the
data, so it is deliberately unused. The launcher also strips IPv6 brackets from
`NO_PROXY` because httpx 0.28 rejects entries such as `[::1]` before Gradio imports.

## Using the four tabs

- **Overview:** live model metrics, training-population count/share chart and table,
  model identity and measured between-cluster SS diagnostic. Values come from
  `/api/v1/model` and `/api/v1/clusters` rather than frontend constants.
- **Predict Cluster:** enter exactly nine raw F9 values, then select **Predict
  Cluster**. The result includes current cluster descriptors, population, model ID,
  centroid distances and an exact numeric table. Smaller distances mean nearer in
  fitted RobustScaler F9 space; they are not probabilities. The optional example is
  explicitly synthetic and produces no result until submitted to the actual API.
- **Cluster Explorer:** select either cluster or both, one feature, and mean or
  median. The comparison chart shows one raw-unit scale at a time. The nine-feature
  table and expandable detailed statistics include available std, Q1, Q3 and IQR.
  Optional missing statistics are blank. Population and interpretations follow the
  current artifact's profiles; cluster IDs do not have permanent musical meanings.
- **Research & Methodology:** dataset preparation, algorithms studied, the explicit
  deployment-v1 recipe, archived historical evidence and limitations.

The seven bounded descriptors are acousticness, danceability, energy, valence,
speechiness, instrumentalness and liveness, each in [0,1]. Tempo is finite,
nonnegative BPM, including zero. Loudness is finite dB without an extra bound.
Exact ordering and authoritative domain rules belong to the
[HTTP contract](API.md#endpoints-and-schemas). The UI checks basic input errors;
FastAPI remains authoritative and performs scaling and inference.

**Refresh live data** loads public aggregates on entry and on demand. They are
session-local in memory. A failed refresh clears the aggregate state; a failed
prediction clears its output. The interface can start with the API offline and
shows actionable, sanitized error messages. Start the API and refresh to recover.
Model identity and population checks prevent combining inconsistent snapshots.
The client does not retry predictions or repeatedly fetch metadata during them.

## Scientific boundaries

Clusters describe acoustic similarity, not verified genres or mood labels. The
instrumentalness contribution measures internal training separation, not accuracy.
Historical FULL/Holdout evidence remains archived; it is not a new deployment-v1
evaluation. Historical final-estimator equivalence is **NOT VERIFIED** and the
Holdout is never reopened. No MP3, Spotify URL or recommendation functionality exists.

No verified, approved per-track PCA/t-SNE export is available to this frontend.
Only API aggregates are charted. Cluster means and centroid distances are never
misrepresented as projection coordinates. See the [notebook audit](NOTEBOOK_AUDIT.md).

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_web_client.py tests/test_web_components.py tests/test_web_charts.py tests/test_web_app.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q tests/test_api_real_model.py --run-real-api
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m build
.\.venv\Scripts\python.exe plans/20261112-gradio-web/verify-http.py
```

Normal tests use labelled software doubles and need no private artifacts. The last
command requires the existing trusted deployment bundle and private verification
sample, starts owned servers on 8000/7860, checks real HTTP predictions and errors,
and shuts down both in `finally`. It records no raw sample features and performs no
training. `--browser` additionally requires the developer-only `playwright` package
(`python -m pip install playwright`) and installed Chrome; it captures all four
tabs at 1440×900, 768×1024 and 375×812. Browser tooling is not an application runtime
dependency. Evidence and presentation limitations are in the
[milestone verification report](../plans/20261112-gradio-web/reports/verification.md).

## Local privacy and future hosting

The entry point binds loopback, disables public sharing, automatic browser launch,
telemetry, run history, monitoring and MCP, and exposes no file input/output.
There are no allowed file directories; the current working tree is explicitly
blocked in Gradio file serving. Input examples are not cached and prediction inputs
are not written to disk. Gradio event APIs remain local HTTP endpoints, not an
authentication boundary. Do not configure broad file allowances.
The entry point rejects `GRADIO_ALLOWED_PATHS` when set: Gradio 6 otherwise uses
that environment variable even when its `allowed_paths` argument is an empty list.

Public hosting requires a separate authorized milestone: TLS and access control,
request/rate limits, dependency/security review, logging/privacy policy, trusted
artifact provisioning, file-serving review and process supervision. Binding the
current app publicly or enabling a sharing tunnel is not a supported deployment.
