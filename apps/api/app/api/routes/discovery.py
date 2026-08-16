from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.providers.csv_provider import CsvSearchDataProvider, CsvValidationError
from app.providers.mock import MOCK_DATASET_SIZE, MockSearchDataProvider
from app.services.discovery import DiscoveryResult, run_discovery

router = APIRouter(prefix="/discovery", tags=["discovery"])
MAX_CSV_BYTES = 5 * 1024 * 1024


class MockDiscoveryRequest(BaseModel):
    seeds: list[str] = Field(min_length=1, max_length=50)
    language: str = Field(default="en", min_length=2, max_length=16)
    geo: str = Field(default="US", min_length=2, max_length=16)
    limit: int = Field(default=MOCK_DATASET_SIZE, ge=1, le=5000)

    @field_validator("seeds")
    @classmethod
    def validate_seeds(cls, value: list[str]) -> list[str]:
        clean = [seed.strip() for seed in value if seed.strip()]
        if not clean:
            raise ValueError("At least one non-empty seed is required.")
        return clean


class DiscoveryRunResponse(BaseModel):
    run_id: UUID
    provider: str
    status: str
    keyword_count: int
    observation_count: int
    monthly_volume_count: int
    cluster_count: int
    sample_keywords: list[str]


def _response(result: DiscoveryResult) -> DiscoveryRunResponse:
    return DiscoveryRunResponse(
        run_id=result.run_id,
        provider=result.provider,
        status=result.status,
        keyword_count=result.keyword_count,
        observation_count=result.observation_count,
        monthly_volume_count=result.monthly_volume_count,
        cluster_count=result.cluster_count,
        sample_keywords=list(result.sample_keywords),
    )


@router.post("/mock", response_model=DiscoveryRunResponse, status_code=status.HTTP_201_CREATED)
async def discover_with_mock(
    request: MockDiscoveryRequest,
    session: Annotated[Session, Depends(get_session)],
) -> DiscoveryRunResponse:
    result = await run_discovery(
        session,
        MockSearchDataProvider(),
        provider_id="mock",
        seeds=request.seeds,
        language=request.language,
        geo=request.geo,
        limit=request.limit,
    )
    return _response(result)


@router.post("/csv", response_model=DiscoveryRunResponse, status_code=status.HTTP_201_CREATED)
async def discover_with_csv(
    session: Annotated[Session, Depends(get_session)],
    file: Annotated[UploadFile, File(description="UTF-8 CSV containing historical metrics")],
    language: Annotated[str, Form(min_length=2, max_length=16)] = "en",
    geo: Annotated[str, Form(min_length=2, max_length=16)] = "US",
    currency: Annotated[str, Form(min_length=3, max_length=3)] = "USD",
) -> DiscoveryRunResponse:
    content = await file.read(MAX_CSV_BYTES + 1)
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail={"code": "csv_too_large", "message": "CSV must not exceed 5 MiB."},
        )
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "invalid_encoding", "message": "CSV must use UTF-8 encoding."},
        ) from error

    try:
        provider = CsvSearchDataProvider(decoded, currency=currency)
    except CsvValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "csv_validation_failed",
                "issues": [asdict(issue) for issue in error.issues],
            },
        ) from error

    result = await run_discovery(
        session,
        provider,
        provider_id="csv",
        seeds=[],
        language=language,
        geo=geo,
        limit=5000,
        config={"filename": file.filename or "upload.csv", "currency": currency.upper()},
    )
    return _response(result)
