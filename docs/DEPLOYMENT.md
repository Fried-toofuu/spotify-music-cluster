# Deployment and operations

The application remains one Gradio frontend calling one FastAPI backend. The
container image contains only source, the Python runtime and the prebuilt
browser assets. Dataset, notebook, model bundle and visualization/research
artifacts are operator-provided read-only mounts and are never baked into the
image.

## Prerequisites

- The authorized dataset and trusted `artifacts/deployment-v1` model bundle.
- Artifacts prepared on the operator's machine:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_visualization.py `
  --dataset dataset.csv --model-dir artifacts/deployment-v1 `
  --output artifacts/visualization-public-v1 --mode aggregate
.\.venv\Scripts\python.exe scripts/prepare_research.py `
  --dataset dataset.csv --model-dir artifacts/deployment-v1 `
  --output artifacts/research-v1
```

For a private/local deployment the operator may use the points artifact
(`visualization-v1`) and `SPOTIFY_VISUALIZATION_DIR` accordingly. The public
compose configuration intentionally mounts **only the aggregate** artifact:
per-track coordinates are not distributed without separate approval.

## Container configuration

- Base: `python:3.12.10-slim-bookworm` (the recorded model environment uses
  Python 3.12.10; do not change the patch version without regenerating the
  bundle).
- Exact runtime pins: `constraints.txt`, generated from the tested environment.
- Non-root UID 10001, read-only root filesystem, `no-new-privileges`, all Linux
  capabilities dropped, `/tmp` tmpfs.
- API and web are separate compose services; the API is not published to the
  host. Only the web port is published, bound to `127.0.0.1` by default;
  terminate TLS and apply access controls at a reverse proxy. The API sets
  `SPOTIFY_PUBLIC_MODE=1`, which refuses a per-track visualization artifact.
- Gradio's `/gradio_api/upload` route is blocked at the proxy example; the app
  has no file input and `max_file_size=1`, but edge blocking removes the unused
  upload surface.
- Health: the API readiness endpoint is `/api/v1/health`; the web healthcheck
  requests `/`. The web service waits for the API health before starting.
- One API worker: the trusted model is loaded once per worker in the FastAPI
  lifespan; multiple workers would multiply memory and model loads.

```bash
docker compose build
docker compose up -d
# local check
curl http://127.0.0.1:7860/
```

The image sets `SPOTIFY_PUBLIC_MODE=1` in compose and mounts only the aggregate
visualization. The image contains the built `constellation.js` and its
third-party license notice. The Plotly.js browser asset is served from the installed `plotly`
package; both are pinned by `constraints.txt`.

**Verification status:** the Docker CLI is not installed in the development
environment used for this implementation, so the container build and compose
startup were not executed. The configuration is prepared and syntax-reviewed;
actual publication remains blocked (below).

## Dependency audit

`pip-audit --local` on the tested environment reports Pillow 12.3.0 advisories
fixed in 13.0.0. Gradio 6.31.0 requires `pillow<13.0`; this application has no
image/file input and does not invoke Pillow, so those advisories are not
reachable through the application's surface. Track a Gradio release that permits
Pillow 13; do not force an unsupported upgrade. Other reported packages were
clean in the tested environment. The local project package is not on PyPI and is
therefore skipped by pip-audit.

## Public exposure and access control

- The web app binds `127.0.0.1` by default. In the container,
  `SPOTIFY_WEB_HOST=0.0.0.0` is explicit. Binding publicly without TLS/access
  control is not a supported local mode.
- Use `deploy/nginx.conf.example` as a starting point for TLS termination,
  WebSocket/SSE proxying, request-size limits and a prediction-submission rate
  limit. Tune the Gradio queue route names for the installed Gradio version and
  verify with a load test.
- The app has no user accounts, administration, training, model export, file
  upload or arbitrary-filesystem endpoint. If the deployment must be private,
  add authentication at the proxy; the application itself remains a local-first
  service.
- Gradio file serving is restricted to the reviewed browser-asset directory in
  the temporary filesystem; the working tree is blocked. Do not add broad
  `allowed_paths` or `GRADIO_ALLOWED_PATHS`.
- Logs: Uvicorn access logs record paths/status, not request bodies. The API
  intentionally does not log feature vectors. Do not add body logging.
- Request/response sizes are bounded; predictions accept 1–100 records in the
  batch contract and the UI submits one. The proxy should enforce body-size and
  rate limits.

## Model and artifact replacement

1. Prepare a new versioned model directory with `scripts/export_model.py` under
   separate authorization; never overwrite the existing bundle.
2. Regenerate visualization and research artifacts against the new bundle; their
   loader checks model ID, dataset SHA-256 and prepared fingerprint.
3. Mount the new directories and restart the API. The API reports visualization
   unavailable rather than serving mismatched data; the frontend clears stale
   visualization/research state when identities disagree.
4. Roll back by restoring the previous mount paths and restarting the API. Keep
   the previous bundle and artifact versions available read-only.
5. The historical final estimator remains gated and is not reconstructed by any
   deployment operation.

## Hugging Face Spaces (free public demo)

A free Docker Space can run the same FastAPI + Gradio pair for a public demo.
The model bundle and private verification sample are uploaded to a **private**
Hugging Face Dataset; the public Space downloads them at startup using an
`HF_TOKEN` Space secret. The default Space uses the aggregate artifact only and
sets `SPOTIFY_PUBLIC_MODE=1`; no per-track coordinates are served. A points-mode
deployment requires explicit redistribution approval and is not the default.

```powershell
# after: .\.venv\Scripts\python.exe -c "from huggingface_hub import login; login()"
.\.venv\Scripts\python.exe deploy/huggingface/deploy.py --visualization-mode aggregate
```

The script creates the private dataset, the public Space, the Space secret and
variables, and waits for the build. Free Spaces cold-start after inactivity and
have no application-level authentication or rate limiting; treat this as a
demo, not a production deployment.

## Public deployment status

**BLOCKED.** No hosting credentials, domain/TLS authority, paid infrastructure
authorization or per-track redistribution approval was available for this
implementation. No public URL is claimed. The local application and the
aggregate-mode deployment configuration are complete; actual publication
requires the separate authority boundaries to be satisfied.
