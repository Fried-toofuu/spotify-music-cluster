# Observed HTTP contract

Inspected source: `api/schemas.py`, `api/routes.py`, `inference.py`, `docs/API.md`.
Confirmed over real loopback HTTP before web implementation; backend exited 0.

- Base URL is operator configuration; paths are `/api/v1/health`, `/model`,
  `/clusters`, `/predict`, `/predict/batch` under `/api/v1`.
- Health: ready, model_loaded true. Model: model_id, deployment_profile,
  algorithm=KMeans, number_of_clusters=2, scaler=RobustScaler, ordered features,
  training_sample_count, modeling_pca=null, model_origin, historical_equivalence.
- F9 order: acousticness, danceability, energy, valence, tempo, loudness,
  speechiness, instrumentalness, liveness. Seven descriptors [0,1]; tempo >=0;
  loudness finite without a bound. POST single body is this exact flat object.
- Prediction: cluster_id, model_id, distances [centroid 0, centroid 1],
  distance_definition, profile, limitation and deployment/historical provenance.
  Distances are Euclidean in fitted RobustScaler space, not probabilities.
- Clusters: model_id, units='raw F9', clusters keyed '0'/'1'; each has
  cluster_id/count/share and mean/median/std/q1/q3/iqr maps in F9 raw units.
  std_ddof=1. Contributions expose definition/population/between_ss/shares.
- Real model ID: spotify-f9-robust-k2-0828777db6924fe39e47335c19cc9363.
  Population 89741; cluster counts 72211/17530; shares .8046600773/.1953399227.
  Instrumentalness contribution .9730218110901931. These are observed evidence,
  not application constants. No additional backend field is required.
- Errors: 422 invalid input, 503 unavailable, 500 internal. The web must never
  render raw bodies, exception messages, private paths or submitted values.

Browser talks to Gradio; Python HTTPX talks to the configured backend. Metadata
and profiles are per-session public aggregate state, refreshed explicitly. A failed
refresh clears that state; predictions do not reuse stale results. No prediction
inputs are cached or written to disk. Model IDs must agree before combining data.

Version references inspected 2026-11-12: official Gradio Blocks docs, Gradio 6
migration guide and Creating Plots guide (retrieved via their `/api/markdown/`
routes). Themes/CSS belong on launch; native BarPlot consumes Pandas tables.
Installed Gradio 6.31.0 signatures checked locally. No custom JavaScript needed.
