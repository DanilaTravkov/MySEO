from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.models import DiscoveryRun, KeywordObservation, MonitorSignal, SearchMonitor
from app.services.monitoring import as_utc, claim_due_monitors, detect_monitor_signals


@pytest.fixture
def monitor_client() -> Iterator[tuple[TestClient, Session]]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)
    app = create_app()

    def override_session() -> Iterator[Session]:
        yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client, session
    session.close()


def create_demo_monitor(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/monitors",
        json={
            "name": "AI meeting assistants",
            "provider": "mock",
            "seeds": ["ai meeting notes", "meeting transcription"],
            "language": "en",
            "geo": "US",
            "frequency": "monthly",
            "limit": 24,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_monitor_lifecycle_reuses_discovery_pipeline(
    monitor_client: tuple[TestClient, Session],
) -> None:
    client, session = monitor_client
    monitor = create_demo_monitor(client)

    assert monitor["frequency"] == "monthly"
    assert monitor["next_run_at"] is not None
    assert monitor["run_count"] == 0

    first = client.post(f"/api/monitors/{monitor['id']}/runs")
    assert first.status_code == 201
    assert first.json()["keyword_count"] == 24
    assert first.json()["signal_count"] == 0

    second = client.post(f"/api/monitors/{monitor['id']}/runs")
    assert second.status_code == 201
    assert second.json()["signal_count"] == 0

    detail = client.get(f"/api/monitors/{monitor['id']}").json()
    assert detail["run_count"] == 2
    assert detail["latest_run"]["status"] == "completed"
    assert session.scalar(select(func.count()).select_from(SearchMonitor)) == 1
    assert session.scalar(select(func.count()).select_from(DiscoveryRun)) == 2


def test_change_detection_records_derived_signals(
    monitor_client: tuple[TestClient, Session],
) -> None:
    client, session = monitor_client
    monitor_payload = create_demo_monitor(client)
    monitor_id = UUID(str(monitor_payload["id"]))
    client.post(f"/api/monitors/{monitor_id}/runs")
    client.post(f"/api/monitors/{monitor_id}/runs")

    runs = session.scalars(
        select(DiscoveryRun)
        .where(DiscoveryRun.monitor_id == monitor_id)
        .order_by(DiscoveryRun.started_at)
    ).all()
    current_observation = session.scalar(
        select(KeywordObservation).where(KeywordObservation.discovery_run_id == runs[1].id)
    )
    assert current_observation is not None
    current_observation.avg_monthly_searches = (
        (current_observation.avg_monthly_searches or 1) * 2 + 10_000
    )
    monitor = session.get(SearchMonitor, monitor_id)
    assert monitor is not None

    count = detect_monitor_signals(session, monitor, runs[0], runs[1])
    session.commit()

    assert count >= 1
    assert session.scalar(
        select(func.count())
        .select_from(MonitorSignal)
        .where(MonitorSignal.signal_type == "demand_growth")
    ) == 1


def test_scheduler_claims_due_monitors_once(
    monitor_client: tuple[TestClient, Session],
) -> None:
    client, session = monitor_client
    monitor_payload = create_demo_monitor(client)
    monitor = session.get(SearchMonitor, UUID(str(monitor_payload["id"])))
    assert monitor is not None
    monitor.next_run_at = datetime.now(UTC) - timedelta(minutes=1)
    session.commit()

    claimed = claim_due_monitors(session)
    claimed_again = claim_due_monitors(session)

    assert [item.monitor_id for item in claimed] == [monitor.id]
    assert claimed_again == []
    assert monitor.next_run_at is not None
    assert as_utc(monitor.next_run_at) > datetime.now(UTC)
