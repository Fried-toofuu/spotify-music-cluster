"""Local REST application: trusted loading in lifespan, never at import time."""

import logging
import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from importlib.metadata import version
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from spotify_cluster.config import DEPLOYMENT_V1, F9
from spotify_cluster.inference import InferenceService

from .routes import cluster_info, model_info, router

logger = logging.getLogger(__name__)


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


def create_app(
    model_dir: Path | None = None,
    *,
    service_factory: Callable[[Path], InferenceService] | None = None,
) -> FastAPI:
    """An explicit factory seam allows software doubles; production has no fallback."""

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.inference_service = None
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
        try:
            yield
        finally:
            application.state.inference_service = None

    application = FastAPI(
        title="Spotify Music Clustering API",
        version=version("spotify-music-clustering-web"),
        lifespan=lifespan,
        debug=False,
    )
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
