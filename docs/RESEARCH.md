# Research design and controlled comparisons

This page separates the historical research authority (the unchanged notebook)
from the deployed model and from the new, explicitly exploratory comparison
artifact. The application presents all three with different labels.

## Question and approach

The study asks whether Spotify's numerical acoustic descriptors form
interpretable acoustic groups **without using genre labels as targets**. This is
unsupervised clustering: there is no classification accuracy to report. The
meaning of a fitted label comes from the current artifact's raw-unit cluster
profiles, not from its number.

## Authorized data and preparation

- Maharshi Pandya Spotify Tracks Dataset snapshot, SHA-256
  `b202fa49909b2d5cef71a04b1d21243cfeb36414535f2ca9272aa646721177bd`.
- 114,000 raw rows → 89,741 canonical track IDs after consistency checks and
  deduplication; 114 reported genres remain in a separate descriptive bridge
  only.
- F9 order: `acousticness, danceability, energy, valence, tempo, loudness,
  speechiness, instrumentalness, liveness`.
- RobustScaler (median/IQR) is paired with K-Means in one fitted Pipeline.
  There is no modeling PCA.
- The dataset license is ODbL 1.0; derived track-level coordinates remain
  private by default.

## Historical evidence vs deployed model

The archived historical evidence belongs to the **historical** frozen
F9/Robust/K-Means/K2 estimator and its one-time Holdout evaluation. It is
reproduced in the Research tab from the labeled research artifact and was
**not recomputed** for this application:

| Archived historical metric | Value (archived) |
|---|---|
| One-time Holdout Silhouette | 0.6076945989627338 |
| One-time Holdout Davies–Bouldin | 0.6323066464652578 |
| One-time Holdout Calinski–Harabasz | 3750.5583111569226 |

The deployed model is a separately approved **deployment-v1** refit on all
canonical tracks. It is not verified equivalent to the historical estimator.
The historical Holdout remains closed; it was not reopened, rerun, extended or
used to select deployment settings. No historical metric is attached to
deployment predictions.

## Deployment-v1 recipe

K-Means, K=2, F9, RobustScaler, no modeling PCA; k-means++, n_init=20,
max_iter=300, tol=0.0001, Lloyd algorithm, seed 42. These are the approved
deployment settings; they do not establish the historical optimizer settings.

## Dominant finding

The fitted deployment artifact's between-cluster sum of squares is 97.3022%
attributable to instrumentalness in scaled space. Raw means are approximately
0.0194 in Cluster 0 and 0.8077 in Cluster 1. Because instrumentalness has a small
interquartile range, RobustScaler amplifies that dimension. The honest reading is
a largely instrumental / less-instrumental partition, not a genre classifier.
A high internal separation diagnostic is not predictive accuracy.

## New controlled development comparison

`scripts/prepare_research.py` writes an aggregate-only artifact
(`artifacts/research-v1/comparison.json`) using the full canonical training
population, identical rows and documented recipes. It is a new exploratory
development calculation, **not model selection, not a Holdout and not a
deployment change**.

| Comparison | Result |
|---|---|
| F5 StandardScaler K-Means vs deployed F9 RobustScaler K-Means | Adjusted Rand Index **+0.0630** |
| F9 K-Means vs a diagonal-covariance F9 GMM, identical fitted scaled representation | Adjusted Rand Index **+0.3117** |
| GMM mean maximum responsibility / mean entropy | **0.9955** / **0.0175 nats** |

Interpretation:

- Feature geometry changes the partition substantially: a low ARI between the
  F5 and F9 partitions is informative, not a quality ranking.
- K-Means minimizes squared centroid distance; a GMM models posterior
  responsibilities. The hard GMM partition is `argmax` responsibility. The
  GMM's high mean maximum responsibility means its soft assignment is, in this
  dataset, close to hard assignment.
- ARI measures partition agreement, not quality. Silhouette values are not
  compared across different feature geometries, and no model is chosen by this
  comparison.

The F5 recipe is a new development recipe (StandardScaler, k-means++, n_init=20,
max_iter=300, seed 42); it is not asserted to reproduce the archived historical
F5 baseline.

## Reproduction and verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_research.py
.\.venv\Scripts\python.exe scripts/prepare_research.py `
  --dataset dataset.csv --model-dir artifacts/deployment-v1 `
  --output artifacts/research-v1
```

The artifact stores the dataset/model identity, exact recipes, population
counts, ARI values, responsibility diagnostics, software versions, archived
evidence labels and a checksum. The loader verifies identity, Holdout closure,
labeling, ARI bounds and aggregate counts. It contains no per-track rows.

## Limitations

- Acoustic descriptors are algorithmic; no listening study establishes
  perceptual or cultural validity.
- Track-disjoint cohorts are not artist-disjoint.
- Cluster labels are arbitrary and can swap across refits.
- Distances are Euclidean in fitted scaled space, not probabilities.
- The archived historical metrics do not describe deployment-v1; equivalence is
  **NOT VERIFIED**.
- The comparison artifact is aggregate-only and contains no individual track
  evidence.
