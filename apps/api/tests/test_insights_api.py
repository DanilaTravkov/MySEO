from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_session
from app.main import create_app


@pytest.fixture
def insights_client() -> Iterator[TestClient]:
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
        yield client
    session.close()


def test_dashboard_and_discovery_results_use_latest_completed_run(
    insights_client: TestClient,
) -> None:
    created = insights_client.post(
        "/api/discovery/mock",
        json={"seeds": ["json", "pdf", "resume"], "limit": 30},
    )
    assert created.status_code == 201

    dashboard = insights_client.get("/api/dashboard")
    assert dashboard.status_code == 200
    payload = dashboard.json()
    assert payload["total_discovered_keywords"] == 30
    assert payload["active_opportunities"] == 0
    assert payload["strong_opportunities"] == 0
    assert payload["median_search_volume"] is not None
    assert payload["median_growth"] is not None
    assert payload["last_discovery_run"]["id"] == created.json()["run_id"]
    assert {provider["id"] for provider in payload["providers"]} == {
        "csv",
        "google_ads",
        "mock",
    }

    results = insights_client.get("/api/discovery/results")
    assert results.status_code == 200
    result_payload = results.json()
    assert result_payload["run_id"] == created.json()["run_id"]
    assert len(result_payload["rows"]) == 30
    assert result_payload["rows"][0]["volume"] >= result_payload["rows"][-1]["volume"]
    assert result_payload["rows"][0]["opportunity_score"] is None


def test_keyword_detail_has_twelve_months_and_deterministic_explanation(
    insights_client: TestClient,
) -> None:
    insights_client.post(
        "/api/discovery/mock",
        json={"seeds": ["json"], "limit": 8},
    )
    results = insights_client.get("/api/discovery/results").json()
    keyword_id = results["rows"][0]["id"]

    detail = insights_client.get(f"/api/keywords/{keyword_id}")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["id"] == keyword_id
    assert len(payload["monthly_volumes"]) == 12
    assert payload["current"] is not None
    assert payload["average"] is not None
    assert payload["growth"] is not None
    assert payload["competition"] is not None
    assert payload["bid"] is not None
    assert payload["explanations"]
    assert all("AI" not in explanation for explanation in payload["explanations"])

    missing = insights_client.get(f"/api/keywords/{uuid4()}")
    assert missing.status_code == 404


def test_opportunity_contract_is_empty_before_clustering(insights_client: TestClient) -> None:
    response = insights_client.get("/api/opportunities")
    assert response.status_code == 200
    assert response.json() == []
