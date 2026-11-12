# Scoped code and security review

Reviewed the milestone requirements against `web/app.py`, `api_client.py`,
`components.py`, `charts.py`, frontend tests, packaging and existing API contracts.
Used the installed `ak-code-review` spec-compliance/checklist workflow inline;
the cook skill also required a scoped simplifier pass on client/chart helpers.
This is a local implementation review, not a penetration test or public-hosting approval.

## Findings repaired

- Malformed JSON arrays/null must produce sanitized frontend errors; consumed
  response fields are checked before use. Tests cover malformed JSON, missing
  fields, profile/identity mismatch, nonfinite distances, HTTP errors and timeouts.
- An oversized JSON integer could overflow `math.isfinite`; the numeric helper
  now rejects it and form tests cover it.
- Gradio 6.31 `Blocks.launch` uses `GRADIO_ALLOWED_PATHS` when passed an empty
  list (installed `blocks.py`, lines 3240–3249). The app rejects that environment
  override explicitly; a regression test covers the installed-version behavior.
- Native bar scales initially omitted zero. Distribution and distances now start
  at zero; feature comparisons include zero while retaining negative raw dB values.
- Tablet example-table overflow was removed using native labelled example buttons.
  Phone intrinsic table sizing was bounded at the tab panel, tab navigation uses
  native wrapping, selectors stack, and long chart/accordion titles were shortened.

## Boundaries checked

- Web imports only shared immutable feature config, HTTPX/Pandas/Gradio and local
  presentation modules. Fresh-process tests guard model/data/notebook access and
  server launch during import/construction. No inference/training/store import.
- API URL is fixed operator configuration, not a visitor field. HTTPX does not
  follow redirects or environment proxies. Error bodies/tracebacks/paths and
  submitted values are never rendered. No response strings enter executable HTML;
  metric text is escaped and model IDs are validated.
- Metadata/profile identities and population totals must match. Prediction model
  identity must match a loaded dashboard. Cluster meaning follows returned profiles.
- No file components, arbitrary URL fetch, uploads, dataset route, estimator calls,
  PCA coordinates, probability conversion, storage of prediction inputs or fitting.
- Loopback, fixed ports, share=False, show_error=False, no analytics, run history,
  monitoring or MCP, allowed_paths empty and current working tree blocked.
  Real file-endpoint probes reject CSV, notebook and model bundle access.
- The normal tests remain software evidence only. The existing private sample is
  used only by controlled integration code and never sent to screenshots or reports.
  Wheel inspection rejects CSV/notebook/joblib/private-sample members.
- Historical optimizer equivalence and Holdout remain explicitly unverified/closed.
  The existing backend and deployment artifacts are unchanged.

No unresolved blocking finding remains within the local milestone scope. Future
public-hosting controls are documented in `docs/WEB.md` and remain undeployed.
