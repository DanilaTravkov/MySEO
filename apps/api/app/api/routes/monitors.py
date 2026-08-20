from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models import DiscoveryRun, KeywordObservation, MonitorSignal, SearchMonitor
from app.services.monitoring import (
    MonitorProviderUnavailable,
    add_one_month,
    create_monitor,
    run_monitor,
)

router = APIRouter(prefix="/monitors", tags=["monitoring"])


class MonitorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    provider: Literal["mock"] = "mock"
    seeds: list[str] = Field(min_length=1, max_length=50)
    language: str = Field(default="en", min_length=2, max_length=16)
    geo: str = Field(default="US", min_length=2, max_length=16)
    frequency: Literal["manual", "monthly"] = "monthly"
    enabled: bool = True
    limit: int = Field(default=500, ge=10, le=5000)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name cannot be empty.")
        return cleaned

    @field_validator("seeds")
    @classmethod
    def clean_seeds(cls, value: list[str]) -> list[str]:
        cleaned = list(dict.fromkeys(seed.strip() for seed in value if seed.strip()))
        if not cleaned:
            raise ValueError("At least one non-empty seed is required.")
        return cleaned


class MonitorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    seeds: list[str] | None = Field(default=None, min_length=1, max_length=50)
    frequency: Literal["manual", "monthly"] | None = None
    enabled: bool | None = None


class MonitorRunResponse(BaseModel):
    id: UUID
    status: str
    trigger: str
    started_at: datetime | None
    completed_at: datetime | None
    keyword_count: int
    signal_count: int


class SignalResponse(BaseModel):
    id: UUID
    signal_type: str
    severity: str
    title: str
    summary: str
    magnitude: float | None
    created_at: datetime


class MonitorResponse(BaseModel):
    id: UUID
    name: str
    provider: str
    seeds: list[str]
    language: str
    geo: str
    frequency: str
    enabled: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_at: datetime
    run_count: int
    latest_run: MonitorRunResponse | None
    recent_signals: list[SignalResponse]


def _run_response(session: Session, run: DiscoveryRun) -> MonitorRunResponse:
    keyword_count = session.scalar(
        select(func.count())
        .select_from(KeywordObservation)
        .where(KeywordObservation.discovery_run_id == run.id)
    )
    signal_count = session.scalar(
        select(func.count())
        .select_from(MonitorSignal)
        .where(MonitorSignal.current_run_id == run.id)
    )
    return MonitorRunResponse(
        id=run.id,
        status=run.status,
        trigger=run.trigger,
        started_at=run.started_at,
        completed_at=run.completed_at,
        keyword_count=keyword_count or 0,
        signal_count=signal_count or 0,
    )


def _monitor_response(session: Session, monitor: SearchMonitor) -> MonitorResponse:
    runs = session.scalars(
        select(DiscoveryRun)
        .where(DiscoveryRun.monitor_id == monitor.id)
        .order_by(DiscoveryRun.started_at.desc())
    ).all()
    signals = session.scalars(
        select(MonitorSignal)
        .where(MonitorSignal.monitor_id == monitor.id)
        .order_by(MonitorSignal.created_at.desc())
        .limit(8)
    ).all()
    return MonitorResponse(
        id=monitor.id,
        name=monitor.name,
        provider=monitor.provider,
        seeds=list(monitor.seeds_json),
        language=monitor.language,
        geo=monitor.geo,
        frequency=monitor.frequency,
        enabled=monitor.enabled,
        last_run_at=monitor.last_run_at,
        next_run_at=monitor.next_run_at,
        created_at=monitor.created_at,
        run_count=len(runs),
        latest_run=_run_response(session, runs[0]) if runs else None,
        recent_signals=[
            SignalResponse(
                id=signal.id,
                signal_type=signal.signal_type,
                severity=signal.severity,
                title=signal.title,
                summary=signal.summary,
                magnitude=signal.magnitude,
                created_at=signal.created_at,
            )
            for signal in signals
        ],
    )


def _monitor_or_404(session: Session, monitor_id: UUID) -> SearchMonitor:
    monitor = session.get(SearchMonitor, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found.")
    return monitor


@router.get("", response_model=list[MonitorResponse])
def list_monitors(
    session: Annotated[Session, Depends(get_session)],
) -> list[MonitorResponse]:
    monitors = session.scalars(
        select(SearchMonitor).order_by(SearchMonitor.created_at.desc())
    ).all()
    return [_monitor_response(session, monitor) for monitor in monitors]


@router.post("", response_model=MonitorResponse, status_code=status.HTTP_201_CREATED)
def add_monitor(
    payload: MonitorCreate,
    session: Annotated[Session, Depends(get_session)],
) -> MonitorResponse:
    try:
        monitor = create_monitor(session, **payload.model_dump())
    except MonitorProviderUnavailable as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return _monitor_response(session, monitor)


@router.get("/{monitor_id}", response_model=MonitorResponse)
def get_monitor(
    monitor_id: UUID,
    session: Annotated[Session, Depends(get_session)],
) -> MonitorResponse:
    return _monitor_response(session, _monitor_or_404(session, monitor_id))


@router.patch("/{monitor_id}", response_model=MonitorResponse)
def update_monitor(
    monitor_id: UUID,
    payload: MonitorUpdate,
    session: Annotated[Session, Depends(get_session)],
) -> MonitorResponse:
    monitor = _monitor_or_404(session, monitor_id)
    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes:
        monitor.name = str(changes["name"]).strip()
    if "seeds" in changes:
        seeds = list(dict.fromkeys(seed.strip() for seed in changes["seeds"] if seed.strip()))
        if not seeds:
            raise HTTPException(status_code=422, detail="At least one seed is required.")
        monitor.seeds_json = seeds
    if "frequency" in changes:
        monitor.frequency = str(changes["frequency"])
    if "enabled" in changes:
        monitor.enabled = bool(changes["enabled"])
    if monitor.enabled and monitor.frequency == "monthly" and monitor.next_run_at is None:
        monitor.next_run_at = add_one_month(datetime.now(UTC))
    if not monitor.enabled or monitor.frequency == "manual":
        monitor.next_run_at = None
    session.commit()
    return _monitor_response(session, monitor)


@router.post(
    "/{monitor_id}/runs",
    response_model=MonitorRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_monitor_now(
    monitor_id: UUID,
    session: Annotated[Session, Depends(get_session)],
) -> MonitorRunResponse:
    _monitor_or_404(session, monitor_id)
    try:
        result = await run_monitor(session, monitor_id)
    except MonitorProviderUnavailable as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    run = session.get(DiscoveryRun, result.run_id)
    assert run is not None
    return _run_response(session, run)


@router.get("/{monitor_id}/runs", response_model=list[MonitorRunResponse])
def list_monitor_runs(
    monitor_id: UUID,
    session: Annotated[Session, Depends(get_session)],
) -> list[MonitorRunResponse]:
    _monitor_or_404(session, monitor_id)
    runs = session.scalars(
        select(DiscoveryRun)
        .where(DiscoveryRun.monitor_id == monitor_id)
        .order_by(DiscoveryRun.started_at.desc())
    ).all()
    return [_run_response(session, run) for run in runs]
