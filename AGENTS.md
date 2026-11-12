# Project boundaries

- Treat the original final notebook as research authority. Preserve it unchanged;
  keep its private configuration and stored outputs out of public commits.
- Use only the authorized CSV snapshot. Do not substitute a dataset or present
  synthetic software fixtures as scientific evidence.
- Use the explicitly authorized deployment-v1 recipe for new deployment refits.
  Keep historical-final-refit gated; historical equivalence stays NOT VERIFIED.
  Do not claim deployment settings establish historical optimizer settings.
- Never reopen Holdout, perform HTTP retraining or train during inference.
- Preserve exact F9 order and pair fitted scaler/centroids in one Pipeline.
- Load only operator-trusted local joblib bundles; checksums are not signatures.
- Do not use the abandoned repository or publish data/artifacts without approval.
- Use FastAPI for local model serving and Gradio as its HTTP-only frontend;
  avoid unnecessary infrastructure.
- Follow [README.md](README.md) for setup and checks and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
  for implementation ownership. Verify results before claiming success.
