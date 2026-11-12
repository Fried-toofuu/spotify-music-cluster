"""Versioned REST routes over the existing inference service."""

from importlib.metadata import version

from fastapi import APIRouter, HTTPException, Query, Request

from spotify_cluster.visualization import (
    neighbours,
    occupancy_view,
    points_view,
    public_meta,
)

from .dependencies import Service
from .schemas import (
    BatchRequest,
    BatchResponse,
    Clusters,
    Health,
    ModelInfo,
    Neighbours,
    OccupancyView,
    PointsView,
    Prediction,
    ResearchResponse,
    Track,
    VisualizationMetaResponse,
)

router = APIRouter(
    prefix="/api/v1", responses={503: {"description": "Model unavailable"}}
)


def model_info(service) -> ModelInfo:
    metadata = service.metadata
    # The bundle loader enforces these estimator types; select only public fields.
    return ModelInfo(
        **{
            name: metadata[name]
            for name in ModelInfo.model_fields
            if name not in {"algorithm", "scaler", "historical_equivalence"}
        },
        algorithm="KMeans",
        scaler="RobustScaler",
        historical_equivalence=historical_status(metadata["historical_equivalence"]),
    )


def historical_status(value: str) -> str:
    if value != "NOT VERIFIED":
        raise ValueError("Unsupported historical-equivalence claim")
    return "not_verified"


def cluster_info(service) -> Clusters:
    profiles = service.profiles
    if profiles["model_id"] != service.metadata["model_id"]:
        raise ValueError("Cluster-profile model identity mismatch")
    shares = profiles["feature_contributions"]["shares"]
    dominant = max(shares, key=shares.get)
    interpretation = (
        f"Largest between-cluster SS contribution: {dominant} "
        f"({shares[dominant]:.3%}) in fitted RobustScaler space. "
        "Interpret each label using its current raw-unit feature statistics. "
        "Labels are arbitrary acoustic groups, not ground-truth genres or moods. "
        "Training-population description only; no independent Holdout evaluation."
    )
    return Clusters(
        **{
            name: profiles[name]
            for name in Clusters.model_fields
            if name != "interpretation"
        },
        interpretation=interpretation,
    )


def prediction_info(result: dict) -> Prediction:
    return Prediction(
        **{
            name: result[name]
            for name in Prediction.model_fields
            if name != "historical_equivalence"
        },
        historical_equivalence=historical_status(result["historical_equivalence"]),
    )


@router.get("/health", response_model=Health)
def health(service: Service):
    return Health(
        service="spotify-music-clustering-web",
        version=version("spotify-music-clustering-web"),
        status="ready",
        model_loaded=True,
    )


@router.get("/model", response_model=ModelInfo)
def model(service: Service):
    return model_info(service)


@router.get("/clusters", response_model=Clusters)
def clusters(service: Service):
    return cluster_info(service)


@router.post("/predict", response_model=Prediction)
def predict(track: Track, service: Service):
    return prediction_info(service.predict_one(track.model_dump()))


@router.post("/predict/batch", response_model=BatchResponse)
def predict_batch(batch: BatchRequest, service: Service):
    results = service.predict_batch([track.model_dump() for track in batch.tracks])
    return BatchResponse(predictions=[prediction_info(result) for result in results])


def _optional_artifact(request: Request, attribute: str, reason_attribute: str):
    payload = getattr(request.app.state, attribute, None)
    if payload is None:
        raise HTTPException(
            status_code=404,
            detail=getattr(
                request.app.state, reason_attribute, "Visualization data unavailable"
            ),
        )
    return payload


@router.get("/visualization/meta", response_model=VisualizationMetaResponse)
def visualization_meta(request: Request):
    payload = getattr(request.app.state, "visualization", None)
    if payload is None:
        return {
            "available": False,
            "reason": getattr(
                request.app.state, "visualization_reason", "Visualization unavailable"
            ),
        }
    return {"available": True, **public_meta(payload)}


@router.get("/visualization/points", response_model=PointsView)
def visualization_points(request: Request):
    payload = _optional_artifact(request, "visualization", "visualization_reason")
    try:
        return points_view(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.get("/visualization/occupancy", response_model=OccupancyView)
def visualization_occupancy(request: Request):
    payload = _optional_artifact(request, "visualization", "visualization_reason")
    return occupancy_view(payload)


@router.get("/visualization/neighbors", response_model=Neighbours)
def visualization_neighbors(
    request: Request,
    index: int = Query(ge=0),
    k: int = Query(default=8, ge=1, le=12),
):
    payload = _optional_artifact(request, "visualization", "visualization_reason")
    if payload.get("artifact_mode") != "points":
        raise HTTPException(
            status_code=404,
            detail="Track-level neighbors are unavailable in aggregate mode",
        )
    try:
        return neighbours(payload, index, k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


@router.get("/research/comparison", response_model=ResearchResponse)
def research_comparison(request: Request):
    payload = getattr(request.app.state, "research", None)
    if payload is None:
        return {
            "available": False,
            "reason": getattr(
                request.app.state, "research_reason", "Research comparison unavailable"
            ),
        }
    return {"available": True, **payload}
