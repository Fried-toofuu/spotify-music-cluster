"""Research contracts recovered from the authoritative notebook (zero-based cells)."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

F9 = (
    "acousticness",
    "danceability",
    "energy",
    "valence",
    "tempo",
    "loudness",
    "speechiness",
    "instrumentalness",
    "liveness",
)
BOUNDED = tuple(f for f in F9 if f not in ("tempo", "loudness"))
EXPECTED_SHA256 = "b202fa49909b2d5cef71a04b1d21243cfeb36414535f2ca9272aa646721177bd"
RAW_ROWS = 114_000
TRACK_COUNT = 89_741
GENRE_COUNT = 114
RAW_COLUMNS = (
    "Unnamed: 0",
    "track_id",
    "artists",
    "album_name",
    "track_name",
    "popularity",
    "duration_ms",
    "explicit",
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "time_signature",
    "track_genre",
)
PREPARATION_VERSION = "notebook-track-f9-v1"
SCALER_PARAMS = dict(
    with_centering=True,
    with_scaling=True,
    quantile_range=(25.0, 75.0),
    copy=True,
    unit_variance=False,
)
LIMITATION = (
    "Acoustic clusters are not ground-truth genres. Robust scaling historically "
    "made instrumentalness dominate this representation. Centroid distances are "
    "Euclidean distances in fitted RobustScaler space, not probabilities. "
    "Exact historical model equivalence is NOT VERIFIED."
)
FINAL_CONFIG_BLOCKER = (
    "Final-model export BLOCKED: notebook cells 109-110 record F9/Robust/KMeans/K2 "
    "but no final-refit n_init, max_iter, init, tol or algorithm. Cell 82 defines "
    "a development demonstration (n_init=10 QUICK / 20 FULL); cell 55's "
    "max_iter=400 belongs to the F5 baseline. These cannot establish the archived "
    "final-refit configuration. Supply the original final-refit parameter evidence "
    "before enabling historical reconstruction. Select deployment-v1 explicitly "
    "to train the separately authorized new deployment recipe."
)


def final_kmeans_params() -> dict:
    """Fail closed until material final-refit settings have source evidence."""
    raise RuntimeError(FINAL_CONFIG_BLOCKER)


@dataclass(frozen=True)
class DeploymentProfile:
    """One approved recipe; immutable settings prevent accidental default drift."""

    name: str
    identifier: str
    features: tuple[str, ...]
    scaler_params: Mapping
    kmeans_params: Mapping
    provenance: Mapping


DEPLOYMENT_V1 = DeploymentProfile(
    name="deployment-v1",
    identifier="spotify-f9-robust-kmeans-k2-v1",
    features=F9,
    scaler_params=MappingProxyType(dict(SCALER_PARAMS)),
    kmeans_params=MappingProxyType(
        dict(
            n_clusters=2,
            init="k-means++",
            n_init=20,
            max_iter=300,
            tol=1e-4,
            random_state=42,
            algorithm="lloyd",
            copy_x=True,
            verbose=0,
        )
    ),
    provenance=MappingProxyType(
        {
            "authorization": (
                "User-approved new deployment recipe; historical identity unverified"
            ),
            "features": "Notebook cell 11 and archived selection in cells 109-110",
            "scaler": (
                "Notebook RobustScaler method; explicit user-approved scaler parameters"
            ),
            "n_clusters": "Notebook archived selected K=2, cells 109-110",
            "modeling_pca": "None; notebook archived selected representation",
            "random_state": "Notebook development seed, cell 3",
            "n_init": "Notebook FULL development F9 K-Means example, cell 82",
            "init": "Explicitly adopted scikit-learn 1.6 default",
            "max_iter": "Explicitly adopted scikit-learn 1.6 default",
            "tol": "Explicitly adopted scikit-learn 1.6 default",
            "algorithm": "Explicitly adopted scikit-learn 1.6 default",
            "copy_x": "Explicitly adopted scikit-learn 1.6 default",
            "verbose": "Explicitly adopted scikit-learn 1.6 default",
            "reference": "https://scikit-learn.org/1.6/modules/generated/sklearn.cluster.KMeans.html",
        }
    ),
)


def training_profile(name: str) -> DeploymentProfile:
    """Deployment authorization never implies historical-estimator reconstruction."""
    if name == "historical-final-refit":
        final_kmeans_params()
    if name != DEPLOYMENT_V1.name:
        raise ValueError(f"Unsupported training profile: {name}")
    return DEPLOYMENT_V1
