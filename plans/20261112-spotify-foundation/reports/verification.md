# Delivery verification

The safe foundation is implemented in `D:\spotify_music_cluster`. The full
milestone remains **BLOCKED** because the supplied notebook does not establish
the archived final-refit optimizer settings. No production model was fitted or
exported; no Holdout evaluation was performed.

## A. Project and environment

Distribution: `spotify-music-clustering-web` 0.1.0; import package:
`spotify_cluster`. Python 3.12.10 in a conventional `.venv`; fresh wheel
installation verified separately in `.venv-wheel`. No remote repository was
configured and no commit/push was made.

Scientific dependencies: NumPy 2.2.6, Pandas 2.2.3, SciPy 1.15.3,
scikit-learn 1.6.1, joblib 1.5.1, threadpoolctl 3.6.0. Development checks use
pytest 9.0.3, Ruff 0.14.4 and build 1.3.0. Pip was updated to 26.3 after the
dependency audit. Exact runtime/tool versions, archive inventories, sizes and
checksums are in [evidence.json](evidence.json); all installed audited package
versions are in [dependency-audit.json](dependency-audit.json).

Meaningful checkout files (generated caches, environment internals and egg-info
omitted; logs are listed in the evidence directory):

```text
D:\spotify_music_cluster\
  .gitignore
  .python-version
  AGENTS.md
  MANIFEST.in
  README.md
  pyproject.toml
  dataset.csv                              # original, ignored
  Spotify_Music_Clustering_Final.ipynb       # original, ignored, unchanged
  artifacts/.gitkeep                       # no final_model directory
  data/raw/.gitkeep
  notebooks/.gitkeep                       # no public notebook copy
  src/spotify_cluster/
    __init__.py
    config.py
    data.py
    training.py
    model_store.py
    inference.py
  scripts/export_model.py
  tests/
    conftest.py
    test_cli.py
    test_data.py
    test_training.py
    test_model_store.py
    test_inference.py
  docs/
    ARCHITECTURE.md
    MODEL_SERVING.md
    NOTEBOOK_AUDIT.md
  plans/20261112-spotify-foundation/
    plan.md
    phase-01-foundation.md
    verify-delivery.py
    reports/                              # this report, JSON evidence, check logs
  plans/journals/                          # local session record
  dist/
    spotify_music_clustering_web-0.1.0-py3-none-any.whl
    spotify_music_clustering_web-0.1.0.tar.gz
```

## B. Notebook audit

All 117 cell sources were read, without execution. The original notebook remains
at its original location; SHA-256:
`76a31ac55e385238761d7decbc5117cede6f1ad8a2c9285504e80c4a2526b178`.
It is ignored because it contains private transport configuration and stored
outputs have not been approved for public distribution.

The [notebook audit](../../../docs/NOTEBOOK_AUDIT.md) identifies source cells,
deduplication, scaling, candidate comparisons, versions and limitations.
Canonical preparation follows cells 21-25, including tolerance-based duplicate
vector checks and stable ID/genre/source-row representative selection. Genre
associations remain in a separate bridge.

Cell 82 specifies development F9 K=2, seed 42 and n_init 10 QUICK / 20 FULL.
Cell 55's max_iter=400 belongs to an F5 baseline. Cells 109-110 identify the
historical representation and separate final refit but do not specify that
refit's optimizer settings. These settings cannot establish final n_init,
max_iter, init, tol or algorithm. The CLI fails closed rather than guessing.

Differences: the requested Python 3.12 target and NumPy 2.2.6 differ from stored
cell 5 output (Python 3.13.18, NumPy 2.4.6); Pandas and scikit-learn versions are
preserved. Boolean rejection, explicit finite-state checks and one-thread
software fitting are safeguards, not extra modeling features.

## C. Dataset and model export

Actual authorized local CSV SHA-256:
`b202fa49909b2d5cef71a04b1d21243cfeb36414535f2ca9272aa646721177bd`.
Verified 114000 records, 21 columns, 114 genres and 89741 normalized unique
tracks. Canonical matrix: `(89741, 9)`, finite and domain-valid. No rows were
silently dropped and no values were imputed/clipped.

Ordered schema: acousticness, danceability, energy, valence, tempo, loudness,
speechiness, instrumentalness, liveness. Genre/text metadata is excluded.

Preparation identity: `notebook-track-f9-v1`; fingerprint:
`35cd173326261791b7c48689176af25a92604d2d543824269059d0816237f407`.

Selected representation: RobustScaler, K-Means K=2, no modeling PCA. Extracted
scaler settings: centering/scaling enabled, quantiles [25,75], unit_variance=False,
copy=True. They come from the executable RobustScaler() demonstration, not an
independently recovered archived final scaler object.

