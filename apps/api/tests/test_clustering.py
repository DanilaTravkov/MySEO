from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.clustering.service import cluster_texts, normalize_cluster_text
from app.db.base import Base
from app.db.session import get_session
from app.main import create_app


def test_normalization_and_reference_zod_keywords_cluster_together() -> None:
    assert normalize_cluster_text("  JSON—to   Zod! ") == "json to zod"
    texts = [
        "json to zod",
        "json to zod schema",
        "generate zod from json",
        "convert json zod",
        "pdf compressor",
    ]

    result = cluster_texts(texts, similarity_threshold=0.15)

    assert len(set(result.labels[:4])) == 1
    assert result.labels[4] != result.labels[0]
    assert result.similarities.shape == (5, 5)


@pytest.fixture
def clustering_client() -> Iterator[TestClient]:
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


def test_cluster_api_exposes_aggregate_metrics_and_is_recalculable(
    clustering_client: TestClient,
) -> None:
    discovery = clustering_client.post(
        "/api/discovery/mock",
        json={"seeds": ["json", "pdf"], "limit": 24},
    )
    assert discovery.status_code == 201
    run_id = discovery.json()["run_id"]

    clusters = clustering_client.get(f"/api/clusters?run_id={run_id}")
    assert clusters.status_code == 200
    payload = clusters.json()
    assert payload
    assert sum(cluster["keyword_count"] for cluster in payload) == 24
    assert all(cluster["total_volume"] >= 0 for cluster in payload)
    assert all(
        cluster["demand_label"] == "Aggregated search-demand signal"
        for cluster in payload
    )

    recalculated = clustering_client.post(
        f"/api/clustering/runs/{run_id}?similarity_threshold=0.2"
    )
    assert recalculated.status_code == 200
    assert recalculated.json()["similarity_threshold"] == 0.2
    assert recalculated.json()["keyword_count"] == 24
