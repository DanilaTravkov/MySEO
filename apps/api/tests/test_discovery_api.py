from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.models import (
    Cluster,
    ClusterKeyword,
    DiscoveryRun,
    Keyword,
    KeywordAnalysis,
    KeywordObservation,
    MonthlySearchVolume,
)


@pytest.fixture
def discovery_client() -> Iterator[tuple[TestClient, Session]]:
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


def test_mock_discovery_persists_provider_data(
    discovery_client: tuple[TestClient, Session],
) -> None:
    client, session = discovery_client

    response = client.post(
        "/api/discovery/mock",
        json={"seeds": ["json", "pdf"], "language": "en", "geo": "US", "limit": 24},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "completed"
    assert response.json()["keyword_count"] == 24
    assert response.json()["monthly_volume_count"] == 24 * 12
    assert response.json()["cluster_count"] > 0
    assert session.scalar(select(func.count()).select_from(DiscoveryRun)) == 1
    assert session.scalar(select(func.count()).select_from(Keyword)) == 24
    assert session.scalar(select(func.count()).select_from(KeywordObservation)) == 24
    assert session.scalar(select(func.count()).select_from(MonthlySearchVolume)) == 24 * 12
    assert session.scalar(select(func.count()).select_from(KeywordAnalysis)) == 24
    assert session.scalar(select(func.count()).select_from(Cluster)) > 0
    assert session.scalar(select(func.count()).select_from(ClusterKeyword)) == 24

    distribution = client.get("/api/distributions?metric=avg_monthly_searches")
    assert distribution.status_code == 200
    assert distribution.json()["diagnostics"]["sample_size"] == 24
    assert distribution.json()["normal_fit_label"] == "Normal fit"
    assert distribution.json()["qq_points"]

    recalculated = client.post(f"/api/analytics/runs/{response.json()['run_id']}")
    assert recalculated.status_code == 200
    assert recalculated.json()["analysis_count"] == 24
    assert session.scalar(select(func.count()).select_from(KeywordAnalysis)) == 24


def test_csv_discovery_upload_and_controlled_validation_error(
    discovery_client: tuple[TestClient, Session],
) -> None:
    client, session = discovery_client
    valid_csv = (
        "keyword,year,month,searches,competition_index,low_bid,high_bid\n"
        "json formatter,2026,1,12000,55,0.8,2.1\n"
        "json formatter,2026,2,14000,57,0.9,2.3\n"
        "pdf compressor,2026,1,8000,42,1.2,3.4\n"
    )

    response = client.post(
        "/api/discovery/csv",
        files={"file": ("keywords.csv", valid_csv, "text/csv")},
        data={"language": "en", "geo": "US", "currency": "USD"},
    )

    assert response.status_code == 201
    assert response.json()["keyword_count"] == 2
    assert response.json()["monthly_volume_count"] == 3
    assert session.scalar(select(func.count()).select_from(KeywordObservation)) == 2

    invalid = client.post(
        "/api/discovery/csv",
        files={"file": ("invalid.csv", "keyword,year\njson,2026\n", "text/csv")},
    )
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["code"] == "csv_validation_failed"
    assert "Missing required column" in invalid.json()["detail"]["issues"][0]["message"]
