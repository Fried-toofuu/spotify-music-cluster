---
title: Build local Gradio web frontend
date: 2026-11-12
summary: Four-tab HTTP-only UI with real-model integration and browser verification
---

# Build local Gradio web frontend

Implemented the milestone's Gradio interface over the existing FastAPI backend:
four tabs (Overview, Predict Cluster, Cluster Explorer, Research & Methodology),
an HTTPX client with sanitized errors and consumed-response checks, aggregate tables
and charts, and local-only launch restrictions. The frontend never loads the model,
dataset or notebook.

Final gates: 196 passed, 6 skipped; real-API opt-in 2 passed; Ruff check/format,
build, pip check, wheel install/import and protected hashes pass. The real
Uvicorn + Gradio smoke passed on ports 8000/7860 with clean shutdown. Browser
checks at 1440×900, 768×1024 and 375×812 produced 12 tab screenshots plus 3
invalid-input captures, no page errors and a clean render-check.

Two defects found by the smoke:

- Gradio builds an HTTPX client at import; HTTPX 0.28.1 rejects `[::1]` in this
  environment's `NO_PROXY`, so the app failed before construction. The web package
  now removes IPv6 brackets before Gradio imports, with a subprocess regression test.
- Gradio 6.31's native `BarPlot` changes titles but keeps the first bars after data
  updates; a minimal reproduction confirmed it. Charts moved to Matplotlib figures
  through `gr.Plot`, which re-encode on every change and were rechecked in the
  browser, including a 375px legibility pass.

The `web` extra adds Matplotlib; scientific pins, model artifacts and the notebook
are unchanged. Historical equivalence remains NOT VERIFIED and the Holdout stays
closed. No remote deployment or share link exists. Current guidance is docs/WEB.md;
evidence is plans/20261112-gradio-web/reports/verification.md.

> Historical work record — not durable authority. Prefer docs/specs/ADRs for current decisions.
