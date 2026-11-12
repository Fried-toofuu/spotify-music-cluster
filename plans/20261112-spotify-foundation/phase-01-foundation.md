# Execution details

Read original notebook without executing cells or publishing private configuration.
Use only the supplied CSV. Its digest matches the declared snapshot.

Implement config/data/training/model_store/inference under src/spotify_cluster,
scripts/export_model.py, tests, packaging and requested docs. Keep notebook in its
original location and ignored, because its configuration includes a private URL.

The archived selection gives F9/Robust/K2 and separate final-refit identity but
omits final-refit optimizer parameters. Do not promote QUICK/FULL demonstration
parameters into historical settings. Production export must fail before fitting.

Validate data first, then synthetic training/serialization/inference tests, CLI
blocking behavior, Ruff, build, fresh wheel install and archive contents. Verify
manual scaling, centroid distances, fresh-process round trip and repeat fitting
only on software fixtures while the scientific gate is unresolved.

Risks: joblib executes pickle; only operator-trusted local bundles are supported.
Checksums provide integrity, not authentication. Pin and record scientific stack.
Rollback: remove newly created project outputs; preserve notebook and CSV.
