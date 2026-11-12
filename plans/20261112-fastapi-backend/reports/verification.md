# FastAPI backend verification — 2026-11-12

Milestone delivered locally. All required gates below passed against the existing
deployment artifact. No model refit/reconstruction, notebook execution, Holdout
evaluation, Gradio implementation, remote deployment or publication occurred.

## A. Implementation

Created:

- `src/spotify_cluster/api/{__init__,app,schemas,dependencies,routes}.py`:
  application factory, lifespan-owned service, strict HTTP schemas, state dependency
  and versioned routes. Imports create an app but never deserialize a bundle.
- `tests/api_fixtures.py`: labelled deterministic software-only inference double.
- `tests/test_api_{health,predict,validation,real_model}.py`: lifecycle, response,
  ordering, strict validation, privacy, failure and actual-model checks.
- `docs/API.md`: installation, configuration, requests, semantics, trust and next
  frontend integration route.
- This plan's verification scripts and reports: reproducible local HTTP and
  installed-wheel checks; no private input rows retained.

Modified:

- `src/spotify_cluster/inference.py`: defensive `metadata` and `profiles`
  properties. Existing prediction behavior and artifact loading are unchanged.
- `pyproject.toml`: optional `api` extra for FastAPI, Pydantic and Uvicorn; HTTPX
  in `dev`; description updated. All scientific pins and build settings retained.
- `tests/conftest.py`: software API fixtures and separate `--run-real-api` switch.
- `README.md`, `docs/ARCHITECTURE.md`: backend ownership and operational navigation.
- `AGENTS.md`: replace the superseded no-web-framework boundary with the explicitly
  authorized local FastAPI scope and future-Gradio boundary.

Architecture: startup resolves an absolute operator path (or checkout-relative
default), initializes the existing InferenceService once, and validates deployment
provenance, F9 order and public metadata/profile views before readiness. Its loader
checks checksums, exact scientific environment, fitted state, paired Pipeline,
model/profile identity and stored sample arithmetic. Requests use that same state.
Shutdown clears it. Invalid artifacts fail startup; no fake fallback exists.

| Endpoint | Contract |
|---|---|
| `GET /api/v1/health` | Service/version, ready state and model-loaded flag |
| `GET /api/v1/model` | Safe verified metadata subset; HTTP historical status `not_verified` |
| `GET /api/v1/clusters` | Current identity, full aggregate profiles and measured separation interpretation |
| `POST /api/v1/predict` | One strict raw F9 record; actual label, centroid distances and matching profile |
| `POST /api/v1/predict/batch` | Object with 1–100 tracks; one existing vectorized batch call, ordered predictions |

Full schemas/examples and error semantics: [API guide](../../../docs/API.md).
Request domains call existing input_matrix; no competing bounds or input clipping.
422 responses strip input/context; runtime absence returns 503; unexpected failures
return sanitized 500. No unrestricted CORS or upload/data/sample/training route.

## B. Real model integration

- Directory: `D:\spotify_music_cluster\artifacts\deployment-v1`.
- Model ID: `spotify-f9-robust-k2-0828777db6924fe39e47335c19cc9363`.
- Model SHA-256, before **and** after:
  `9c23058262845f3efa2ac2acaf277a9e66ea90066561c893ab6844b586946435`.
- Origin: `new_deployment_refit`; immutable historical status: `NOT VERIFIED`.
  HTTP maps that spelling to `not_verified` without changing the artifact.
- Actual profile training counts: 72211 and 17530; stored instrumentalness share
  of between-cluster SS: 0.9730218110901931 in fitted RobustScaler space.
- TestClient checked all 32 stored private verification records through both single
  and batch endpoints, with estimator fitting and dataset/notebook reads blocked.
  Labels match exactly, distances match with rtol=1e-9, atol=1e-7, and profiles match
  the verified artifact. No row-level input is reproduced in this report.
- Real Uvicorn HTTP smoke checked one single and all 32 batch records: 25 cluster-0
  and 7 cluster-1 assignments. First single output: cluster 0, Euclidean distances
  `[2.7783335136536538, 8.888969568042624]`. Batch maximum absolute distance error
  against the saved expected outputs was 0.0. These are training-consistency
  observations, not independent evaluation or confidence estimates.
- Final smoke startup was approximately 1.03 seconds; clean server exit code 0,
  port 8000 released. See [HTTP evidence](http-smoke.json) and [server log](http-server.txt).

