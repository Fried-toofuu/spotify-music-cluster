# Simplification pass

Reviewed the current UI diff in the six scoped source files. Applied one bounded,
behavior-preserving cleanup in `explorer.py`: the Plotly configuration now reuses
the existing `coarsePointer` result instead of evaluating the same media query a
second time. No public contracts or UI semantics changed.

Verification:

- `ruff check src/spotify_cluster/web/explorer.py` — passed
- `pytest tests/test_web_components.py tests/test_web_app.py -q` — 30 passed
