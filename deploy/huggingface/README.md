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
- The default public Space mounts the **aggregate** visualization artifact only
  (`SPOTIFY_PUBLIC_MODE=1`): no per-track coordinates or raw F9 rows are
  distributed. A points-mode deployment is available only with explicit
  redistribution approval; it serves per-track derived coordinates through the
  app with ODbL attribution.
- Clusters are acoustic groups, not genres or moods. Centroid distances are not
  probabilities. Historical estimator equivalence is **NOT VERIFIED**; the
  historical Holdout remains closed.

Source and methodology:
<https://github.com/Fried-toofuu/spotify-music-cluster>

This is a free CPU demo, not a hardened production deployment. It may cold-start
after inactivity, and the public Gradio prediction flow has no application-level
authentication or rate limiting. Use the model only through the published
inference endpoints; do not upload private data.
