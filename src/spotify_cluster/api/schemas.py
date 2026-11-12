"""Explicit HTTP contracts; inference owns the audio-feature validation policy."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from spotify_cluster.inference import input_matrix


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Features(Contract):
    acousticness: float
    danceability: float
    energy: float
    valence: float
    tempo: float
    loudness: float
    speechiness: float
    instrumentalness: float
    liveness: float


class Track(Features):
    """Raw F9: bounded descriptors [0,1], tempo >=0, finite loudness unbounded."""

    @model_validator(mode="after")
    def validate_audio_domains(self) -> Self:
        try:
            input_matrix([self.model_dump()])
        except OverflowError as exc:
            raise ValueError("Features must be representable finite numbers") from exc
        return self


class BatchRequest(Contract):
    tracks: Annotated[list[Track], Field(min_length=1, max_length=100)]


class Health(Contract):
    service: str
    version: str
    status: Literal["ready"]
    model_loaded: Literal[True]


class ModelInfo(Contract):
    model_id: str
    deployment_profile: str
    algorithm: Literal["KMeans"]
    number_of_clusters: Literal[2]
    scaler: Literal["RobustScaler"]
    features: list[str]
    training_sample_count: int
    modeling_pca: None
    model_origin: str
    historical_equivalence: Literal["not_verified"]


class ClusterProfile(Contract):
    cluster_id: Literal[0, 1]
    count: int
    share: float
    mean: Features
    median: Features
    std: Features
    q1: Features
    q3: Features
    iqr: Features


class FeatureContributions(Contract):
    definition: str
    population: str
    between_ss: Features
    shares: Features


class Clusters(Contract):
    model_id: str
    units: str
    std_ddof: int
    singleton_std: int
    clusters: dict[str, ClusterProfile]
    feature_contributions: FeatureContributions
    interpretation: str


class Prediction(Contract):
    model_id: str
    cluster_id: Literal[0, 1]
    distances: Annotated[list[float], Field(min_length=2, max_length=2)]
    distance_definition: str
    profile: ClusterProfile
    limitation: str
    reconstruction_status: str
    deployment_profile: str
    historical_equivalence: Literal["not_verified"]


class BatchResponse(Contract):
    predictions: list[Prediction]


class VisualizationUnavailable(Contract):
    available: Literal[False]
    reason: str


class PcaView(Contract):
    explained_variance_ratio: Annotated[list[float], Field(min_length=3, max_length=3)]
    cumulative_explained_variance: Annotated[
        list[float], Field(min_length=3, max_length=3)
    ]
    scope: str


class PcaMeta(PcaView):
    n_components: Literal[3]
    fit_representation: str
    components: Annotated[list[list[float]], Field(min_length=3, max_length=3)]
    sign_convention: str


class Population(Contract):
    training_sample_count: int
    cluster_counts: Annotated[list[int], Field(min_length=2, max_length=2)]
    cluster_shares: Annotated[list[float], Field(min_length=2, max_length=2)]


class SampleMeta(Contract):
    policy: str
    seed: int
    per_cluster_cap: int
    size: int
    cluster_counts: Annotated[list[int], Field(min_length=2, max_length=2)]
    population_cluster_counts: Annotated[list[int], Field(min_length=2, max_length=2)]
    proportions_disclosure: str


class Views(Contract):
    points: bool
    density: bool


class License(Contract):
    name: str
    license: str
    url: str
    redistribution: str


class VisualizationMeta(Contract):
    available: Literal[True]
    schema_version: int
    artifact_kind: str
    artifact_mode: Literal["points", "aggregate"]
    model_id: str
    deployment_profile: str
    dataset_sha256: str
    prepared_fingerprint: str
    preparation_version: str | None
    created_at: str
    features: list[str]
    population: Population
    pca: PcaMeta
    sample: SampleMeta
    views: Views
    software: dict[str, str]
    license: License
    limitations: str
    historical_equivalence: Literal["NOT VERIFIED"]
    model_origin: str | None


class OccupancyCell(Contract):
    x: float
    y: float
    count: int
    cluster1_share: float
    mean_instrumentalness: float


class Occupancy(Contract):
    definition: str
    bins: int
    min_cell_count: int
    x_range: Annotated[list[float], Field(min_length=2, max_length=2)]
    y_range: Annotated[list[float], Field(min_length=2, max_length=2)]
    cells: list[OccupancyCell]


class Points(Contract):
    x: list[float]
    y: list[float]
    z: list[float]
    cluster: list[int]
    raw_features: list[list[float]]

    @model_validator(mode="after")
    def validate_arrays(self) -> Self:
        size = len(self.x)
        if size < 2 or not (
            len(self.y)
            == len(self.z)
            == len(self.cluster)
            == len(self.raw_features)
            == size
        ):
            raise ValueError("Point arrays must share one length")
        if any(label not in (0, 1) for label in self.cluster):
            raise ValueError("Invalid point cluster")
        if any(len(row) != 9 for row in self.raw_features):
            raise ValueError("Points must carry nine acoustic features")
        return self


class PointsView(Contract):
    model_id: str
    view: Literal["points"]
    features: list[str]
    pca: PcaView
    population: Population
    sample: SampleMeta
    points: Points
    occupancy: Occupancy
    limitations: str
    historical_equivalence: Literal["NOT VERIFIED"]


class OccupancyView(Contract):
    model_id: str
    view: Literal["density"]
    features: list[str]
    pca: PcaView
    population: Population
    occupancy: Occupancy
    limitations: str
    historical_equivalence: Literal["NOT VERIFIED"]


class PointInfo(Contract):
    index: int
    cluster: Literal[0, 1]
    coordinates: Annotated[list[float], Field(min_length=3, max_length=3)]
    features: Features


class NeighborInfo(PointInfo):
    distance: float


class Neighbours(Contract):
    model_id: str
    selection: str
    distance_definition: str
    sample_size: int
    point: PointInfo
    neighbors: list[NeighborInfo]
    historical_equivalence: Literal["NOT VERIFIED"]


class ResearchUnavailable(Contract):
    available: Literal[False]
    reason: str


class F5Comparison(Contract):
    definition: str
    identical_track_ids: Literal[True]
    f5_features: list[str]
    f5_recipe: dict
    deployment_recipe: dict
    ari: float
    f5_cluster_counts: list[int]
    deployment_cluster_counts: list[int]
    interpretation: str


class GmmComparison(Contract):
    definition: str
    identical_track_ids: Literal[True]
    representation: str
    gmm_recipe: dict
    ari: float
    gmm_hard_cluster_counts: list[int]
    mean_max_responsibility: float
    mean_entropy_nats: float
    soft_assignment_definition: str
    interpretation: str


class Comparisons(Contract):
    f5_kmeans_vs_deployment_f9_kmeans: F5Comparison
    f9_kmeans_vs_f9_gmm: GmmComparison


class ArchivedEvidence(Contract):
    label: Literal["Archived historical FULL research evidence"]
    source: str
    scope: str
    status: Literal["ARCHIVED; NOT RECOMPUTED; HOLDOUT CLOSED"]
    holdout_silhouette: float
    holdout_davies_bouldin: float
    holdout_calinski_harabasz: float
    warning: str


class ResearchComparison(Contract):
    available: Literal[True]
    schema_version: int
    artifact_kind: str
    created_at: str
    model_id: str
    deployment_profile: str
    dataset_sha256: str
    prepared_fingerprint: str
    preparation_version: str | None
    features: list[str]
    population: Population
    scope: str
    comparisons: Comparisons
    archived_evidence: ArchivedEvidence
    software: dict[str, str]
    license: License
    limitations: str
    historical_equivalence: Literal["NOT VERIFIED"]
    holdout_evaluated: Literal[False]


VisualizationMetaResponse = VisualizationUnavailable | VisualizationMeta
ResearchResponse = ResearchUnavailable | ResearchComparison
