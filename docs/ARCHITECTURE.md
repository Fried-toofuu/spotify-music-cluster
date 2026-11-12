# Architecture

The application imports Python modules; it never executes notebook cells. The
original notebook is methodological authority, not a runtime dependency.

- [config.py](../src/spotify_cluster/config.py) owns research constants, the
  immutable approved deployment-v1 recipe and the historical-only gate.
- [data.py](../src/spotify_cluster/data.py) owns snapshot verification, canonical
  tracks and the separate genre bridge. Metadata never enters the F9 matrix.
- [training.py](../src/spotify_cluster/training.py) owns offline fitting, raw-unit
  profiles and independent numerical checks. Explicit parameters make absent
  scientific evidence visible instead of masking it with library defaults.
- [model_store.py](../src/spotify_cluster/model_store.py) owns bundle identity,
  checksums, fitted-state checks and environment compatibility.
- [verification.py](../src/spotify_cluster/verification.py) owns deterministic
  private sample selection and independent centroid arithmetic.
- [inference.py](../src/spotify_cluster/inference.py) owns strict input validation
  and reusable single/batch prediction, with defensive verified metadata/profile access.
- [api/app.py](../src/spotify_cluster/api/app.py) owns the optional FastAPI factory,
  trusted local directory resolution, lifespan state and sanitized error boundaries.
- [api/schemas.py](../src/spotify_cluster/api/schemas.py) owns HTTP contracts;
  [routes.py](../src/spotify_cluster/api/routes.py) adapts existing service outputs.
- [export_model.py](../scripts/export_model.py) is the offline orchestration boundary.
- [web/app.py](../src/spotify_cluster/web/app.py) owns the optional Gradio Blocks
  factory, four tabs, local launch policy and theme. Imports start no server.
- [web/api_client.py](../src/spotify_cluster/web/api_client.py) owns configurable
  HTTPX calls, timeouts, consumed-response checks and sanitized frontend errors.
- [web/components.py](../src/spotify_cluster/web/components.py) owns presentation,
  basic form validation and session aggregate handlers;
  [web/charts.py](../src/spotify_cluster/web/charts.py) builds aggregate tables and
  Matplotlib figures. Figures render through `gr.Plot` because Gradio 6.31's native
  `BarPlot` does not apply data updates after its first render.

Deployment-v1 trains the user-approved recipe on the full verified canonical
population. Historical-final-refit remains unavailable without its own evidence.
These are separate identities; no deployment artifact inherits a historical score.

A single fitted Pipeline keeps scaler and centroids paired. PCA is excluded
from modeling; notebook projection figures are visualization only. Profiles use
actual model assignments and raw feature units, with arbitrary numeric labels.

FastAPI initialization creates one InferenceService per lifespan and reuses it;
requests obtain it from application state. Model loading never happens at import
time. Request domain validation calls the existing inference validator. The loader
checks actual model/profile identity and the adapter selects safe public fields.
The HTTP spelling `not_verified` preserves the unchanged artifact's `NOT VERIFIED`
meaning. See [API operations and schemas](API.md).

The browser calls Gradio, which calls FastAPI over HTTP; see [web operations](WEB.md).
Gradio holds public aggregates per session, verifies combined model identities and
uses the prediction's returned current profile. It never imports model-serving
modules. No dataset/model loading or training occurs during UI construction.
Neither request handling nor the UI may
load the CSV, fit estimators, revisit model selection or evaluate Holdout.
There are no databases, queues, deployment services or HTTP retraining paths.
