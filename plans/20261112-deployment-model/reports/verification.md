# Deployment model verification

The new deployment model was trained, exported and verified on the actual local
Spotify snapshot. All requested deployment/software gates passed. Historical
identity remains **NOT VERIFIED**, as required. No Holdout evaluation, notebook
execution, remote publication or web application was performed.

## A. Changes

Added:

- `src/spotify_cluster/verification.py`: deterministic private sample and
  independent NumPy centroid checks.
- `tests/test_deployment.py`: immutable recipe, provenance, persistence and
  corruption/configuration rejection.
- `tests/test_real_model.py`: opt-in real snapshot/profile/math/inference checks
  and one sequential full-data reconstruction through the actual export CLI.
- This plan/report and the two verification runners in its parent directory.
- Five local ignored artifacts under `artifacts/deployment-v1`.

Modified:

- `config.py`: frozen deployment-v1 recipe and per-parameter provenance; kept
  `historical-final-refit` gated and preserved NOT VERIFIED semantics.
- `training.py`: actual-assignment feature contributions and explicit in-sample
  diagnostic scope. Data preparation and F9 ordering are unchanged.
- `model_store.py`: optional profile/sample support with old bundle compatibility;
  metadata/profile/sample checksums and current-sample checks during loading.
- `inference.py`: additive deployment-profile and historical-status fields.
- `scripts/export_model.py`: explicit `--profile deployment-v1`; omitted profile
  retains the historical gate. Existing directories are refused.
- `tests/conftest.py`: explicit `--run-real-model` opt-in.
- `.gitignore` and `MANIFEST.in`: exclude private verification sample JSON.
- `AGENTS.md`, README and the requested architecture, notebook-audit and serving
  docs: distinguish the approved new recipe from historical reconstruction.

Packaging and dependency declarations are preserved. There was no project
rebuild/reinitialization, abandoned-repository access, commit or push.

## B. Actual model and artifacts

| Property | Recorded value |
|---|---|
| Root | `D:\spotify_music_cluster` |
| Profile selector | `deployment-v1` |
| Deployment profile | `spotify-f9-robust-kmeans-k2-v1` |
| Model ID | `spotify-f9-robust-k2-0828777db6924fe39e47335c19cc9363` |
| Origin / reconstruction status | `new_deployment_refit` |
| Creation time (UTC) | `2026-11-12T10:03:35.096272+00:00` |
| Training population | 89741 canonical tracks, 9 F9 features |
| Raw snapshot | 114000 rows, 21 columns, 114 genres |
| Preparation identity | `notebook-track-f9-v1` |
| Modeling PCA | None |
| Fit native-thread limit | 1 |
| Historical equivalence | NOT VERIFIED |
| Holdout evaluated | false |

Dataset SHA-256:
`b202fa49909b2d5cef71a04b1d21243cfeb36414535f2ca9272aa646721177bd`.
Prepared-data fingerprint:
`35cd173326261791b7c48689176af25a92604d2d543824269059d0816237f407`.
This equals the initial milestone's verified preparation fingerprint.

Ordered F9: acousticness, danceability, energy, valence, tempo, loudness,
speechiness, instrumentalness, liveness. Genre and text metadata are excluded.

Exact scaler: RobustScaler(with_centering=True, with_scaling=True,
quantile_range=(25.0,75.0), copy=True, unit_variance=False).

Exact estimator: KMeans(n_clusters=2, init="k-means++", n_init=20,
max_iter=300, tol=1e-4, random_state=42, algorithm="lloyd", copy_x=True,
verbose=0). The fitted scaler and estimator are one Pipeline.

