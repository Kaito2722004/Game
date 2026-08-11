"""Shared pytest fixtures.

The suite runs against an in-memory SQLite database so it needs no running
PostgreSQL. The models use dialect-neutral types (sa.Uuid, sa.JSON), so the
same schema is exercised either way; the Alembic migration is what is verified
against PostgreSQL.
"""

from __future__ import annotations

import os

# Must be set before app.core.config is imported anywhere.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-used-in-production")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database.session import get_db  # noqa: E402
from app.game_theory.payoff import PayoffMatrix  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.models import Base  # noqa: E402
from app.models.user import UserRole  # noqa: E402


@pytest.fixture()
def engine():
    """A fresh in-memory database per test, shared across connections."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def db(engine) -> Session:
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    session = factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def seeded_db(db: Session) -> Session:
    """A database with the default matrix, strategies and admin in place."""
    from app.database.seed import seed_all

    seed_all(db)
    return db


@pytest.fixture()
def client(seeded_db: Session) -> TestClient:
    """A TestClient wired to the seeded test database."""

    def _override_get_db():
        yield seeded_db

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def classic_matrix() -> PayoffMatrix:
    return PayoffMatrix.classic()


# ------------------------------------------------------------- auth helpers --
def register_user(
    client: TestClient,
    email: str,
    password: str = "password123",
    role: UserRole = UserRole.STUDENT,
    token: str | None = None,
) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Test User",
            "password": password,
            "role": role.value,
        },
        headers=headers,
    )
    return response.json()


def login(client: TestClient, email: str, password: str = "password123") -> str:
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["access_token"]


def admin_token(client: TestClient) -> str:
    """Token for the admin account created by the seed."""
    return login(client, "admin@example.com", "admin12345")


def teacher_token(client: TestClient) -> str:
    """Create a teacher via the admin account and return its token."""
    token = admin_token(client)
    register_user(
        client, "teacher@example.com", role=UserRole.TEACHER, token=token
    )
    return login(client, "teacher@example.com")


def student_token(client: TestClient) -> str:
    register_user(client, "student@example.com", role=UserRole.STUDENT)
    return login(client, "student@example.com")


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_headers(client: TestClient) -> dict[str, str]:
    return auth_headers(admin_token(client))


@pytest.fixture()
def teacher_headers(client: TestClient) -> dict[str, str]:
    return auth_headers(teacher_token(client))


@pytest.fixture()
def student_headers(client: TestClient) -> dict[str, str]:
    return auth_headers(student_token(client))
