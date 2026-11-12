# FastAPI backend integration

Outcome: serve the existing trusted deployment-v1 artifact through five versioned
REST endpoints, with strict F9 validation, one lifespan-owned inference service,
private-artifact-free software tests, real-model integration and local HTTP proof.

Constraints: preserve all model bytes, metadata, profiles, CSV and notebook.
No refit/reconstruction, Holdout access, Gradio, remote publishing, uploads,
database, queue, CORS expansion or client-selected paths. The request explicitly
authorizes FastAPI beyond the earlier milestone's no-framework boundary.

Phases (sequential):

1. Audit and record protected hashes; implement lifecycle, schemas and routes.
2. Test software contracts and opt-in actual-model API behavior without refitting.
3. Run local HTTP smoke, full default suite, Ruff, build and clean-wheel checks.
4. Review security/correctness, reconcile docs and record verification evidence.

Acceptance: all five endpoints, Swagger/OpenAPI, strict numeric and domain
validation, vectorized ordered batches of 1–100, sanitized errors, safe startup,
one load per lifespan, verified model/profile identity, unchanged protected files,
passing required checks and accurate scientific limitations.

Details: [execution](phase-01-backend.md). Evidence:
[verification report](reports/verification.md).

State: complete. All required API, real-model HTTP, packaging and preservation
gates passed. Default tests: 121 passed, 5 intentionally skipped; separate API
opt-in: 2 passed. See the verification report for limits and exact evidence.
