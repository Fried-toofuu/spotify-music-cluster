---
title: Acoustic Observatory
emoji: 🎛️
colorFrom: indigo
colorTo: teal
sdk: docker
app_port: 7860
pinned: false
---

# Acoustic Observatory

An interactive scientific music-intelligence application for unsupervised
acoustic clustering, built from the authorized Spotify Tracks Dataset
(Maharshi Pandya, ODbL 1.0).

- **FastAPI** serves the trusted deployment-v1 F9/RobustScaler/K-Means/K2 model.
- **Gradio** is the HTTP-only browser frontend (port 7860).
- The model bundle and private verification sample live in a **private
  Hugging Face dataset** and are downloaded at startup with an `HF_TOKEN`
  Space secret. They are not part of this public repository.
- The owner approved public per-track coordinates and 3D on 2026-11-12. The
  approved public deployment mounts the **points** artifact
  (`SPOTIFY_PUBLIC_MODE=0`): a 6,000-track stratified sample with PCA
  coordinates, cluster assignments and F9 acoustic rows, no track
  identifiers/names/genres, and ODbL attribution. The deploy script defaults to
  the aggregate artifact; points mode requires `--allow-public-points`.
- Clusters are acoustic groups, not genres or moods. Centroid distances are not
  probabilities. Historical estimator equivalence is **NOT VERIFIED**; the
  historical Holdout remains closed.

Source and methodology:
<https://github.com/Fried-toofuu/spotify-music-cluster>

This is a free CPU demo, not a hardened production deployment. It may cold-start
after inactivity, and the public Gradio prediction flow has no application-level
authentication or rate limiting. Use the model only through the published
inference endpoints; do not upload private data.