The real CLI verified this snapshot and exited **2**, with no output directory:
[export-cli.txt](export-cli.txt). Production model ID, training cluster counts,
shares, bundle sizes/checksums and profiles are **not available**, because no
production fit/export was authorized under ambiguous settings. Test models
exist only in temporary directories and carry `software-test-only` status.
They are not Spotify research artifacts.

Built wheel/source archive sizes, SHA-256 values and full file inventories are
recorded in [evidence.json](evidence.json). Inspection excluded CSVs, notebooks,
joblib bundles and environment files from both archives. The wheel contains only
package modules and distribution metadata; the source archive also includes
CLI, docs and complete test fixtures.

## D. Inference verification

On synthetic software fixtures only, tests independently verified median/IQR
scaling (including zero-IQR handling), Euclidean centroid distances, nearest
centroid predictions, SSE, repeated-fit state and label-permutation matching.
Save/load predictions matched. A separate Python process matched serialized
predictions. A clean installed-wheel process verified single and batch inference
outside the source import path. See [wheel-clean-process.txt](wheel-clean-process.txt).

Tests reject missing/extra features, booleans, text, NaN/Infinity, out-of-domain
values, invalid tempo and dimensions. They verify correct profile association,
defensive profile copying, checksum/environment rejection and no fitting or CSV
access during prediction. No notebook is executed or required by inference.

No corresponding production-model inference result is claimed while export is
blocked. Historical centroid/prediction equivalence is **NOT VERIFIED**.

## E. Quality results

| Check | Status | Evidence / scope |
|---|---|---|
| Dataset provenance | PASS | Exact local bytes and required snapshot contract |
| Data preparation | PASS | Actual canonical matrix (89741, 9), plus focused tests |
| Exact feature schema | PASS | F9 order and genre exclusion |
| Model export | BLOCKED | Missing final-refit optimizer evidence |
| Bundle integrity | BLOCKED | Production absent; software-fixture checks PASS |
| Independent prediction verification | BLOCKED | Production absent; fixture arithmetic PASS |
| Historical model equivalence | NOT VERIFIED | No original final estimator or matched predictions |
| Unit tests | PASS | 56 passed; no warnings on final run |
| Ruff lint | PASS | `python -m ruff check .` |
| Ruff format | PASS | `python -m ruff format --check .` |
| Package build | PASS | `python -m build`; wheel and source inspected |
| Clean-process inference | BLOCKED | Production absent; fresh-wheel fixture inference PASS |
| Security review | PARTIAL | Local source/trust boundaries reviewed; dependency audit clean; publication/licensing review outstanding |

Exact outputs: [pytest.txt](pytest.txt), [ruff-check.txt](ruff-check.txt),
[ruff-format.txt](ruff-format.txt), [build.txt](build.txt),
[wheel-install.txt](wheel-install.txt), [wheel-pip-check.txt](wheel-pip-check.txt).
The verification runner is [verify-delivery.py](../verify-delivery.py).

Security review: joblib loading is a trusted-local boundary, not an upload API.
Checksums detect accidental damage but do not authenticate a malicious bundle.
Static inspection found no network acquisition, shell execution, credentials,
web endpoints or runtime fitting paths in application code. Git ignores both
original inputs and generated models. No files were published.

The initial dependency audit flagged pip and pytest. Pip was upgraded to 26.3
and pytest pinned to 9.0.3; the repeat audit reports no known vulnerabilities in
auditable packages. The local unpublished distribution is skipped by the advisory
database and reviewed as source instead. Sources:
[pytest release notes](https://github.com/pytest-dev/pytest/releases/tag/9.0.3),
[pip changelog](https://pip.pypa.io/en/stable/news/).

## F. Remaining blockers and acceptance gaps

1. Supply authoritative final-refit optimizer settings or verified final-estimator
   evidence. Then update the gate and metadata provenance, fit all 89741 tracks,
   export, and rerun numerical/reload/reconstruction checks on that actual model.
2. Exact historical equality remains unverified without the original final
   centroids or matched reference predictions; aggregate archived scores cannot
   establish it. No Holdout re-evaluation is needed or permitted.
3. Python/NumPy differ from stored research execution; do not claim historical
   numerical equivalence. Actual environment is recorded.
4. Dataset/model redistribution rights and notebook-output publication have not
   been reviewed. Keep them local/ignored until reviewed and approved.

There is no missing CSV and no failing required software check. FastAPI and
Gradio are deliberately absent. The reusable interface is ready for later web
integration once the scientific model artifact is available; the full original
milestone acceptance criteria are not yet satisfied.
