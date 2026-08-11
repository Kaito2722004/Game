"""Match simulation and tournament endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

ALL_SIX = [
    "ALWAYS_COOPERATE",
    "ALWAYS_DEFECT",
    "TIT_FOR_TAT",
    "GRIM_TRIGGER",
    "TIT_FOR_TWO_TATS",
    "RANDOM",
]


def create_tournament(client: TestClient, headers: dict, **overrides) -> dict:
    payload = {
        "name": "Test tournament",
        "strategy_ids": ALL_SIX,
        "rounds_per_match": 100,
        "seed": 42,
    }
    payload.update(overrides)
    response = client.post("/api/v1/tournaments", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["data"]


class TestMatchSimulation:
    def test_simulate_returns_the_full_history(self, client: TestClient):
        response = client.post(
            "/api/v1/matches/simulate",
            json={
                "strategy_a_id": "TIT_FOR_TAT",
                "strategy_b_id": "ALWAYS_DEFECT",
                "rounds": 10,
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["rounds"]) == 10
        assert data["player_a"]["total_payoff"] == 9
        assert data["player_b"]["total_payoff"] == 14
        assert data["winner"] == "ALWAYS_DEFECT"

    def test_round_records_carry_actions_payoffs_and_outcome(self, client: TestClient):
        data = client.post(
            "/api/v1/matches/simulate",
            json={
                "strategy_a_id": "ALWAYS_COOPERATE",
                "strategy_b_id": "ALWAYS_DEFECT",
                "rounds": 3,
            },
        ).json()["data"]
        first = data["rounds"][0]
        assert first["round_number"] == 1
        assert first["player_a_action"] == "COOPERATE"
        assert first["player_b_action"] == "DEFECT"
        assert (first["player_a_payoff"], first["player_b_payoff"]) == (0, 5)
        assert first["outcome"] == "CD"

    def test_cumulative_scores_are_returned(self, client: TestClient):
        data = client.post(
            "/api/v1/matches/simulate",
            json={
                "strategy_a_id": "ALWAYS_COOPERATE",
                "strategy_b_id": "ALWAYS_COOPERATE",
                "rounds": 5,
            },
        ).json()["data"]
        assert data["cumulative_scores"][-1]["player_a_cumulative"] == 15

    def test_draw_is_reported_as_such(self, client: TestClient):
        data = client.post(
            "/api/v1/matches/simulate",
            json={"strategy_a_id": "TIT_FOR_TAT", "strategy_b_id": "TIT_FOR_TAT", "rounds": 10},
        ).json()["data"]
        assert data["winner"] is None
        assert data["is_draw"] is True

    def test_seed_makes_the_result_reproducible(self, client: TestClient):
        payload = {
            "strategy_a_id": "RANDOM",
            "strategy_b_id": "TIT_FOR_TAT",
            "rounds": 50,
            "seed": 99,
        }
        first = client.post("/api/v1/matches/simulate", json=payload).json()["data"]
        second = client.post("/api/v1/matches/simulate", json=payload).json()["data"]
        assert first["player_a"]["total_payoff"] == second["player_a"]["total_payoff"]

    def test_inline_matrix_is_used(self, client: TestClient):
        data = client.post(
            "/api/v1/matches/simulate",
            json={
                "strategy_a_id": "ALWAYS_COOPERATE",
                "strategy_b_id": "ALWAYS_COOPERATE",
                "rounds": 4,
                "matrix": {
                    "cc": {"player_a_payoff": 10, "player_b_payoff": 10},
                    "cd": {"player_a_payoff": 0, "player_b_payoff": 12},
                    "dc": {"player_a_payoff": 12, "player_b_payoff": 0},
                    "dd": {"player_a_payoff": 2, "player_b_payoff": 2},
                },
            },
        ).json()["data"]
        assert data["player_a"]["total_payoff"] == 40

    def test_continuation_probability_of_zero_stops_after_one_round(
        self, client: TestClient
    ):
        data = client.post(
            "/api/v1/matches/simulate",
            json={
                "strategy_a_id": "TIT_FOR_TAT",
                "strategy_b_id": "TIT_FOR_TAT",
                "rounds": 100,
                "continuation_probability": 0,
            },
        ).json()["data"]
        assert data["rounds_played"] == 1

    def test_persisted_match_can_be_fetched_by_id(self, client: TestClient):
        created = client.post(
            "/api/v1/matches/simulate",
            json={
                "strategy_a_id": "TIT_FOR_TAT",
                "strategy_b_id": "GRIM_TRIGGER",
                "rounds": 20,
                "persist": True,
            },
        ).json()["data"]
        assert created["id"] is not None

        fetched = client.get(f"/api/v1/matches/{created['id']}")
        assert fetched.status_code == 200
        data = fetched.json()["data"]
        assert data["rounds_played"] == 20
        assert len(data["rounds"]) == 20
        assert data["player_a"]["total_payoff"] == created["player_a"]["total_payoff"]

    def test_unpersisted_match_has_no_id(self, client: TestClient):
        data = client.post(
            "/api/v1/matches/simulate",
            json={"strategy_a_id": "TIT_FOR_TAT", "strategy_b_id": "RANDOM", "rounds": 5},
        ).json()["data"]
        assert data["id"] is None

    def test_unknown_match_id_is_404(self, client: TestClient):
        response = client.get("/api/v1/matches/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_unknown_strategy_is_404(self, client: TestClient):
        response = client.post(
            "/api/v1/matches/simulate",
            json={"strategy_a_id": "NOPE", "strategy_b_id": "TIT_FOR_TAT", "rounds": 10},
        )
        assert response.status_code == 404

    def test_zero_rounds_is_422(self, client: TestClient):
        response = client.post(
            "/api/v1/matches/simulate",
            json={"strategy_a_id": "TIT_FOR_TAT", "strategy_b_id": "RANDOM", "rounds": 0},
        )
        assert response.status_code == 422

    def test_negative_rounds_is_422(self, client: TestClient):
        response = client.post(
            "/api/v1/matches/simulate",
            json={"strategy_a_id": "TIT_FOR_TAT", "strategy_b_id": "RANDOM", "rounds": -1},
        )
        assert response.status_code == 422

    def test_out_of_range_continuation_probability_is_422(self, client: TestClient):
        response = client.post(
            "/api/v1/matches/simulate",
            json={
                "strategy_a_id": "TIT_FOR_TAT",
                "strategy_b_id": "RANDOM",
                "rounds": 10,
                "continuation_probability": 2,
            },
        )
        assert response.status_code == 422


class TestTournamentLifecycle:
    def test_create_starts_pending(self, client: TestClient, teacher_headers):
        tournament = create_tournament(client, teacher_headers)
        assert tournament["status"] == "PENDING"
        assert tournament["matches_played"] == 0

    def test_run_produces_a_full_ranking(self, client: TestClient, teacher_headers):
        tournament = create_tournament(client, teacher_headers)
        response = client.post(
            f"/api/v1/tournaments/{tournament['id']}/run", headers=teacher_headers
        )
        assert response.status_code == 200
        data = response.json()["data"]

        assert data["status"] == "COMPLETED"
        assert len(data["rankings"]) == 6
        assert data["matches_played"] == 15
        assert data["rankings"][0]["rank"] == 1
        assert data["winner_strategy_id"] == data["rankings"][0]["strategy_id"]

    def test_ranking_is_sorted_by_total_score(self, client: TestClient, teacher_headers):
        tournament = create_tournament(client, teacher_headers)
        data = client.post(
            f"/api/v1/tournaments/{tournament['id']}/run", headers=teacher_headers
        ).json()["data"]
        scores = [row["total_score"] for row in data["rankings"]]
        assert scores == sorted(scores, reverse=True)

    def test_known_cooperation_rates_appear_in_the_table(
        self, client: TestClient, teacher_headers
    ):
        tournament = create_tournament(client, teacher_headers)
        data = client.post(
            f"/api/v1/tournaments/{tournament['id']}/run", headers=teacher_headers
        ).json()["data"]
        rates = {row["strategy_id"]: row["cooperation_rate"] for row in data["rankings"]}
        assert rates["ALWAYS_COOPERATE"] == 1.0
        assert rates["ALWAYS_DEFECT"] == 0.0

    def test_win_draw_loss_counts_add_up(self, client: TestClient, teacher_headers):
        tournament = create_tournament(client, teacher_headers)
        data = client.post(
            f"/api/v1/tournaments/{tournament['id']}/run", headers=teacher_headers
        ).json()["data"]
        for row in data["rankings"]:
            assert row["wins"] + row["draws"] + row["losses"] == row["matches_played"] == 5

    def test_results_are_readable_after_the_run(self, client: TestClient, teacher_headers):
        tournament = create_tournament(client, teacher_headers)
        client.post(f"/api/v1/tournaments/{tournament['id']}/run", headers=teacher_headers)
        response = client.get(f"/api/v1/tournaments/{tournament['id']}/results")
        assert response.status_code == 200
        assert len(response.json()["data"]["rankings"]) == 6

    def test_matches_are_stored_with_their_rounds(
        self, client: TestClient, teacher_headers
    ):
        tournament = create_tournament(client, teacher_headers, rounds_per_match=20)
        client.post(f"/api/v1/tournaments/{tournament['id']}/run", headers=teacher_headers)

        matches = client.get(f"/api/v1/tournaments/{tournament['id']}/matches").json()["data"]
        assert len(matches) == 15

        detail = client.get(
            f"/api/v1/tournaments/{tournament['id']}/matches/{matches[0]['id']}"
        ).json()["data"]
        assert len(detail["rounds"]) == 20
        assert detail["rounds"][0]["round_number"] == 1

    def test_statistics_endpoint(self, client: TestClient, teacher_headers):
        tournament = create_tournament(client, teacher_headers, rounds_per_match=25)
        client.post(f"/api/v1/tournaments/{tournament['id']}/run", headers=teacher_headers)

        data = client.get(
            f"/api/v1/tournaments/{tournament['id']}/statistics"
        ).json()["data"]
        assert data["matches_played"] == 15
        assert data["score_statistics"]["count"] == 6
        assert len(data["cooperation_by_round"]) == 25
        assert len(data["head_to_head"]) == 30
        assert sum(data["outcome_rates"].values()) == 1.0

    def test_same_seed_reproduces_the_table(self, client: TestClient, teacher_headers):
        first = create_tournament(client, teacher_headers, name="Run one", seed=7)
        second = create_tournament(client, teacher_headers, name="Run two", seed=7)
        table_one = client.post(
            f"/api/v1/tournaments/{first['id']}/run", headers=teacher_headers
        ).json()["data"]["rankings"]
        table_two = client.post(
            f"/api/v1/tournaments/{second['id']}/run", headers=teacher_headers
        ).json()["data"]["rankings"]
        assert [r["total_score"] for r in table_one] == [
            r["total_score"] for r in table_two
        ]

    def test_repetitions_are_honoured(self, client: TestClient, teacher_headers):
        tournament = create_tournament(
            client, teacher_headers, rounds_per_match=10, repetitions=3
        )
        data = client.post(
            f"/api/v1/tournaments/{tournament['id']}/run", headers=teacher_headers
        ).json()["data"]
        assert data["matches_played"] == 45

    def test_self_play_adds_the_diagonal(self, client: TestClient, teacher_headers):
        tournament = create_tournament(
            client, teacher_headers, rounds_per_match=10, include_self_play=True
        )
        data = client.post(
            f"/api/v1/tournaments/{tournament['id']}/run", headers=teacher_headers
        ).json()["data"]
        assert data["matches_played"] == 21


class TestTournamentEdgeCases:
    def test_running_twice_is_a_conflict(self, client: TestClient, teacher_headers):
        tournament = create_tournament(client, teacher_headers, rounds_per_match=10)
        client.post(f"/api/v1/tournaments/{tournament['id']}/run", headers=teacher_headers)
        second = client.post(
            f"/api/v1/tournaments/{tournament['id']}/run", headers=teacher_headers
        )
        assert second.status_code == 409

    def test_results_before_running_is_a_conflict(
        self, client: TestClient, teacher_headers
    ):
        tournament = create_tournament(client, teacher_headers)
        response = client.get(f"/api/v1/tournaments/{tournament['id']}/results")
        assert response.status_code == 409

    def test_statistics_before_running_is_a_conflict(
        self, client: TestClient, teacher_headers
    ):
        tournament = create_tournament(client, teacher_headers)
        response = client.get(f"/api/v1/tournaments/{tournament['id']}/statistics")
        assert response.status_code == 409

    def test_duplicate_strategies_are_rejected(self, client: TestClient, teacher_headers):
        response = client.post(
            "/api/v1/tournaments",
            json={
                "name": "Duplicates",
                "strategy_ids": ["TIT_FOR_TAT", "TIT_FOR_TAT"],
            },
            headers=teacher_headers,
        )
        assert response.status_code == 422

    def test_empty_strategy_list_is_rejected(self, client: TestClient, teacher_headers):
        response = client.post(
            "/api/v1/tournaments",
            json={"name": "Empty", "strategy_ids": []},
            headers=teacher_headers,
        )
        assert response.status_code == 422

    def test_single_strategy_without_self_play_is_rejected(
        self, client: TestClient, teacher_headers
    ):
        response = client.post(
            "/api/v1/tournaments",
            json={"name": "Lonely", "strategy_ids": ["TIT_FOR_TAT"]},
            headers=teacher_headers,
        )
        assert response.status_code == 422

    def test_single_strategy_with_self_play_is_allowed(
        self, client: TestClient, teacher_headers
    ):
        tournament = create_tournament(
            client,
            teacher_headers,
            strategy_ids=["TIT_FOR_TAT"],
            include_self_play=True,
            rounds_per_match=5,
        )
        data = client.post(
            f"/api/v1/tournaments/{tournament['id']}/run", headers=teacher_headers
        ).json()["data"]
        assert data["matches_played"] == 1

    def test_unknown_strategy_is_404(self, client: TestClient, teacher_headers):
        response = client.post(
            "/api/v1/tournaments",
            json={"name": "Bad", "strategy_ids": ["TIT_FOR_TAT", "NOPE"]},
            headers=teacher_headers,
        )
        assert response.status_code == 404

    def test_unknown_tournament_is_404(self, client: TestClient):
        response = client.get(
            "/api/v1/tournaments/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404

    def test_match_from_another_tournament_is_404(
        self, client: TestClient, teacher_headers
    ):
        first = create_tournament(client, teacher_headers, name="A", rounds_per_match=5)
        second = create_tournament(client, teacher_headers, name="B", rounds_per_match=5)
        client.post(f"/api/v1/tournaments/{first['id']}/run", headers=teacher_headers)
        client.post(f"/api/v1/tournaments/{second['id']}/run", headers=teacher_headers)

        first_matches = client.get(
            f"/api/v1/tournaments/{first['id']}/matches"
        ).json()["data"]
        response = client.get(
            f"/api/v1/tournaments/{second['id']}/matches/{first_matches[0]['id']}"
        )
        assert response.status_code == 404


class TestTournamentExport:
    def test_results_csv(self, client: TestClient, teacher_headers):
        tournament = create_tournament(client, teacher_headers, rounds_per_match=10)
        client.post(f"/api/v1/tournaments/{tournament['id']}/run", headers=teacher_headers)

        response = client.get(f"/api/v1/tournaments/{tournament['id']}/export/results.csv")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        lines = response.text.strip().splitlines()
        assert lines[0].startswith("rank,strategy_id")
        assert len(lines) == 7  # header plus six strategies

    def test_rounds_csv_has_every_round(self, client: TestClient, teacher_headers):
        tournament = create_tournament(client, teacher_headers, rounds_per_match=10)
        client.post(f"/api/v1/tournaments/{tournament['id']}/run", headers=teacher_headers)

        response = client.get(f"/api/v1/tournaments/{tournament['id']}/export/rounds.csv")
        lines = response.text.strip().splitlines()
        assert len(lines) == 1 + 15 * 10
