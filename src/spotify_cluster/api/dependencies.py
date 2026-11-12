"""One application-owned service; no per-request model loading."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request

from spotify_cluster.inference import InferenceService


def get_service(request: Request) -> InferenceService:
    service = getattr(request.app.state, "inference_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="Model service unavailable")
    return service


Service = Annotated[InferenceService, Depends(get_service)]
