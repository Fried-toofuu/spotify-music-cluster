# Acoustic Observatory UI refinement

## Outcome and constraints

Deliver the attached final refinement brief in the existing Gradio/Plotly/Three.js
application. Keep the acoustic map central, compact the header and mobile entry,
clarify Explorer selection, disclose detailed prediction/research evidence on demand,
and preserve the established charcoal/teal/violet design.

No training, Holdout access, artifact regeneration, scientific metric changes,
new frontend framework, public data expansion, or deployment configuration changes.
The original notebook, dataset and fitted bundles are protected. Public deployment
is conditional on authorization; local implementation and verification proceed now.

## Design brief

Register: Product.
Scene: Visitors explore acoustic research on desktop and phone, in a dark analytical studio.
Direction: Editorial scientific instrument because the genuine acoustic space is the content.
Color: Restrained; existing charcoal background, pale text, mint and violet cluster identities.
Type: Existing system serif display, sans body, mono technical notation.
Signature: Real PCA acoustic map beside the compact editorial introduction.
Dials: variance 3, motion 2, density 5.

## Phases and acceptance

- [x] Baseline: capture four tabs at 1440×900, 768×1024, 375×812; inspect live status.
- [x] Implement: map in first desktop viewport; compact header and discoverable mobile tabs;
  accessible controls; selection/inspector agreement; filter camera continuity;
  prediction distance disclosure; three research layers with intact evidence.
- [x] Verify: existing tests, relevant behavioral tests, lint/format/build, actual browser
  interactions including points/3D/constellation/fallback and keyboard/mobile states.
- [x] Review: independent integrated review, scoped security review and visual inspection.
- [x] Finish: update owning docs/screenshots, report exact evidence and limitations, handoff.

Dependencies: existing trusted artifacts; Python virtualenv and Chromium browser.
Baseline source: main at 7fb39ef9e0221e84951c8e7d607c5c7469165f70, clean worktree.
Evidence and execution details: [reports](reports/).

## Risk and rollback

Gradio callback arity, lazy scene lifecycle, and stale asynchronous selection are the
main integration risks. Preserve API response contracts and test browser callbacks.
Rollback is reverting the scoped UI commit; existing model/artifacts remain untouched.

Final evidence: [delivery report](reports/delivery.md). Publication remains a separate decision.
