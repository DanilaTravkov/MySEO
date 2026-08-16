from fastapi.testclient import TestClient

from app.db.session import database_is_ready
from app.main import create_app


def test_health_returns_success_when_database_is_ready() -> None:
    app = create_app()
    app.dependency_overrides[database_is_ready] = lambda: True

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "database": "ready",
        "version": "0.1.0",
    }


def test_health_reports_degraded_database() -> None:
    app = create_app()
    app.dependency_overrides[database_is_ready] = lambda: False

    response = TestClient(app).get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
