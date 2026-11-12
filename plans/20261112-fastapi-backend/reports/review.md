# Backend code and security review

Scope: API modules, inference metadata/profile accessors, package extras, API tests,
verification scripts and impacted documentation. Reviewed inline against the
requested contract, API/base review checklists and STRIDE/OWASP trust boundaries.
No independent reviewer agent or remote repository was used. The repository has
no HEAD commit; the existing foundation and all additions remain untracked, so
review used the actual files rather than an unavailable committed diff.

Assets: trusted local executable joblib state, private verification inputs, raw
CSV and notebook. HTTP callers may supply acoustic numbers only. Operators own
model-directory configuration; checksums do not authenticate that operator trust.

Confirmed findings resolved:

- The actual immutable historical status differs from the requested HTTP spelling.
  Map it only at the adapter; test both the expected origin and HTTP status.
- Default FastAPI validation errors can echo input/context and cannot safely emit
  nonfinite inputs as JSON. Strip those fields; tests cover NaN/infinities and
  private marker values with 422 responses.
- Single/batch native arithmetic may differ in the last floating-point bit.
  Use the existing stored-sample tolerance (rtol 1e-9, atol 1e-7), retaining exact
  labels, metadata and profile assertions. No model arithmetic changed.
- Windows smoke harness initially started a stdin-reader thread before NumPy
  native import. Stack tracing showed import blocked until stdin closed; loading
  the application before starting that helper eliminated the wait. Actual server
  startup then completed in about one second and shutdown exited 0.
- Smoke cleanup now tolerates a broken stdin pipe when startup exits early.

Reviewed boundaries:

- No fit, CSV load, notebook execution or new scientific algorithm in the API.
  Real tests and installed-wheel checks actively block fitting and dataset reads.
- One lifecycle service; explicit state dependency, 503 for missing state, no
  import-time load, validated public response views before readiness.
- F9 domains reuse input_matrix; strict numeric Pydantic input and 1–100 batch
  limits prevent coercion and invalid batch inference. One batch service call.
- Metadata uses a field allowlist; profiles belong to the checked identity.
  Responses contain aggregate statistics and requested predictions only.
- No upload, client path, model URL, remote call, unrestricted CORS, raw-data,
  verification-sample or HTTP training surface. Local loopback serving is intentional.
- Runtime 500 responses contain no exception details; logs record exception type
  without raw feature payloads. Startup diagnostics remain operator-only.
- Local artifacts/dataset/notebook stay Git-ignored and excluded from wheel/sdist.
- API extra leaves numerical pins unchanged. Pip audit found no known dependency
  vulnerabilities; the local unpublished package cannot be audited on PyPI.

No unresolved blocking correctness/security finding was identified in this scope.
Authentication, TLS, rate limits and body-size gateway controls remain future
public-deployment decisions, not missing local-MVP requirements. Starlette emits
a nonblocking deprecation warning for HTTPX TestClient; no warning is suppressed.
