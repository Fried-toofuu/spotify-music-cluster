# Notebook extraction audit

Source: the unchanged root `Spotify_Music_Clustering_Final.ipynb`. Cell references
are zero-based JSON indices, not execution counters. All 117 cell sources were
read; no cell was executed. Private transport configuration is omitted here.

| Cells | Evidence and extraction decision |
|---|---|
| 0-9 | Development-only presentation, QUICK=True, seed 42, fit cap 12000; exact snapshot digest. No network transport is copied. |
| 11-12 | Ordered F9 and domains. Genre excluded; loudness is dB, tempo nonnegative. |
| 13-25 | CSV schema; normalized stripped IDs; reject missing IDs; float64 numeric parsing; finite/domain checks; per-ID extrema compared with rtol=1e-6, atol=1e-8. |
| 24-26 | Separate distinct normalized track/genre bridge; stable sort by ID, genre and source row, missing genres last, keep first; sort final tracks by ID. |
| 28-33 | ID-based Fit/Evaluation/Holdout split and QUICK subsampling. These are not rerun: requested final refit would use all 89741 unique tracks. |
| 42-53 | RobustScaler() defaults; fit on Fit in the demo. StandardScaler and PCA are comparisons/projections, not selected final modeling steps. |
| 54-67 | F5 baseline: k-means++, seed 42, n_init 10 QUICK/20 FULL, max_iter=400. This is not the selected F9 final refit. |
| 69-88 | GMM and candidate comparisons. F9 K-Means in cell 82 explicitly sets only K=2, n_init 10 QUICK/20 FULL and seed 42. Remaining optimizer settings are installed-library defaults for that development call. |
| 89-108 | F9/Robust/K2 development visualization/profile; arbitrary labels; raw-unit profiles; instrumentalness dominance and sensitivity checks. |
| 109-112 | Archived 77 candidates (27 K-Means, 50 GMM), frozen representation F9/Robust/no-PCA/K2; one-time Holdout and separate final refit. No final estimator or final-refit optimizer settings serialized or specified. |
| 113-116 | Research limitations, development-only conclusions and reproducibility warnings. |

## Historical identity ambiguity

The archive identifies a representation and separate final-refit procedure, but
does not say whether final n_init was 10, 20 or another value; it does not record
final max_iter, init, tol, algorithm or full scaler settings independently of the
demonstration. Inferring the final optimizer from either cell 55 (F5 baseline)
or cell 82 (F9 development) would invent research provenance.

Therefore config.final_kmeans_params() still gates historical reconstruction.
Historical aggregate metrics cannot prove centroid equality. Exact historical
equivalence is NOT VERIFIED. The user has separately authorized a new deployment
recipe; recovering historical optimizer settings is not its prerequisite.

## Approved deployment recipe

[config.DEPLOYMENT_V1](../src/spotify_cluster/config.py) is the immutable owning
recipe and records parameter provenance. Profile `deployment-v1`, ID
`spotify-f9-robust-kmeans-k2-v1`, uses the selected F9/Robust/K2/no-PCA
representation. Seed 42 comes from cell 3 and n_init=20 from cell 82's FULL
development example. They are now adopted for deployment, not asserted as
historical final-refit settings.

The user explicitly adopts init=k-means++, max_iter=300, tol=1e-4,
algorithm=lloyd, copy_x=True and verbose=0 from the documented
[scikit-learn 1.6 defaults](https://scikit-learn.org/1.6/modules/generated/sklearn.cluster.KMeans.html).
They are frozen explicitly to prevent future default drift. max_iter=400 from
the F5 baseline is excluded. RobustScaler's full approved settings are also
explicit in the recipe. No candidate selection or Holdout evaluation follows.

Deployment metadata uses model_origin=new_deployment_refit and its own UUID;
historical_equivalence retains the existing literal NOT VERIFIED. Archived
research evidence and the original notebook are unchanged. A full-population
refit has no newly independent Holdout score.

## Environment and implementation differences

Stored cell 5 output reports Python 3.13.18, NumPy 2.4.6, Pandas 2.2.3 and
scikit-learn 1.6.1; notebook language metadata says 3.12. The executed output is
the stronger evidence of that run. The requested project target is Python 3.12.
The project pins NumPy 2.2.6, Pandas 2.2.3 and scikit-learn 1.6.1; no exact
historical reproduction claim follows from those pins. Actual environment
versions are recorded in generated bundle metadata and the verification report.

Safety improvements: boolean descriptors are explicitly rejected; production
loading requires snapshot counts, strict metadata and fitted-state checks;
training uses one thread for bounded resource use and reproducibility. These
are software safeguards, not new scientific feature engineering. Data hashing
uses length-prefixed normalized UTF-8 IDs followed by little-endian float64
row-major F9 bytes and the preparation version.
