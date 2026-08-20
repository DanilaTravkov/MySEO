from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.models.auth import User, UserSession


@pytest.fixture
def auth_client() -> Iterator[tuple[TestClient, Session]]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    database = Session(engine, expire_on_commit=False)
    app = create_app()

    def override_session() -> Iterator[Session]:
        yield database

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client, database
    database.close()


def register(client: TestClient, email: str = "alex@example.com") -> dict[str, object]:
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Alex Morgan",
            "email": email,
            "password": "correct-horse-battery",
            "company": "Acme",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_register_login_profile_and_logout(auth_client: tuple[TestClient, Session]) -> None:
    client, database = auth_client
    registration = register(client)
    token = str(registration["access_token"])
    headers = {"Authorization": f"Bearer {token}"}

    assert registration["user"]["email"] == "alex@example.com"  # type: ignore[index]
    user = database.scalar(select(User).where(User.email == "alex@example.com"))
    assert user is not None
    assert user.password_hash != "correct-horse-battery"
    assert database.scalar(select(UserSession)) is not None

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["full_name"] == "Alex Morgan"

    updated = client.patch(
        "/api/auth/me",
        headers=headers,
        json={"role": "Founder", "experience_level": "advanced"},
    )
    assert updated.status_code == 200
    assert updated.json()["role"] == "Founder"
    assert updated.json()["experience_level"] == "advanced"

    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401

    login = client.post(
        "/api/auth/login",
        json={"email": "ALEX@example.com", "password": "correct-horse-battery"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["email"] == "alex@example.com"


def test_registration_conflict_and_invalid_login(
    auth_client: tuple[TestClient, Session],
) -> None:
    client, _ = auth_client
    register(client)

    duplicate = client.post(
        "/api/auth/register",
        json={
            "full_name": "Another User",
            "email": "alex@example.com",
            "password": "another-secure-password",
        },
    )
    assert duplicate.status_code == 409

    invalid_login = client.post(
        "/api/auth/login",
        json={"email": "alex@example.com", "password": "incorrect-password"},
    )
    assert invalid_login.status_code == 401
    assert invalid_login.json()["detail"] == "Email or password is incorrect."