F9/Robust/K2/no-PCA come from the notebook's selected representation. Seed 42
and n_init=20 are adopted from its development examples. The remaining optimizer
values explicitly adopt the documented
[scikit-learn 1.6 defaults](https://scikit-learn.org/1.6/modules/generated/sklearn.cluster.KMeans.html).
This freezes a new approved deployment recipe and makes no assertion about the
undocumented historical final estimator. F5 max_iter=400 was not substituted.

Actual versions: Python 3.12.10, NumPy 2.2.6, Pandas 2.2.3, SciPy 1.15.3,
scikit-learn 1.6.1, joblib 1.5.1 and threadpoolctl 3.6.0. These are recorded
in metadata and are not asserted to be the historical research environment.

All paths below are relative to `artifacts/deployment-v1/`:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| model_bundle.joblib | 360526 | `9c23058262845f3efa2ac2acaf277a9e66ea90066561c893ab6844b586946435` |
| metadata.json | 3126 | `39e64e022708e18cc08b8b857d5653e22f8f5ec36395783f84d26e5a48c4ba17` |
| cluster_profiles.json | 5554 | `90346684cab0a7b6ee5b1b52a0f8c6d5b58f83bfa741e4b3866b17c4c57b924e` |
| verification_sample.json | 10037 | `5345b8f1b35e4f2b50bb87796e116a4a2e0fec5c0f5758a1e4f3faa7be86a4e9` |
| verification_report.json | 750 | `3874e879e973880288d8d7ef97b587bda27caa0469a09df10b807b07d277a6fd` |

The report checksums bundle, metadata, profiles and sample; metadata also carries
bundle/profile/sample hashes. The sample has 32 equally spaced canonical
positions with real raw F9 values, predictions and distances. It is private,
ignored and excluded from distributions. No row-level values are copied here.

Machine-owned inventories/checksums and full aggregate statistics:
[evidence.json](evidence.json). Files were not overwritten on export.

## C. Current cluster profiles

Labels below describe only this model's actual assignments; future model labels
can permute. Counts sum to **89741**.

| Cluster | Count | Share | Mean instrumentalness | Median instrumentalness |
|---|---:|---:|---:|---:|
| 0 | 72211 | 80.4660% | 0.019433 | 0.00000533 |
| 1 | 17530 | 19.5340% | 0.807702 | 0.858000 |

Raw-unit means:

| Feature | Cluster 0 | Cluster 1 |
|---|---:|---:|
| acousticness | 0.314100 | 0.386739 |
| danceability | 0.577752 | 0.497960 |
| energy | 0.655555 | 0.547555 |
| valence | 0.509761 | 0.303539 |
| tempo (BPM) | 122.810430 | 118.960147 |
| loudness (dB) | -7.461745 | -12.771769 |
| speechiness | 0.092673 | 0.065892 |
| instrumentalness | 0.019433 | 0.807702 |
| liveness | 0.224888 | 0.184351 |

Profiles also include all nine medians, sample standard deviations, Q1, Q3 and
IQR. Values are computed from this model's full-population assignments.

The newly measured instrumentalness share of between-cluster sum of squares is
**97.3021811%** in fitted RobustScaler space, independently checked with the
two-group mean-difference identity. This is not the archived 97.37% value.
The model is primarily an instrumentalness-based acoustic partition; cluster 1
has higher instrumentalness descriptors and lower mean valence/loudness here.
Neither label is a ground-truth genre or a verified listening persona.

## D. Executed verification

| Gate | Status | Evidence |
|---|---|---|
| Dataset integrity | PASS | Exact hash, raw schema/counts, canonical matrix (89741,9) |
| Deployment recipe validation | PASS | Frozen explicit parameters and provenance |
| Real model export | PASS | Actual CLI, five local artifacts |
| Fitted Pipeline integrity | PASS | Types, dimensions, fitted state, two populated clusters |
| Real single inference | PASS | Real sample; fresh installed-wheel process |
| Real batch inference | PASS | 32 real records and reversed-order consistency |
| Independent mathematical checks | PASS | Full-population median/IQR, scaling, nearest centroid, SSE; sample squared distances |
| Serialization round trip | PASS | Stored in-memory predictions/distances matched reloaded model |
| Clean-process model loading | PASS | Fresh process and installed-wheel process |
| Cluster-profile identity | PASS | Model ID, counts/shares and complete profiles recomputed |
| Unit and integration tests | PASS | 66 default tests passed; 4 private tests passed explicitly |
| Ruff lint and format | PASS | All checks passed; 19 files already formatted |
| Package build | PASS | Wheel/source built and inspected |
| Controlled reconstruction | PASS | One additional sequential real CLI export in temporary directory |
| Notebook preservation | PASS | Original hash unchanged |
| Local artifact privacy | PASS | Git ignores artifacts; distributions omit data/models/samples |
| Historical identity | NOT VERIFIED | Preserved boundary; no original historical estimator comparison |

Commands actually executed (using `.venv\Scripts\python.exe`):

```powershell
python scripts/export_model.py --dataset dataset.csv --output artifacts/deployment-v1 --profile deployment-v1
python -m pytest -q
python -m pytest tests/test_real_model.py -q --run-real-model
python -m ruff check .
python -m ruff format --check .
python -m build
python plans/20261112-deployment-model/verify-delivery.py
```

Exact outputs: [pytest.txt](pytest.txt) (`66 passed, 4 skipped`),
[pytest-real-model.txt](pytest-real-model.txt) (`4 passed`),
[ruff-check.txt](ruff-check.txt), [ruff-format.txt](ruff-format.txt),
[build.txt](build.txt), [wheel-install.txt](wheel-install.txt),
[wheel-pip-check.txt](wheel-pip-check.txt), and
[wheel-real-inference.txt](wheel-real-inference.txt).
Default skips intentionally isolate private data; all four were then executed.
The original 56 software tests remain functional.

The real-data tests independently verified full-population scaling and SSE
(`894373.6064971715`), sample raw values against their canonical positions,
NumPy squared distances, nearest-centroid labels and profile statistics.
SSE is an in-sample consistency diagnostic, not an independent score.

One extra export through the same approved CLI was performed sequentially in a
temporary directory. Scaler center/scale matched exactly; centroids matched
within 1e-12 tolerance after optimal label mapping; all training assignments,
cluster populations and sample predictions matched with that mapping. The
reconstruction had a separate model ID. Binary joblib equality was not required.

A new `.venv-deployment-check` received the built wheel. An isolated process
loaded a copy of only the real five-file bundle, with no CSV/notebook in its
working directory and guards that fail CSV/notebook reads, fitting and socket
connections. Single/batch predictions, distances, reversed input order, strict
validation, profile labels and model identity all passed. Import provenance
points into that environment's site-packages, not the checkout.

Both the main and installed-wheel dependency audits reported
`No known vulnerabilities found`; the unpublished local distribution is skipped
by the advisory database and reviewed as source. See
[dependency-audit.json](dependency-audit.json) and
[wheel-dependency-audit.json](wheel-dependency-audit.json).
Source review verified trusted-local deserialization, pre-load integrity/version
checks, no model upload/network acquisition and no inference fitting. The retained
simplifier session could not start its command helper, so review was completed
inline; no independent-agent review is claimed.

The wheel and source archive exclude CSV, notebook, joblib, verification sample
and environment files. Full archive inventories, sizes and checksums are in
[evidence.json](evidence.json). No remote files were published.

Original notebook SHA-256 remains:
`76a31ac55e385238761d7decbc5117cede6f1ad8a2c9285504e80c4a2526b178`.
No Holdout cohort, archived metrics or historical identity was modified.

## Remaining limitations

Historical equivalence is intentionally unverified; the deployment model has no
fresh independent Holdout score. The representation strongly emphasizes
instrumentalness, and centroid distances are not probabilities. Python/NumPy
versions differ from the notebook's stored research execution. Data/model/sample
distribution remains subject to a separate review; all remain local and ignored.

There are no remaining deployment acceptance blockers. The verified local model
and reusable inference interface are ready for subsequent FastAPI integration;
FastAPI and Gradio remain outside this milestone.
