# Integrated review: UI refinement

## Scope

- Reviewed the pending UI refinement against `AGENTS.md`, `docs/ARCHITECTURE.md`,
  `docs/DESIGN.md`, and `plans/20261112-ui-refinement/plan.md`.
- Inspected the current diff and surrounding contracts in
  `src/spotify_cluster/web/{app,components,explorer,figures,theme}.py`,
  `scripts/constellation/entry.js`, the generated constellation bundle, and
  `tests/test_web_components.py`.
- Focused on Explorer selection and inspector agreement, asynchronous Gradio
  callback ordering, camera/filter continuity, Three.js lifecycle, reduced motion,
  HTML/input handling, and preservation of model/data identity.

## Overall assessment

No blocking or non-blocking correctness, security, or data-integrity findings remain
in the reviewed revision.

The main candidate defect during review was a lost rapid clear/selection event while
an earlier neighbour request was pending. The final revision explicitly configures
the Explorer `select` dependency with `trigger_mode="always_last"`
(`src/spotify_cluster/web/app.py:426`) and keeps the browser's selected index as the
display authority (`src/spotify_cluster/web/explorer.py:240-255`). Stale cards are
hidden by sample index until the latest queued response arrives. Inspection of the
generated Gradio dependency confirmed `trigger_mode=always_last`.

The final-delta review also found and rechecked two browser-state defects that were
fixed before this report closed:

- Coarse-pointer `touch-action: pan-y` initially remained active after enabling
  Plotly 3D rotation, so vertical orbit gestures could still become page scroll.
  The final CSS and control state now apply `touch-action: none` through
  `.is-touch-enabled` only while coarse-pointer 3D/constellation interaction is
  explicitly enabled (`src/spotify_cluster/web/explorer.py:115-124,238-246`).
- The new keyboard sample picker could submit while the constellation module was
  still importing, updating the inspector without creating the scene's selection
  marker. Scene creation now reapplies `state.selected` after the cluster filter and
  before publishing the live scene handle
  (`src/spotify_cluster/web/explorer.py:532-562`).

No residual finding remains from either issue.

## Findings

None.

## Edge cases checked

- Rapid point selection followed by reset, view change, or cluster filtering while
  the neighbour HTTP request is pending.
- Keyboard sample inspection in 2D, 3D, and constellation views, including hidden
  clusters, aggregate/compact hiding, and submission during lazy scene creation.
- A selected point becoming invisible under a cluster filter.
- Re-rendering after Plotly selection/filter changes without losing the actual
  rendered Plotly 3D camera. The implementation snapshots Plotly 6.9's live scene
  camera before trace changes; explicit reset/projection changes clear the cache.
- Coarse-pointer behavior: default 2D permits native vertical page scroll, while
  explicit 3D/constellation interaction mode owns touch gestures and can be returned
  to page scrolling.
- Lazy constellation import resolving after a view change or component teardown;
  generation checks discard stale imports and disposal disconnects observers,
  controls, pointer handlers, geometries, materials, texture, renderer, and WebGL
  context.
- Reusing a live constellation for filtering versus disposing it on view/payload
  changes.
- Point, 3D, constellation, density, aggregate-only, backend-offline, and no-selection
  paths.
- Reduced-motion behavior: Plotly transitions remain disabled, scroll behavior uses
  `prefers-reduced-motion`, and the constellation has no damping/autorotation loop.
- Gradio callback input/output arity and the removal of the redundant tab-selection
  callback.

## Scoped security review

### Attack surface

The changed browser surface emits only a sample index and view name through the
private Gradio selection event. The Gradio handler sends the integer index to the
existing FastAPI neighbour endpoint through `APIClient`; it does not read files,
load artifacts, fit models, or accept a URL/path/command sink.

### Non-findings considered

- **DOM/XSS:** tooltips and live status use `textContent`; server-rendered API/error
  strings pass through HTML escaping, and the HTTP client validates consumed numeric,
  identity, feature-order, and neighbour response fields before rendering.
- **Tampering / model confusion:** refresh checks profile, visualization, research,
  and model identities; neighbour responses are checked again against the model in
  the Gradio state before inspector rendering.
- **DoS:** no new unbounded server operation was added. Selection requests use the
  fixed neighbour count of eight; rapid selection is coalesced to the latest pending
  event.
- **Data disclosure:** the UI continues to expose only approved sampled raw F9
  descriptors/local sample indices or aggregate occupancy. No track identifier,
  dataset path, model bundle, notebook output, or stack trace is introduced.
- **Privilege/auth changes:** none. The reviewed change adds no authentication,
  authorization, upload, filesystem, training, or artifact-loading route.

## Verification evidence

- `pytest tests/test_web_components.py -q`: **25 passed**.
- Ruff over the scoped Python source and test files: **0 issues**.
- `node --check scripts/constellation/entry.js`: **passed**.
- `git diff --check`: **passed** (Git emitted only the existing generated-bundle
  LF/CRLF warning).
- Review-time Gradio config inspection: Explorer `select` dependency is
  `always_last`.
- The controller supplied browser evidence for desktop/tablet selection, neighbours,
  density, prediction, 3D, camera/filter continuity, constellation reuse/disposal,
  mobile tap/keyboard inspection, and real rendered-camera equality after rotation,
  wheel zoom, filter, and reset. The final coarse-pointer 3D orbit/no-page-scroll
  assertions were still running when this read-only delta review closed.

## Metrics and limitations

- Type coverage: not measured (Python project; no scoped type-coverage gate supplied).
- Test coverage percentage: not measured; focused behavioral suite passed.
- Lint issues: 0 in reviewed Python files.
- Full repository suite: not rerun by this reviewer; the controller reported the
  pre-review 53-test suite passing.
- Scientific artifacts, dataset, notebook, model bundle, backend training, and
  deployment configuration were intentionally not accessed or modified.

## Recommended action

Proceed once the controller records the final coarse-pointer browser-suite result and
generated-bundle parity. No code change is requested by this review.