All five artifact files and the notebook match their complete before/after hashes:
[before](protected-before.json), [after](protected-after.json).
Notebook SHA-256 remains
`76a31ac55e385238761d7decbc5117cede6f1ad8a2c9285504e80c4a2526b178`.

## C. Executed gates

| Gate | Status | Evidence |
|---|---|---|
| FastAPI startup | PASS | Real loader, HTTP startup and installed-wheel startup |
| Health endpoint | PASS | HTTP 200; dependency absence tested as 503 |
| Model endpoint | PASS | HTTP 200; safe fields, ordered F9, origin and historical status |
| Clusters endpoint | PASS | HTTP 200; exact loaded identity and aggregates |
| Single prediction | PASS | HTTP 200; all 32 TestClient singles checked |
| Batch prediction | PASS | HTTP 200; actual sample, order and software boundary sizes |
| Input validation | PASS | HTTP 422; strict types, domains, malformed JSON, batch bounds |
| Lifespan loading | PASS | Once per lifespan, reuse, shutdown cleanup and startup failure tests |
| Real-model API integration | PASS | [2 tests passed](pytest-real-api.txt), including private API integration and software accessor test |
| OpenAPI/Swagger | PASS | HTTP 200 for `/openapi.json` and `/docs` |
| Local HTTP smoke | PASS | [All required statuses and clean shutdown](http-smoke.json) |
| Full pytest | PASS | [121 passed, 5 skipped](pytest.txt); no existing software test removed |
| Ruff | PASS | [Lint](ruff-check.txt) and [format check](ruff-format.txt) |
| Package build | PASS | [Wheel and sdist](build.txt); API modules included, private files excluded |
| Clean-wheel imports | PASS | [Isolated wheel API](wheel-api.txt), actual inference outside checkout; [CLI help](wheel-cli.txt) |
| Model artifact unchanged | PASS | All five before/after hashes identical |
| Notebook unchanged | PASS | Before/after hash identical |

Additional checks: development and wheel `pip check` pass. Dependency audit reports
zero known vulnerabilities across the auditable installed dependencies; the local
unpublished project package is skipped by PyPI lookup. See
[audit JSON](dependency-audit.json). Documentation links resolve, and Git ignore
checks confirmed private artifacts, sample, CSV and notebook stay ignored.

The fresh `.venv-api-wheel` was created without system site packages, installed from
the built wheel with API dependencies and HTTPX, and executed with `-I` from a
temporary directory outside the checkout. It used site-packages, required explicit
model configuration and served all 32 stored records while training/data reads were
blocked. Wheel SHA-256:
`0f7cfb557ad502ac15ba53b1e1ed0f9b5dd49bd0ef72869ae0dbc22e1aab95f0`.

Tested tool versions and machine evidence: [evidence.json](evidence.json).
Focused code/security review: [review.md](review.md). Version-sensitive guidance
was checked against official [FastAPI lifespan documentation](https://fastapi.tiangolo.com/advanced/events/)
and [lifespan testing documentation](https://fastapi.tiangolo.com/advanced/testing-events/).

## D. Remaining limits and recorded mismatches

- Default pytest intentionally skips one private API test and four older private
  model tests. The API test was separately enabled and passed. The older option
  includes reconstruction, so it was deliberately not enabled in this integration
  milestone. No required API gate remains unverified.
- Starlette 1.10.0 emits a nonblocking deprecation warning for HTTPX-based
  TestClient. Tests pass; the warning is neither suppressed nor hidden.
- The initial smoke harness timed out before serving because a Windows stdin
  helper blocked NumPy native import. A stack trace established the blocked
  import; importing the application before starting that helper fixed it.
  Final smoke evidence reflects the corrected harness. No production API change
  or numerical dependency change was needed.
- Single and batch numerical distances can differ by final floating-point bits;
  exact metadata/profile/label checks and existing numerical tolerances are used.
- Checksums are not signatures. Only operator-trusted local bundles are safe.
  Public hosting would require separate access-control, TLS, request-size/rate and
  logging decisions. This work provides a loopback MVP only.
- No Gradio frontend or remote deployment exists. The API is ready for a future
  Gradio HTTP client; that UI still needs design and implementation.
- The repository already had no commits and all foundation files were untracked.
  Work remains local and uncommitted. No abandoned repository was accessed.
