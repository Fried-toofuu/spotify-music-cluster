# PCA visualization pipeline

The Explorer and Overview charts are backed by an **offline, versioned
visualization artifact**. The deployed clustering model is never fitted or
changed by this pipeline. PCA is a visualization projection only: it is not used
to fit K-Means, assign clusters or compute model distances.

## Inputs and authorization

| Input | Requirement |
|---|---|
| Dataset | The authorized Maharshi Pandya Spotify Tracks Dataset snapshot, SHA-256 `b202fa49909b2d5cef71a04b1d21243cfeb36414535f2ca9272aa646721177bd`, 114,000 raw rows → 89,741 canonical tracks (`notebook-track-f9-v1`). |
| Model | The trusted `artifacts/deployment-v1` bundle (`spotify-f9-robust-kmeans-k2-v1`), loaded with its checksum and environment checks. |
| Representation | The fitted `RobustScaler` + F9 matrix used by the deployed model. No alternative dataset, Spotify API fetch, synthetic evidence or retraining. |

The dataset page describes the database as **ODbL 1.0**, with
`Database: Open Database, Contents: © Original Authors`. ODbL permits sharing
and adaptation with attribution and share-alike obligations. Separately, the
project's data-publication boundary requires approval before publishing derived
artifacts. The default local application therefore uses the **points** artifact
(private/local), while the public deployment uses the **aggregate** artifact.
The repository never commits either artifact or the raw CSV.

## Prepare the artifacts

```powershell
# Private/local: per-track coordinates, features and occupancy grid
.\.venv\Scripts\python.exe scripts/prepare_visualization.py `
  --dataset dataset.csv --model-dir artifacts/deployment-v1 `
  --output artifacts/visualization-v1 --mode points

# Public: aggregate occupancy only (no per-track coordinates or features)
.\.venv\Scripts\python.exe scripts/prepare_visualization.py `
  --dataset dataset.csv --model-dir artifacts/deployment-v1 `
  --output artifacts/visualization-public-v1 --mode aggregate

# Controlled research comparison (training population only)
.\.venv\Scripts\python.exe scripts/prepare_research.py `
  --dataset dataset.csv --model-dir artifacts/deployment-v1 `
  --output artifacts/research-v1
```

Output directories are new-only; partial writes are staged and renamed. The
scripts verify the dataset hash and that the model metadata matches the prepared
fingerprint, canonical count and deployment profile before writing anything.

## What is computed

1. Load the dataset and the trusted deployment bundle.
2. Assign clusters with the fitted Pipeline; verify assignments equal
   `KMeans.labels_`, counts equal the model metadata and profiles.
3. Transform the full canonical training matrix with the **fitted deployment
   scaler**.
4. Fit a **visualization-only** `PCA(n_components=3, svd_solver="full",
   random_state=42)` on that scaled representation. Components receive a
   deterministic sign convention (largest absolute loading positive).
5. Recompute the projection for the full population and verify it against the
   fitted PCA.
6. Select a deterministic, equal-cap stratified sample per cluster using
   `numpy.random.default_rng(42)`; sample order is canonical row order.
7. Build an aggregate 40×40 PC1/PC2 occupancy grid from the **full** population
   with a minimum cell count of 10.
8. Verify every artifact invariant, write a checksummed
   `verification_report.json`, then round-trip through the loader.

The real artifact produced on this checkout:

| Field | Value |
|---|---|
| Sample | 6,000 points (3,000 / 3,000) |
| Population | 89,741 tracks (72,211 / 17,530) |
| Explained variance | PC1 55.6988%, PC2 25.0315%, PC3 6.5385% (cumulative 87.2689%) |
| Occupancy | 40 bins, min cell count 10, 306 exported cells |
| Model ID | `spotify-f9-robust-k2-0828777db6924fe39e47335c19cc9363` |

## Artifact contract

`artifacts/visualization-v1/visualization.json` (points mode) contains:

- identity: schema, model ID, deployment profile, dataset SHA-256, prepared
  fingerprint, preparation version, creation time;
- population counts/shares;
- PCA: explained variance, cumulative variance, components, mean, sign
  convention and the explicit **visualization-only** scope;
- sample policy, seed, cap, size, sample counts and a disclosure that plotted
  proportions are not population proportions;
- coordinates `x`, `y`, `z`, cluster assignments, raw F9 rows (8 decimals) and
  the fitted scaler center/scale (for independent projection verification);
- aggregate occupancy cells with count, cluster-1 share and mean
  instrumentalness;
- software versions, dataset license and scientific limitations.

The public aggregate mode omits `points` and sets `sample.size = 0`; it keeps
the occupancy grid, PCA metadata and population totals. No track IDs, names,
artists, albums, popularity, genre or row positions are exported. The loader
recursively rejects record-level field names.

## Verification

- Checksum of `visualization.json` against the report.
- Schema/version, F9 feature order, model/profile identity, population totals.
- PCA components finite and orthonormal (3×3 Gram matrix ≈ I).
- Explained variance non-increasing and cumulative consistent.
- Coordinates recompute from the recorded raw features, scaler state, PCA mean
  and components within `2e-6` (the independent projection check).
- Feature domains, finite values, cluster IDs, sample counts and occupancy
  minimum-cell policy.
- Deterministic sampling is re-run at build time.
- No record identifiers anywhere in the payload.
- `pytest tests/test_visualization.py` covers the software-fixture contract,
  tamper rejection, identity mismatch, aggregate privacy and neighbor space.

## API surface

| Method | Path | Content |
|---|---|---|
| GET | `/api/v1/visualization/meta` | Available/ unavailable, mode, identity, PCA, sample policy, views, license |
| GET | `/api/v1/visualization/points` | Points view (private artifact only), including occupancy for the density switch |
| GET | `/api/v1/visualization/occupancy` | Aggregate density view |
| GET | `/api/v1/visualization/neighbors?index=&k=` | Selected sampled point and up to 12 nearest sampled tracks in fitted scaled F9 space |

The API loads the artifact once per worker in the FastAPI lifespan; a missing,
incompatible or mismatched artifact is reported as unavailable, not as a
readiness failure. Responses are compressed (`gzip`, ~207 KB for the 6,000-point
payload; ~574 KB uncompressed) and bounded. The browser never opens the model
bundle or dataset.

## Public fallback

If per-track redistribution approval is unavailable, deploy with
`SPOTIFY_VISUALIZATION_DIR=artifacts/visualization-public-v1`. The Explorer then
serves the aggregate density view: cells contain at least 10 training tracks,
are never labeled as individual tracks, and no per-track coordinates or
features leave the server. The UI states this explicitly. The private points
mode is not enabled by any public route.

## Performance and limits

Measured on this checkout: `/visualization/points` ~7.6 ms locally (574,542 B
uncompressed; 207,431 B gzip); Explorer plot ready ~1.17 s after tab selection;
3D switch ~1.33 s; 18 view switches kept JS heap at ~115 MB. These are local
measurements, not universal budgets. The PCA coordinates are visualization
coordinates, not the model's training distances; the plotted stratified
proportions are not population proportions; cluster labels are acoustic groups.
