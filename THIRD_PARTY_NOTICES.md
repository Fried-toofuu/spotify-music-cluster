# Third-party notices

This repository includes or uses the following third-party materials.

## Data

**Spotify Tracks Dataset** by Maharshi Pandya (Kaggle):
<https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset>.
The dataset page describes the database as **ODbL 1.0** with
“Database: Open Database, Contents: © Original Authors.” The raw CSV and derived
artifacts are not committed. Track-level derived visualization data remains
private by default; public deployment uses the aggregate-only artifact unless
redistribution is explicitly approved. ODbL attribution/share-alike obligations
still apply to any distributed derivative.

## Three.js

The optional constellation bundle `src/spotify_cluster/web/static/constellation.js`
is built from **three@0.187.0** under the MIT License, copyright © 2010–2026
three.js authors. See
[src/spotify_cluster/web/static/THIRD_PARTY_LICENSES.txt](src/spotify_cluster/web/static/THIRD_PARTY_LICENSES.txt).
The reproducible source/build is in
[scripts/constellation](scripts/constellation).

## Plotly

The Plotly Python package (pinned in `constraints.txt`) and its bundled
`plotly.min.js` are served from the installed package under the MIT License,
copyright © 2016–2024 Plotly Technologies Inc. The same license text is included
in the static third-party license file.

## Python and frontend dependencies

Runtime Python dependencies are declared in `pyproject.toml` and pinned in
`constraints.txt`; their own licenses are distributed with the installed
packages. No credentials or private dataset content are included.
