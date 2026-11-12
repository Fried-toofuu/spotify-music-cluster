# Approved deployment model execution

Outcome: train and export the explicitly authorized deployment-v1 recipe on the
verified 89741 canonical tracks, then verify actual model serving independently.
Historical final-refit identity stays NOT VERIFIED. Preserve notebook, CSV,
preparation policy and existing software contracts. No web framework, remote
publication, model search or Holdout evaluation.

Sequential phases:

1. Add immutable deployment profile, explicit CLI selection and provenance.
2. Extend local bundle verification with profiles and deterministic private sample.
3. Train/export once; verify numerics, fresh-process/fresh-wheel inference and one
   sequential reconstruction in a temporary directory.
4. Run existing/new tests, Ruff, build and security review; update owning docs.

Acceptance: exact profile/parameters, full verified population, paired fitted
Pipeline, own identity, five complete checksum-verified artifacts, current raw-unit
profiles and measured feature contributions, no dataset access during inference,
all executed software/artifact gates PASS, notebook hash unchanged.

State: complete. The actual deployment model and all requested software/artifact
gates were verified. Historical-final-refit remains gated and historical identity
remains NOT VERIFIED. See [verification](reports/verification.md) and
[machine evidence](reports/evidence.json).
