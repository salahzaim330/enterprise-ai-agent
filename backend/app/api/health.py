"""Route de santé : état de l'API et de ses dépendances."""

from typing import Literal

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app import __version__
from app.core.config import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    environment: str
    dependencies: dict[str, Literal["up", "down"]]


async def check_qdrant(url: str, timeout: float = 2.0) -> bool:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url.rstrip('/')}/healthz")
    except httpx.HTTPError:
        return False
    return response.status_code == httpx.codes.OK


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:  # noqa: B008
    qdrant_up = await check_qdrant(settings.qdrant_url)
    return HealthResponse(
        status="ok" if qdrant_up else "degraded",
        version=__version__,
        environment=settings.environment,
        dependencies={"qdrant": "up" if qdrant_up else "down"},
    )
