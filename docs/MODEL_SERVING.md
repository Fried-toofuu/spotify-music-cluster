# Model serving contract

Profile `deployment-v1` is an explicitly approved new deployment refit. It is
separate from the historical frozen evaluation and final-refit estimators.
Historical equivalence stays NOT VERIFIED; historical Holdout metrics cannot be
attributed to this model. Software fixtures keep `software-test-only` identity.

## Artifacts and trust

[model_store.py](../src/spotify_cluster/model_store.py) writes a new directory
containing `model_bundle.joblib`, `metadata.json`, `cluster_profiles.json`,
`verification_sample.json` and `verification_report.json` for deployment-v1.
Existing directories are refused. An interrupted write is invalid; choose a new
path after inspection rather than overwrite it.

Joblib uses pickle and can execute code. Only load artifacts from an operator
trusted local source. Checksums detect accidental corruption and mismatched
files; they do not authenticate an attacker-controlled directory. Never accept
uploaded bundles. Exact recorded environment versions are required before
deserialization; recreate that environment when versions differ.

Metadata records a new UUID model identity, UTC creation time, input/preparation
fingerprints, explicit parameters, population, versions, counts and bundle hash.
The report hashes bundle, metadata, profiles and sample. Metadata also records
profile and sample hashes, approved profile identity and per-parameter provenance.
Stored sample predictions/distances are checked during loading. The report is not
self-signed. No historical Holdout score is attached to a new estimator.

Select the approved recipe with `--profile deployment-v1` using the command in
[README.md](../README.md). An omitted profile or `historical-final-refit` keeps
the historical gate. New exports always require a new directory. Independent
numerics check full-population medians/IQRs, scaling, centroid assignments and
SSE. The saved private sample contains 32 equally spaced canonical records,
their predictions and both squared and Euclidean distances. It is training
consistency evidence, not an independent evaluation set. Keep it local and ignored.

## Visualization and research artifacts

These are separate offline exports; neither is part of the joblib bundle and
neither trains or alters the model.

- `visualization-v1` (private/local) contains visualization-only PCA coordinates,
  a deterministic stratified 6,000-point sample, raw F9 rows (no identifiers),
  the fitted scaler state for independent projection verification, and an
  aggregate occupancy grid. See [VISUALIZATION.md](VISUALIZATION.md).
- `visualization-public-v1` contains the aggregate occupancy grid only; no
  per-track coordinates/features. This is the default public deployment mount.
- `research-v1` contains the labeled controlled training-population comparison
  and archived historical evidence; no per-track rows. See [RESEARCH.md](RESEARCH.md).

Each artifact has a `verification_report.json` with a SHA-256 checksum and the
model ID, dataset SHA-256 and prepared fingerprint. The API loader verifies these
before serving; a mismatch marks the feature unavailable rather than mixing
identities. The model and artifact directories are configured by
`SPOTIFY_MODEL_DIR`, `SPOTIFY_VISUALIZATION_DIR` and `SPOTIFY_RESEARCH_DIR`
(absolute paths). Optional artifact failure does not prevent predictions.

The visualization pipeline uses the **fitted deployment scaler** for the scaling
step, fits only a visualization PCA, and verifies assignments against
`KMeans.labels_` and the model profiles. It never fits a new clustering estimator.
PCA coordinates are not model training coordinates. Sample points carry no track
identifiers. Public aggregate cells meet a minimum count and are never labeled as
individual tracks.

## Inference interface

Use the local verified deployment bundle:

```python
from pathlib import Path
from spotify_cluster.inference import InferenceService

service = InferenceService(Path("artifacts/deployment-v1"))
features = {
    "acousticness": 0.1, "danceability": 0.6, "energy": 0.7,
    "valence": 0.5, "tempo": 120.0, "loudness": -8.0,
    "speechiness": 0.05, "instrumentalness": 0.0, "liveness": 0.1,
}
result = service.predict_one(features)
results = service.predict_batch([features, features])
```

The illustrative mapping above is usage documentation, not research evidence.
Actual-model acceptance checks use private real verification records.

To inspect aggregate profiles locally:

```python
import json
profiles = json.loads(Path("artifacts/deployment-v1/cluster_profiles.json").read_text())
print(profiles["clusters"])
print(profiles["feature_contributions"])
```

Mappings may arrive in any key order. Values must be finite real numbers;
booleans and numeric strings are rejected. Bounded descriptors use [0, 1],
tempo may be zero but not negative, and loudness has no extra bound in the
notebook. Missing/extra fields and empty batches raise ValueError. Input is
never clipped or imputed.

Each result contains the model ID, cluster ID, distances in centroid order
[0, 1], distance definition, matching profile, reconstruction status and
scientific limitations. These distances are Euclidean in fitted RobustScaler
space; they are not calibrated confidence. Returned profiles are defensive
copies. Prediction reuses fitted state and requires no CSV or notebook access.

Profiles include count/share and raw-unit mean, median, sample standard
deviation, quartiles and IQR. A singleton's standard deviation is explicitly
represented as zero. Interpret labels from their current profiles; no label
number has a fixed musical meaning.

Feature contributions measure per-feature between-cluster sum of squares in the
actual fitted RobustScaler space over all training assignments. They are new
model measurements, not a copy of the archived instrumentalness percentage.
Clustering does not establish ground-truth genre labels or listening-study
validity.

## Replacement and rollback

Prepare a new versioned bundle and matching artifacts under separate
authorization; never overwrite the existing directory. Mount the new paths and
restart the API. The frontend checks model identity and clears stale visualization
or research state when identities differ. Roll back by restoring the previous
mounts and restarting. There is no retraining or Holdout path in serving.
