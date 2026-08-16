from fastapi.testclient import TestClient

from app.main import create_app


def test_provider_catalog_is_provider_neutral() -> None:
    response = TestClient(create_app()).get("/api/providers")

    assert response.status_code == 200
    providers = response.json()
    assert [provider["id"] for provider in providers] == ["mock", "csv", "google_ads"]
    assert providers[0]["status"] == "available"
    assert providers[1]["status"] == "available"
    assert providers[2]["status"] == "requires_configuration"
