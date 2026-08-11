"""Analysis, strategy catalogue and payoff-matrix endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

CLASSIC = {
    "cc": {"player_a_payoff": 3, "player_b_payoff": 3},
    "cd": {"player_a_payoff": 0, "player_b_payoff": 5},
    "dc": {"player_a_payoff": 5, "player_b_payoff": 0},
    "dd": {"player_a_payoff": 1, "player_b_payoff": 1},
}


class TestAnalyzeEndpoint:
    def test_classic_matrix_analysis(self, client: TestClient):
        response = client.post("/api/v1/game-theory/analyze", json={"matrix": CLASSIC})
        assert response.status_code == 200
        data = response.json()["data"]

        assert data["conditions"]["is_prisoners_dilemma"] is True
        assert data["dominant_strategy_player_a"]["action"] == "DEFECT"
        assert data["dominant_strategy_player_b"]["action"] == "DEFECT"
        assert [eq["outcome"] for eq in data["nash_equilibria"]] == ["DD"]
        assert data["mutual_cooperation_pareto_superior_to_mutual_defection"] is True
        assert data["equilibrium_is_pareto_inferior"] is True
        assert "DD" in data["pareto_inferior_outcomes"]

    def test_trps_values_are_reported(self, client: TestClient):
        data = client.post(
            "/api/v1/game-theory/analyze", json={"matrix": CLASSIC}
        ).json()["data"]
        player_a = data["conditions"]["player_a"]
        assert player_a["temptation"] == 5
        assert player_a["reward"] == 3
        assert player_a["punishment"] == 1
        assert player_a["sucker"] == 0

    def test_non_dilemma_matrix(self, client: TestClient):
        stag_hunt = {
            "cc": {"player_a_payoff": 4, "player_b_payoff": 4},
            "cd": {"player_a_payoff": 0, "player_b_payoff": 3},
            "dc": {"player_a_payoff": 3, "player_b_payoff": 0},
            "dd": {"player_a_payoff": 2, "player_b_payoff": 2},
        }
        data = client.post(
            "/api/v1/game-theory/analyze", json={"matrix": stag_hunt}
        ).json()["data"]
        assert data["conditions"]["is_prisoners_dilemma"] is False
        assert data["dominant_strategy_player_a"]["exists"] is False
        assert len(data["nash_equilibria"]) == 2

    def test_analysis_of_a_stored_matrix(self, client: TestClient):
        matrices = client.get("/api/v1/payoff-matrices").json()["data"]
        default_id = next(m["id"] for m in matrices if m["is_default"])
        response = client.post(
            "/api/v1/game-theory/analyze", json={"payoff_matrix_id": default_id}
        )
        assert response.status_code == 200
        assert response.json()["data"]["conditions"]["is_prisoners_dilemma"] is True

    def test_get_variant_by_matrix_id(self, client: TestClient):
        matrices = client.get("/api/v1/payoff-matrices").json()["data"]
        default_id = next(m["id"] for m in matrices if m["is_default"])
        response = client.get(f"/api/v1/game-theory/analyze/{default_id}")
        assert response.status_code == 200

    def test_supplying_both_sources_is_rejected(self, client: TestClient):
        matrices = client.get("/api/v1/payoff-matrices").json()["data"]
        response = client.post(
            "/api/v1/game-theory/analyze",
            json={"matrix": CLASSIC, "payoff_matrix_id": matrices[0]["id"]},
        )
        assert response.status_code == 422

    def test_supplying_neither_source_is_rejected(self, client: TestClient):
        assert client.post("/api/v1/game-theory/analyze", json={}).status_code == 422

    def test_unknown_matrix_id_is_404(self, client: TestClient):
        response = client.post(
            "/api/v1/game-theory/analyze",
            json={"payoff_matrix_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert response.status_code == 404

    def test_incomplete_matrix_is_rejected(self, client: TestClient):
        response = client.post(
            "/api/v1/game-theory/analyze",
            json={"matrix": {"cc": {"player_a_payoff": 3, "player_b_payoff": 3}}},
        )
        assert response.status_code == 422


class TestStrategyEndpoints:
    def test_list_returns_all_six(self, client: TestClient):
        data = client.get("/api/v1/strategies").json()["data"]
        assert len(data) == 6
        assert {s["id"] for s in data} == {
            "ALWAYS_COOPERATE",
            "ALWAYS_DEFECT",
            "TIT_FOR_TAT",
            "GRIM_TRIGGER",
            "TIT_FOR_TWO_TATS",
            "RANDOM",
        }

    def test_each_entry_carries_metadata(self, client: TestClient):
        for strategy in client.get("/api/v1/strategies").json()["data"]:
            assert strategy["name"] and strategy["description"]
            assert strategy["rules"]
            assert strategy["category"] in {"NICE", "NASTY", "STOCHASTIC"}

    def test_get_one_strategy(self, client: TestClient):
        data = client.get("/api/v1/strategies/TIT_FOR_TAT").json()["data"]
        assert data["name"] == "Tit-for-Tat"

    def test_lookup_is_case_insensitive(self, client: TestClient):
        assert client.get("/api/v1/strategies/tit_for_tat").status_code == 200

    def test_unknown_strategy_is_404(self, client: TestClient):
        response = client.get("/api/v1/strategies/NOPE")
        assert response.status_code == 404
        assert "Available strategies" in response.json()["errors"][0]


class TestPayoffMatrixEndpoints:
    def test_seed_created_the_default_matrix(self, client: TestClient):
        data = client.get("/api/v1/payoff-matrices").json()["data"]
        defaults = [m for m in data if m["is_default"]]
        assert len(defaults) == 1
        assert defaults[0]["cc"]["player_a_payoff"] == 3

    def test_create_and_fetch(self, client: TestClient, teacher_headers):
        created = client.post(
            "/api/v1/payoff-matrices",
            json={"name": "Chicken", "description": "Not a dilemma", **CLASSIC},
            headers=teacher_headers,
        )
        assert created.status_code == 201
        matrix_id = created.json()["data"]["id"]

        fetched = client.get(f"/api/v1/payoff-matrices/{matrix_id}")
        assert fetched.status_code == 200
        assert fetched.json()["data"]["name"] == "Chicken"

    def test_duplicate_name_is_a_conflict(self, client: TestClient, teacher_headers):
        payload = {"name": "Same name", **CLASSIC}
        client.post("/api/v1/payoff-matrices", json=payload, headers=teacher_headers)
        second = client.post(
            "/api/v1/payoff-matrices", json=payload, headers=teacher_headers
        )
        assert second.status_code == 409

    def test_update_changes_the_payoffs(self, client: TestClient, admin_headers):
        created = client.post(
            "/api/v1/payoff-matrices",
            json={"name": "Editable", **CLASSIC},
            headers=admin_headers,
        ).json()["data"]
        updated = client.put(
            f"/api/v1/payoff-matrices/{created['id']}",
            json={"dd": {"player_a_payoff": 2, "player_b_payoff": 2}},
            headers=admin_headers,
        )
        assert updated.status_code == 200
        assert updated.json()["data"]["dd"]["player_a_payoff"] == 2

    def test_setting_a_new_default_clears_the_old_one(
        self, client: TestClient, admin_headers
    ):
        client.post(
            "/api/v1/payoff-matrices",
            json={"name": "New default", "is_default": True, **CLASSIC},
            headers=admin_headers,
        )
        matrices = client.get("/api/v1/payoff-matrices").json()["data"]
        assert sum(1 for m in matrices if m["is_default"]) == 1

    def test_delete_removes_the_matrix(self, client: TestClient, admin_headers):
        created = client.post(
            "/api/v1/payoff-matrices",
            json={"name": "Disposable", **CLASSIC},
            headers=admin_headers,
        ).json()["data"]
        assert (
            client.delete(
                f"/api/v1/payoff-matrices/{created['id']}", headers=admin_headers
            ).status_code
            == 200
        )
        assert client.get(f"/api/v1/payoff-matrices/{created['id']}").status_code == 404

    def test_the_default_matrix_cannot_be_deleted(
        self, client: TestClient, admin_headers
    ):
        matrices = client.get("/api/v1/payoff-matrices").json()["data"]
        default_id = next(m["id"] for m in matrices if m["is_default"])
        response = client.delete(
            f"/api/v1/payoff-matrices/{default_id}", headers=admin_headers
        )
        assert response.status_code == 409

    def test_unknown_matrix_is_404(self, client: TestClient):
        response = client.get(
            "/api/v1/payoff-matrices/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404

    def test_malformed_uuid_is_422(self, client: TestClient):
        assert client.get("/api/v1/payoff-matrices/not-a-uuid").status_code == 422
