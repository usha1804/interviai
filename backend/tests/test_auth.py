import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.models import User
from app.routes.auth import router as auth_router
from app.utils.auth import verify_password


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(auth_router)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client, test_session

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def register(client):
    return client.post(
        "/auth/register",
        json={
            "name": "Auth Test User",
            "email": "auth-test@example.com",
            "password": "test-password-123",
        },
    )


def test_registration_hashes_password_and_returns_tokens(client):
    http, test_session = client

    response = register(http)

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]

    with test_session() as db:
        user = db.query(User).filter(User.email == "auth-test@example.com").one()
        assert user.password != "test-password-123"
        assert user.password.startswith("$2")
        assert verify_password("test-password-123", user.password)
        assert user.is_active is True
        assert user.role == "USER"


def test_registration_and_login_normalize_email_whitespace_consistently(client):
    http, test_session = client
    response = http.post(
        "/auth/register",
        json={
            "name": "Auth Test User",
            "email": "  auth-test@example.com  ",
            "password": "test-password-123",
        },
    )
    assert response.status_code == 200
    with test_session() as db:
        assert db.query(User).filter(User.email == "auth-test@example.com").one()

    login_response = http.post(
        "/auth/login",
        json={"email": "  auth-test@example.com  ", "password": "test-password-123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["access_token"]


def test_successful_login_returns_tokens(client):
    http, _ = client
    assert register(http).status_code == 200

    response = http.post(
        "/auth/login",
        json={"email": "auth-test@example.com", "password": "test-password-123"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]
    assert response.json()["token_type"] == "bearer"


def test_login_rejects_incorrect_password(client):
    http, _ = client
    assert register(http).status_code == 200

    response = http.post(
        "/auth/login",
        json={"email": "auth-test@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_rejects_nonexistent_account(client):
    response = client[0].post(
        "/auth/login",
        json={"email": "missing@example.com", "password": "test-password-123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"password": "test-password-123"}, "email"),
        ({"email": "auth-test@example.com"}, "password"),
        ({"email": "not-an-email", "password": "test-password-123"}, "email"),
        ({"email": "user@domain", "password": "test-password-123"}, "email"),
        ({"email": "   ", "password": "test-password-123"}, "email"),
        ({"email": "auth-test@example.com", "password": "   "}, "password"),
    ],
)
def test_login_returns_field_validation_errors(client, payload, field):
    response = client[0].post("/auth/login", json=payload)

    assert response.status_code == 422
    details = response.json()["detail"]
    assert any(field in error["loc"] for error in details)
