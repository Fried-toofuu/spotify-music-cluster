"""Local REST application: trusted loading in lifespan, never at import time."""

import logging
import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from importlib.metadata import version
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from spotify_cluster.config import DEPLOYMENT_V1, F9
from spotify_cluster.inference import InferenceService
from spotify_cluster.research import load_comparison
from spotify_cluster.visualization import (
    load_visualization,
    occupancy_view,
    points_view,
    public_meta,
)

from .routes import cluster_info, model_info, router
from .schemas import (
    OccupancyView,
    PointsView,
    ResearchComparison,
    VisualizationMeta,
)

logger = logging.getLogger(__name__)
_UNSET = object()
_MAX_BODY_BYTES = 64 * 1024


class BodyLimitMiddleware:
    """Buffer and cap HTTP request bodies, including chunked requests."""

    def __init__(self, app, max_bytes: int = _MAX_BODY_BYTES):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        body = b""
        more = True
        while more:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue
            body += message.get("body", b"")
            more = message.get("more_body", False)
            if len(body) > self.max_bytes:
                response = JSONResponse(
                    status_code=413, content={"detail": "Request body too large"}
                )
                await response(scope, receive, send)
                return
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.disconnect"}

        await self.app(scope, replay, send)


def _validated_visualization(payload: dict) -> dict:
    """Validate the exact public view before an artifact can become available."""
    VisualizationMeta(**{"available": True, **public_meta(payload)})
    if payload.get("artifact_mode") == "points":
        PointsView(**points_view(payload))
    else:
        OccupancyView(**occupancy_view(payload))
    return payload


def _validated_research(payload: dict) -> dict:
    ResearchComparison(**{"available": True, **payload})
    return payload


def resolve_model_dir(model_dir: Path | None = None) -> Path:
    configured = (
        model_dir if model_dir is not None else os.environ.get("SPOTIFY_MODEL_DIR")
    )
    if configured is not None:
        path = Path(configured).expanduser()
        if not path.is_absolute():
            raise ValueError("SPOTIFY_MODEL_DIR/model_dir must be an absolute path")
        return path.resolve()
    # Only the source checkout has this default. Wheels require operator configuration.
    root = Path(__file__).resolve().parents[3]
    if (
        Path(__file__).resolve().parent.parent.parent.name != "src"
        or not (root / "pyproject.toml").is_file()
    ):
        raise ValueError(
            "Set SPOTIFY_MODEL_DIR to a trusted absolute artifact directory"
        )
    return root / "artifacts" / "deployment-v1"


def resolve_optional_dir(
    configured: Path | None | object, env_name: str, default_name: str
) -> Path | None:
    """Resolve an optional artifact directory; absence is not a readiness failure."""
    if configured is None:
        return None
    if configured is _UNSET:
        value = os.environ.get(env_name)
        if value is not None:
            configured = Path(value).expanduser()
        else:
            root = Path(__file__).resolve().parents[3]
            if (
                Path(__file__).resolve().parent.parent.parent.name != "src"
                or not (root / "pyproject.toml").is_file()
            ):
                return None
            return root / "artifacts" / default_name
    path = Path(configured).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{env_name}/artifact directory must be an absolute path")
    return path.resolve()


def _load_optional(
    label: str,
    loader,
    configured: Path | None | object,
    env_name: str,
    default_name: str,
):
    try:
        directory = resolve_optional_dir(configured, env_name, default_name)
        if directory is None or not directory.is_dir():
            return None, f"{label} artifact not provisioned"
        return loader(directory), None
    except Exception as exc:
        logger.warning("%s artifact unavailable: %s", label, type(exc).__name__)
        return None, f"{label} artifact failed verification; inspect server logs"


def create_app(
    model_dir: Path | None = None,
    *,
    service_factory: Callable[[Path], InferenceService] | None = None,
    visualization_dir: Path | None | object = _UNSET,
    research_dir: Path | None | object = _UNSET,
) -> FastAPI:
    """An explicit factory seam allows software doubles; production has no fallback."""

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.inference_service = None
        application.state.visualization = None
        application.state.visualization_reason = (
            "Visualization artifact not provisioned"
        )
        application.state.research = None
        application.state.research_reason = "Research comparison not provisioned"
        try:
            service = (service_factory or InferenceService)(
                resolve_model_dir(model_dir)
            )
            metadata = service.metadata
            if (
                metadata["features"] != list(F9)
                or metadata["deployment_profile"] != DEPLOYMENT_V1.identifier
                or metadata["model_origin"] != "new_deployment_refit"
                or metadata["reconstruction_status"] != "new_deployment_refit"
            ):
                raise ValueError("API requires a verified deployment-v1 model")
            # Validate the safe response views before readiness can succeed.
            model_info(service)
            cluster_info(service)
        except Exception:
            logger.exception("Trusted deployment model initialization failed")
            raise RuntimeError(
                "Model initialization failed; check trusted artifact configuration "
                "and integrity in server logs"
            ) from None
        application.state.inference_service = service
        public_mode = os.environ.get("SPOTIFY_PUBLIC_MODE", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        if metadata.get("dataset_sha256") and metadata.get("prepared_fingerprint"):
            visualization, visualization_reason = _load_optional(
                "Visualization",
                lambda directory: _validated_visualization(
                    load_visualization(
                        directory,
                        expected_model_id=metadata["model_id"],
                        expected_dataset_sha256=metadata["dataset_sha256"],
                        expected_fingerprint=metadata["prepared_fingerprint"],
                    )
                ),
                visualization_dir,
                "SPOTIFY_VISUALIZATION_DIR",
                "visualization-v1",
            )
            research, research_reason = _load_optional(
                "Research comparison",
                lambda directory: _validated_research(
                    load_comparison(
                        directory,
                        expected_model_id=metadata["model_id"],
                        expected_dataset_sha256=metadata["dataset_sha256"],
                        expected_fingerprint=metadata["prepared_fingerprint"],
                    )
                ),
                research_dir,
                "SPOTIFY_RESEARCH_DIR",
                "research-v1",
            )
        else:
            visualization, visualization_reason = None, "Visualization not applicable"
            research, research_reason = None, "Research comparison not applicable"
        if public_mode and visualization and visualization["artifact_mode"] == "points":
            logger.warning("Public mode refuses a per-track visualization artifact")
            visualization = None
            visualization_reason = "Public mode serves aggregate visualization only"
        application.state.visualization = visualization
        application.state.visualization_reason = (
            visualization_reason or "Visualization unavailable"
        )
        application.state.research = research
        application.state.research_reason = research_reason or "Research unavailable"
        try:
            yield
        finally:
            application.state.inference_service = None
            application.state.visualization = None
            application.state.research = None

    application = FastAPI(
        title="Spotify Music Clustering API",
        version=version("spotify-music-clustering-web"),
        lifespan=lifespan,
        debug=False,
    )
    application.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=6)
    application.add_middleware(BodyLimitMiddleware, max_bytes=_MAX_BODY_BYTES)
    application.include_router(router)

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Default error input/ctx can echo full payloads and non-JSON NaN values.
        errors = [
            {"loc": error["loc"], "type": error["type"], "msg": error["msg"]}
            for error in exc.errors()
        ]
        return JSONResponse(status_code=422, content={"detail": errors})

    @application.exception_handler(Exception)
    async def internal_error(request: Request, exc: Exception):
        logger.error("API request failed: %s", type(exc).__name__)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )

    return application


app = create_app()
