# Spotify Music Clustering foundation

A new standalone Python package for acoustic track clustering, derived solely
from the supplied final research notebook. A local FastAPI backend serves the
verified deployment model; a four-tab Gradio app calls it through HTTP. No connection to the abandoned
repository exists.

The explicitly authorized `deployment-v1` recipe trains a new
F9/RobustScaler/K-Means/K2 model on all 89741 canonical tracks. Its profile ID is
`spotify-f9-robust-kmeans-k2-v1`. Historical final-estimator equivalence remains
**NOT VERIFIED**: the notebook does not fully document that estimator's optimizer
settings. See the [notebook audit](docs/NOTEBOOK_AUDIT.md) for the distinction.

## Environment and checks

Use Python 3.12, venv and pip. Dependency declarations are in
[pyproject.toml](pyproject.toml); they intentionally preserve research Pandas and
scikit-learn versions. The stored notebook output reports Python 3.13.18 and
NumPy 2.4.6; this project targets Python 3.12 and NumPy 2.2.6. Exact historical
equivalence remains unverified.

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade "pip>=26.2.2"
.\.venv\Scripts\python.exe -m pip install -e ".[api,web,dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m build
.\.venv\Scripts\python.exe scripts/export_model.py --dataset dataset.csv --output artifacts/deployment-v1 --profile deployment-v1
```

On POSIX use `python3.12` and `.venv/bin/python` in the equivalent commands.
Export requires a new output directory. To repeat training, choose a distinct
versioned output path; existing artifacts are never overwritten. Omitted profile
selection retains the gated `historical-final-refit` route. The approved deployment
profile does not establish historical equivalence.

The default tests need neither CSV nor model artifacts. With the private CSV and
`artifacts/deployment-v1` available, run the real-model checks and one sequential
temporary reconstruction explicitly:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --run-real-model
```

[Model serving](docs/MODEL_SERVING.md) shows real inference and profile inspection.
[Local API](docs/API.md) owns backend startup, endpoints and API-only real-model
verification (`--run-real-api`, without reconstruction). No refit is needed to
serve the existing bundle.

[Local web application](docs/WEB.md) covers the Gradio dashboard, numerical F9
prediction form, Cluster Explorer and research presentation. Start FastAPI on
loopback port 8000, then run `.\.venv\Scripts\python.exe -m spotify_cluster.web.app`
and open <http://127.0.0.1:7860>. Configure the backend through
`SPOTIFY_API_BASE_URL` (default `http://127.0.0.1:8000`). No public sharing or remote
deployment is enabled.

## Inputs and scientific boundaries

Only the Maharshi Pandya Spotify Tracks Dataset snapshot declared in
[config.py](src/spotify_cluster/config.py) is authorized. The local `dataset.csv`
is ignored by Git. There is no automatic network acquisition or alternative data.
Synthetic test fixtures are software checks, never experimental evidence.

The original `Spotify_Music_Clustering_Final.ipynb` remains at the project root,
unchanged and ignored: its configuration contains a private transport URL and
stored outputs have not been approved for redistribution. `notebooks/` is reserved
for a separately reviewed public copy; no such copy is made here.

F9 excludes genre and text metadata. Robust geometry historically emphasized
instrumentalness. Clusters are not ground-truth genres, distances are not
probabilities, and a refit on all unique tracks has no fresh independent Holdout
score. The historical Holdout remains closed.

## Navigation

- [Architecture](docs/ARCHITECTURE.md): package boundaries and HTTP web integration.
- [Local web application](docs/WEB.md): installation, tabs, startup and browser checks.
- [Model serving](docs/MODEL_SERVING.md): trusted artifacts and inference usage.
- [Local REST API](docs/API.md): installation, startup, schemas and HTTP verification.
- [Backend verification](plans/20261112-fastapi-backend/reports/verification.md):
  executed API, packaging and artifact-preservation evidence.
- [Notebook audit](docs/NOTEBOOK_AUDIT.md): extraction evidence and unresolved settings.
- [Deployment verification](plans/20261112-deployment-model/reports/verification.md):
  actual model identity, profiles and executed acceptance checks.
- [Initial foundation report](plans/20261112-spotify-foundation/reports/verification.md):
  preserved historical delivery record from before deployment authorization.
