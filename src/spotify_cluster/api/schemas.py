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
