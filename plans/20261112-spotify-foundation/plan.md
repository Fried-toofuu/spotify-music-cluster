# Spotify foundation execution plan

Outcome: a standalone Python 3.12 package extracting the final notebook's data
preparation, offline training/persistence and reusable inference. Preserve both
source inputs. No web framework, remote repository, model selection or Holdout
evaluation. Complete the safe foundation even if scientific evidence blocks export.

Acceptance: exact snapshot and canonical (89741, 9) F9 matrix verified; training
settings sourced before production export; trusted-local bundle validation;
single/batch inference; independent arithmetic and serialization checks; pytest,
Ruff and build; fresh wheel installation and factual evidence report.

Phases (sequential dependencies):

1. Audit notebook and dataset; recover preparation/settings and environment.
2. Implement package, CLI and explicit scientific export gate.
3. Verify software with synthetic fixtures and real dataset preparation; review.
4. Document usage, evidence, blockers and remaining acceptance criteria.

Execution detail: [phase-01-foundation.md](phase-01-foundation.md).
State: safe foundation implemented and verified. Production final export remains
blocked by absent final-refit parameter evidence; the full milestone is not complete.
See [verification](reports/verification.md) and [machine evidence](reports/evidence.json).
