# Gradio web milestone

Status: complete (2026-11-12), verified locally. Work context: `D:/spotify_music_cluster`. Evidence: [verification](reports/verification.md).

Outcome: four functional, polished Gradio tabs using the existing FastAPI HTTP
contract, with real local prediction, aggregate charts, tested errors and packaging.
Constraints: Python 3.12; scientific pins preserved; no model/dataset imports in
web code, refit, notebook execution, Holdout reopening, publishing or remote hosting.
Non-goals: MP3/URL ingestion, PCA coordinates, genre accuracy or probabilities.
Acceptance: all 20 criteria in the supplied milestone request, verified by software
tests, real HTTP integration, browser inspection where available, Ruff and builds.

## Design brief

Register: Product.
Scene: academic presenters and portfolio visitors exploring acoustic data on desktop
or phone, with a calm dark analytics surface.
Direction: understated music analytics; the measured cluster split is the signature.
Color: restrained; background oklch(0.18 0.01 155), text oklch(0.95 0.01 155),
accent oklch(0.78 0.17 155); secondary cluster blue with explicit labels.
Type: local system sans; hierarchy through size and weight, tabular numeric values.
Signature: two labelled cluster bars and a prominent measured separation diagnostic.
Dials: variance 3, motion 1, density 5.

## Phases

1. Inspect live backend and record [HTTP contract](contract.md); dependencies.
2. Implement client, pure presentation/chart helpers and four-tab Blocks app.
3. Test client failures, chart values, handlers and offline construction; real HTTP
   smoke, browser desktop/mobile, wheel install, existing regression gates.
4. Review code/security, update owning docs and [verification](reports/verification.md).

Risks: Gradio 6 configuration and file serving; schema drift; mixed model identities;
misrepresenting transformed distances or historical evidence. Validate consumed
responses, clear failed outputs, keep identity checks and local launch restrictions.
Rollback: remove only milestone web files/dependency/docs edits; never touch protected
artifacts. No Git baseline exists; preserve all existing untracked work.

## Completion

All four tabs, the HTTP client, aggregate charts, tests, packaging and docs are in
place. Final evidence: 196 passed / 6 skipped, real API opt-in 2 passed, Ruff,
build, wheel install, real HTTP/browser smoke and protected hashes all pass.

Two functional defects were found by the smoke and fixed: HTTPX 0.28 rejects
bracketed IPv6 `NO_PROXY` entries before Gradio imports, and Gradio 6.31 native
`BarPlot` keeps stale bars on data updates. The charts therefore use Matplotlib
figures through `gr.Plot`, which re-encodes on every change.
