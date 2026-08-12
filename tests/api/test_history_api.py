"""The combined activity history endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _data(response):
    """Unwrap a successful envelope. Creates answer 201, reads 200."""
    assert 200 <= response.status_code < 300, response.text
    body = response.json()
    assert body["success"] is True
    return body["data"]


def _run_tournament(client: TestClient, headers: dict[str, str], name: str) -> str:
    created = _data(
        client.post(
            "/api/v1/tournaments",
            headers=headers,
            json={
                "name": name,
                "strategy_ids": ["TIT_FOR_TAT", "ALWAYS_DEFECT", "GRIM_TRIGGER"],
                "rounds_per_match": 10,
                "seed": 7,
            },
        )
    )
    _data(client.post(f"/api/v1/tournaments/{created['id']}/run", headers=headers))
    return created["id"]


class TestHistoryEmpty:
    def test_reports_zeroes_before_anything_is_played(self, client: TestClient) -> None:
        data = _data(client.get("/api/v1/history"))
        assert data["entries"] == []
        totals = data["totals"]
        assert totals["tournaments"] == 0
        assert totals["experiments"] == 0
        assert totals["simulated_matches"] == 0
        assert totals["total_rounds_played"] == 0

    def test_is_readable_without_signing_in(self, client: TestClient) -> None:
        assert client.get("/api/v1/history").status_code == 200


class TestHistoryWithActivity:
    def test_lists_a_completed_tournament(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        _run_tournament(client, admin_headers, "History tournament")

        data = _data(client.get("/api/v1/history"))
        tournaments = [e for e in data["entries"] if e["kind"] == "TOURNAMENT"]
        assert len(tournaments) == 1

        entry = tournaments[0]
        assert entry["title"] == "History tournament"
        assert entry["status"] == "COMPLETED"
        assert entry["matches"] == 3  # three strategies -> three pairings
        assert entry["rounds"] == 30  # three matches of ten rounds
        assert entry["headline"].startswith("Winner:")
        assert 0.0 <= entry["cooperation_rate"] <= 1.0

    def test_totals_count_rounds_across_kinds(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        _run_tournament(client, admin_headers, "Counted tournament")
        _data(
            client.post(
                "/api/v1/matches/simulate",
                headers=admin_headers,
                json={
                    "strategy_a_id": "TIT_FOR_TAT",
                    "strategy_b_id": "ALWAYS_DEFECT",
                    "rounds": 12,
                    "seed": 1,
                    "persist": True,
                },
            )
        )

        totals = _data(client.get("/api/v1/history"))["totals"]
        assert totals["tournaments"] == 1
        assert totals["tournament_rounds"] == 30
        assert totals["simulated_matches"] == 1
        assert totals["total_rounds_played"] == 42

    def test_a_persisted_simulation_is_its_own_entry_not_a_tournament(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        """The ad hoc container is a storage detail and must not surface."""
        _data(
            client.post(
                "/api/v1/matches/simulate",
                headers=admin_headers,
                json={
                    "strategy_a_id": "TIT_FOR_TAT",
                    "strategy_b_id": "ALWAYS_DEFECT",
                    "rounds": 10,
                    "seed": 42,
                    "persist": True,
                },
            )
        )

        data = _data(client.get("/api/v1/history"))
        kinds = [entry["kind"] for entry in data["entries"]]
        assert kinds == ["SIMULATED_MATCH"]
        assert data["totals"]["tournaments"] == 0

        entry = data["entries"][0]
        assert entry["title"] == "Tit-for-Tat vs Always Defect"
        assert entry["rounds"] == 10
        # TFT cooperates once against Always Defect, so 1 of 20 moves.
        assert entry["cooperation_rate"] == 1 / 20
        assert entry["parent_id"] is not None

    def test_an_unrun_tournament_still_appears(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        _data(
            client.post(
                "/api/v1/tournaments",
                headers=admin_headers,
                json={
                    "name": "Pending one",
                    "strategy_ids": ["TIT_FOR_TAT", "ALWAYS_DEFECT"],
                    "rounds_per_match": 5,
                },
            )
        )

        entry = _data(client.get("/api/v1/history"))["entries"][0]
        assert entry["status"] == "PENDING"
        assert entry["rounds"] == 0
        assert entry["cooperation_rate"] is None


class TestHistoryFiltering:
    def test_kind_narrows_the_list_but_not_the_totals(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        _run_tournament(client, admin_headers, "Filtered tournament")
        _data(
            client.post(
                "/api/v1/matches/simulate",
                headers=admin_headers,
                json={
                    "strategy_a_id": "GRIM_TRIGGER",
                    "strategy_b_id": "RANDOM",
                    "rounds": 8,
                    "seed": 3,
                    "persist": True,
                },
            )
        )

        everything = _data(client.get("/api/v1/history"))
        assert len(everything["entries"]) == 2

        only_matches = _data(client.get("/api/v1/history?kind=SIMULATED_MATCH"))
        assert [e["kind"] for e in only_matches["entries"]] == ["SIMULATED_MATCH"]
        # Totals describe the whole record regardless of the filter.
        assert only_matches["totals"] == everything["totals"]

    def test_rejects_an_unknown_kind(self, client: TestClient) -> None:
        assert client.get("/api/v1/history?kind=NONSENSE").status_code == 422

    def test_limit_is_bounded(self, client: TestClient) -> None:
        assert client.get("/api/v1/history?limit=0").status_code == 422
        assert client.get("/api/v1/history?limit=5000").status_code == 422


class TestHistoryOrdering:
    def test_newest_first(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        _run_tournament(client, admin_headers, "Older")
        _run_tournament(client, admin_headers, "Newer")

        entries = _data(client.get("/api/v1/history?kind=TOURNAMENT"))["entries"]
        stamps = [entry["occurred_at"] for entry in entries]
        assert stamps == sorted(stamps, reverse=True)


class TestHistoryExperiments:
    def test_reports_recorded_rounds_and_cooperation(
        self, client: TestClient, admin_headers: dict[str, str]
    ) -> None:
        experiment = _data(
            client.post(
                "/api/v1/experiments",
                headers=admin_headers,
                json={
                    "name": "History session",
                    "rounds": 3,
                    "anonymous_mode": True,
                    "trust_survey_enabled": False,
                },
            )
        )
        eid = experiment["id"]
        for code in ("S01", "S02"):
            client.post(
                f"/api/v1/experiments/{eid}/participants",
                headers=admin_headers,
                json={"code": code},
            )
        started = _data(
            client.post(f"/api/v1/experiments/{eid}/start?seed=1", headers=admin_headers)
        )
        match_id = started["pairs"][0]["id"]

        # Two rounds: (C,C) then (C,D) — three cooperations out of four moves.
        for number, (a, b) in enumerate(
            [("COOPERATE", "COOPERATE"), ("COOPERATE", "DEFECT")], start=1
        ):
            _data(
                client.post(
                    f"/api/v1/experiments/{eid}/rounds",
                    headers=admin_headers,
                    json={
                        "match_id": match_id,
                        "round_number": number,
                        "player_a_action": a,
                        "player_b_action": b,
                    },
                )
            )

        entry = _data(client.get("/api/v1/history?kind=EXPERIMENT"))["entries"][0]
        assert entry["title"] == "History session"
        assert entry["status"] == "RUNNING"
        assert entry["matches"] == 1
        assert entry["rounds"] == 2
        assert entry["cooperation_rate"] == 0.75
