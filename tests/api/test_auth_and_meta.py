"""Authentication, authorisation and the response envelope."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.user import UserRole
from tests.conftest import admin_token, auth_headers, login, register_user


class TestEnvelope:
    def test_success_envelope_shape(self, client: TestClient):
        body = client.get("/health").json()
        assert body["success"] is True
        assert body["data"]["status"] == "ok"
        assert "message" in body

    def test_error_envelope_shape(self, client: TestClient):
        response = client.get("/api/v1/strategies/NOT_A_STRATEGY")
        body = response.json()
        assert response.status_code == 404
        assert body["success"] is False
        assert body["data"] is None
        assert body["message"]
        assert isinstance(body["errors"], list)

    def test_root_lists_the_docs(self, client: TestClient):
        data = client.get("/").json()["data"]
        assert data["docs"] == "/docs"
        assert data["api_base"] == "/api/v1"

    def test_openapi_and_swagger_are_served(self, client: TestClient):
        assert client.get("/openapi.json").status_code == 200
        assert client.get("/docs").status_code == 200


class TestRegistration:
    def test_register_returns_a_token_and_the_user(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "full_name": "New Person",
                "password": "password123",
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["access_token"]
        assert data["user"]["email"] == "new@example.com"
        assert data["user"]["role"] == "STUDENT"

    def test_duplicate_email_is_a_conflict(self, client: TestClient):
        register_user(client, "dup@example.com")
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "dup@example.com",
                "full_name": "Other",
                "password": "password123",
            },
        )
        assert response.status_code == 409
        assert response.json()["success"] is False

    def test_email_is_case_insensitive_for_duplicates(self, client: TestClient):
        register_user(client, "case@example.com")
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "CASE@example.com",
                "full_name": "Other",
                "password": "password123",
            },
        )
        assert response.status_code == 409

    def test_short_password_is_rejected(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "x@example.com", "full_name": "X", "password": "short"},
        )
        assert response.status_code == 422
        assert response.json()["errors"][0]["field"] == "password"

    def test_invalid_email_is_rejected(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "full_name": "X", "password": "password123"},
        )
        assert response.status_code == 422

    def test_self_registration_cannot_claim_admin(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "sneaky@example.com",
                "full_name": "Sneaky",
                "password": "password123",
                "role": "ADMIN",
            },
        )
        assert response.status_code == 403

    def test_admin_can_create_a_teacher(self, client: TestClient):
        token = admin_token(client)
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "t@example.com",
                "full_name": "T",
                "password": "password123",
                "role": "TEACHER",
            },
            headers=auth_headers(token),
        )
        assert response.status_code == 201
        assert response.json()["data"]["user"]["role"] == "TEACHER"


class TestLogin:
    def test_login_succeeds_with_correct_credentials(self, client: TestClient):
        register_user(client, "login@example.com")
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "password123"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["token_type"] == "bearer"

    def test_wrong_password_is_rejected(self, client: TestClient):
        register_user(client, "wrong@example.com")
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "wrong@example.com", "password": "not-the-password"},
        )
        assert response.status_code == 401

    def test_unknown_email_gives_the_same_error_as_a_wrong_password(
        self, client: TestClient
    ):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "password123"},
        )
        assert response.status_code == 401
        assert response.json()["message"] == "Incorrect email or password"

    def test_seeded_admin_can_log_in(self, client: TestClient):
        assert admin_token(client)


class TestCurrentUser:
    def test_me_returns_the_authenticated_user(self, client: TestClient):
        register_user(client, "me@example.com")
        token = login(client, "me@example.com")
        response = client.get("/api/v1/auth/me", headers=auth_headers(token))
        assert response.status_code == 200
        assert response.json()["data"]["email"] == "me@example.com"

    def test_me_requires_a_token(self, client: TestClient):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_garbage_token_is_rejected(self, client: TestClient):
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"}
        )
        assert response.status_code == 401


class TestRoleGuards:
    def test_student_cannot_create_a_payoff_matrix(
        self, client: TestClient, student_headers
    ):
        response = client.post(
            "/api/v1/payoff-matrices",
            json={
                "name": "Student attempt",
                "cc": {"player_a_payoff": 3, "player_b_payoff": 3},
                "cd": {"player_a_payoff": 0, "player_b_payoff": 5},
                "dc": {"player_a_payoff": 5, "player_b_payoff": 0},
                "dd": {"player_a_payoff": 1, "player_b_payoff": 1},
            },
            headers=student_headers,
        )
        assert response.status_code == 403

    def test_student_cannot_create_a_tournament(
        self, client: TestClient, student_headers
    ):
        response = client.post(
            "/api/v1/tournaments",
            json={
                "name": "Student tournament",
                "strategy_ids": ["TIT_FOR_TAT", "ALWAYS_DEFECT"],
            },
            headers=student_headers,
        )
        assert response.status_code == 403

    def test_teacher_cannot_delete_a_global_matrix(
        self, client: TestClient, teacher_headers
    ):
        created = client.post(
            "/api/v1/payoff-matrices",
            json={
                "name": "Teacher matrix",
                "cc": {"player_a_payoff": 3, "player_b_payoff": 3},
                "cd": {"player_a_payoff": 0, "player_b_payoff": 5},
                "dc": {"player_a_payoff": 5, "player_b_payoff": 0},
                "dd": {"player_a_payoff": 1, "player_b_payoff": 1},
            },
            headers=teacher_headers,
        ).json()["data"]
        response = client.delete(
            f"/api/v1/payoff-matrices/{created['id']}", headers=teacher_headers
        )
        assert response.status_code == 403

    def test_unauthenticated_write_is_401_not_403(self, client: TestClient):
        response = client.post(
            "/api/v1/tournaments",
            json={"name": "Anon", "strategy_ids": ["TIT_FOR_TAT", "ALWAYS_DEFECT"]},
        )
        assert response.status_code == 401

    def test_reads_are_public(self, client: TestClient):
        assert client.get("/api/v1/strategies").status_code == 200
        assert client.get("/api/v1/payoff-matrices").status_code == 200
