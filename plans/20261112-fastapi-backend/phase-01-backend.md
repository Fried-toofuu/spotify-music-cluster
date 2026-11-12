# Backend execution

## Evidence and decisions

The existing InferenceService delegates to load_bundle, which checks checksums,
environment, fitted dimensions/state, F9 order, profile identity and stored sample
arithmetic. Reuse it; expose defensive metadata/profile accessors. Its predictions
already contain Euclidean centroid distances and full aggregate profiles.

The immutable artifact uses `NOT VERIFIED`, whereas the requested HTTP spelling
is `not_verified`. Normalize only in the HTTP schema adapter. No artifact edit.
The existing `--run-real-model` option includes a real reconstruction: do not run
it during this integration-only milestone. Add `--run-real-api` separately.

## Files and steps

- pyproject.toml: optional API dependencies and development HTTPX.
- inference.py: defensive read-only metadata/profile access only.
- api/: explicit schemas, app factory/lifespan, dependency and routes.
- tests/test_api*: software doubles, real loader failure checks, real API opt-in.
- plans/20261112-fastapi-backend/: sanitized reproducible verification scripts/logs.
- docs/API.md, README.md, docs/ARCHITECTURE.md: owning operational guidance.

Use request model validation through existing input_matrix rather than a second
audio-domain policy. Future Gradio is an HTTP consumer of these same schemas;
no frontend scaffolding is required. Tests verify that stable contract now.

## Verification

Start with API tests, then full default pytest; opt in only to real API tests.
Guard fitting and CSV/notebook reads for actual model serving. Start a tracked
Uvicorn subprocess on 127.0.0.1:8000 after checking port ownership; terminate in
finally. Compare private saved sample outputs without retaining input rows.
Run Ruff, build, clean-wheel imports/CLI/API outside checkout, dependency audit,
protected-hash comparison and docs link checks. Record actual results.

## Risk and rollback

Only trusted operator-selected local bundles may be deserialized. Checksum
validation is not authentication. Fail startup for invalid artifacts; return 503
when runtime state is absent. Strip validation input/context and sanitize 500s.
Rollback removes the API additions and dependency extra; artifacts are untouched.
