---
title: Integrate local FastAPI model serving
date: 2026-11-12
summary: Verified REST serving without model changes or refitting
---

# Integrate local FastAPI model serving

Implemented the local FastAPI adapter over the verified deployment-v1 inference service. Added strict F9 HTTP schemas, lifespan state, safe metadata/profile views, ordered bounded batches and sanitized failures. The artifact's NOT VERIFIED spelling maps to not_verified only in HTTP.

Default tests: 121 passed, 5 private tests skipped. Separate API opt-in: 2 passed. Real Uvicorn loopback smoke, Ruff, wheel/sdist build and fresh-wheel inference passed. All protected artifact and notebook hashes match. No refit or Holdout evaluation occurred.

The smoke harness initially blocked in NumPy native import after starting a Windows stdin reader. Importing the application before starting that helper resolved the block; final startup was about one second, and shutdown released port 8000.

Current operational guidance is docs/API.md; detailed evidence is plans/20261112-fastapi-backend/reports/verification.md. Gradio and remote deployment remain future work.

> Historical work record — not durable authority. Prefer docs/specs/ADRs for current decisions.
