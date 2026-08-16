from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from app.db.session import database_is_ready

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str


@router.get("/health", response_model=HealthResponse)
def health(
    response: Response,
    database_ready: Annotated[bool, Depends(database_is_ready)],
) -> HealthResponse:
    if not database_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="degraded", database="unavailable", version="0.1.0")
    return HealthResponse(status="success", database="ready", version="0.1.0")

