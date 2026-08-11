"""Human experiment and trust survey endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def create_experiment(client: TestClient, headers: dict, **overrides) -> dict:
    payload = {"name": "Game Theory Classroom Experiment", "rounds": 10}
    payload.update(overrides)
    response = client.post("/api/v1/experiments", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["data"]


def add_participants(
    client: TestClient, headers: dict, experiment_id: str, count: int
) -> list[dict]:
    participants = []
    for index in range(1, count + 1):
        response = client.post(
            f"/api/v1/experiments/{experiment_id}/participants",
            json={"code": f"S{index:02d}", "display_name": f"Student {index}"},
            headers=headers,
        )
        assert response.status_code == 201, response.text
        participants.append(response.json()["data"])
    return participants


def start(client: TestClient, headers: dict, experiment_id: str, seed: int = 1) -> dict:
    response = client.post(
        f"/api/v1/experiments/{experiment_id}/start?seed={seed}", headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def submit(
    client: TestClient,
    headers: dict,
    experiment_id: str,
    match_id: str,
    round_number: int,
    action_a: str,
    action_b: str,
):
    return client.post(
        f"/api/v1/experiments/{experiment_id}/rounds",
        json={
            "match_id": match_id,
            "round_number": round_number,
            "player_a_action": action_a,
            "player_b_action": action_b,
        },
        headers=headers,
    )


class TestExperimentSetup:
    def test_create_starts_as_draft(self, client: TestClient, teacher_headers):
        experiment = create_experiment(client, teacher_headers)
        assert experiment["status"] == "DRAFT"
        assert experiment["participant_count"] == 0
        assert experiment["rounds"] == 10

    def test_uses_the_default_matrix_when_none_is_given(
        self, client: TestClient, teacher_headers
    ):
        experiment = create_experiment(client, teacher_headers)
        matrices = client.get("/api/v1/payoff-matrices").json()["data"]
        default_id = next(m["id"] for m in matrices if m["is_default"])
        assert experiment["payoff_matrix_id"] == default_id

    def test_add_and_list_participants(self, client: TestClient, teacher_headers):
        experiment = create_experiment(client, teacher_headers)
        add_participants(client, teacher_headers, experiment["id"], 4)
        listed = client.get(
            f"/api/v1/experiments/{experiment['id']}/participants"
        ).json()["data"]
        assert len(listed) == 4

    def test_duplicate_participant_code_is_a_conflict(
        self, client: TestClient, teacher_headers
    ):
        experiment = create_experiment(client, teacher_headers)
        add_participants(client, teacher_headers, experiment["id"], 1)
        response = client.post(
            f"/api/v1/experiments/{experiment['id']}/participants",
            json={"code": "S01"},
            headers=teacher_headers,
        )
        assert response.status_code == 409

    def test_remove_participant(self, client: TestClient, teacher_headers):
        experiment = create_experiment(client, teacher_headers)
        participants = add_participants(client, teacher_headers, experiment["id"], 2)
        response = client.delete(
            f"/api/v1/experiments/{experiment['id']}/participants/{participants[0]['id']}",
            headers=teacher_headers,
        )
        assert response.status_code == 200
        remaining = client.get(
            f"/api/v1/experiments/{experiment['id']}/participants"
        ).json()["data"]
        assert len(remaining) == 1

    def test_removing_an_unknown_participant_is_404(
        self, client: TestClient, teacher_headers
    ):
        experiment = create_experiment(client, teacher_headers)
        response = client.delete(
            f"/api/v1/experiments/{experiment['id']}/participants/"
            "00000000-0000-0000-0000-000000000000",
            headers=teacher_headers,
        )
        assert response.status_code == 404

    def test_settings_can_be_updated_while_draft(
        self, client: TestClient, teacher_headers
    ):
        experiment = create_experiment(client, teacher_headers)
        response = client.put(
            f"/api/v1/experiments/{experiment['id']}",
            json={"rounds": 5, "anonymous_mode": False},
            headers=teacher_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["rounds"] == 5


class TestExperimentStart:
    def test_start_pairs_participants(self, client: TestClient, teacher_headers):
        experiment = create_experiment(client, teacher_headers)
        add_participants(client, teacher_headers, experiment["id"], 6)
        data = start(client, teacher_headers, experiment["id"])
        assert data["status"] == "RUNNING"
        assert len(data["pairs"]) == 3
        assert data["unpaired_participant_ids"] == []

    def test_odd_participant_is_reported_not_dropped(
        self, client: TestClient, teacher_headers
    ):
        experiment = create_experiment(client, teacher_headers)
        add_participants(client, teacher_headers, experiment["id"], 5)
        data = start(client, teacher_headers, experiment["id"])
        assert len(data["pairs"]) == 2
        assert len(data["unpaired_participant_ids"]) == 1

    def test_pairing_is_reproducible_from_a_seed(
        self, client: TestClient, teacher_headers
    ):
        first = create_experiment(client, teacher_headers, name="One")
        add_participants(client, teacher_headers, first["id"], 6)
        pairs_one = start(client, teacher_headers, first["id"], seed=5)["pairs"]

        second = create_experiment(client, teacher_headers, name="Two")
        add_participants(client, teacher_headers, second["id"], 6)
        pairs_two = start(client, teacher_headers, second["id"], seed=5)["pairs"]

        assert [p["participant_a_label"] for p in pairs_one] == [
            p["participant_a_label"] for p in pairs_two
        ]

    def test_anonymous_mode_hides_display_names(
        self, client: TestClient, teacher_headers
    ):
        experiment = create_experiment(client, teacher_headers, anonymous_mode=True)
        add_participants(client, teacher_headers, experiment["id"], 2)
        pairs = start(client, teacher_headers, experiment["id"])["pairs"]
        assert pairs[0]["participant_a_label"].startswith("S")

    def test_named_mode_shows_display_names(self, client: TestClient, teacher_headers):
        experiment = create_experiment(client, teacher_headers, anonymous_mode=False)
        add_participants(client, teacher_headers, experiment["id"], 2)
        pairs = start(client, teacher_headers, experiment["id"])["pairs"]
        assert pairs[0]["participant_a_label"].startswith("Student")

    def test_cannot_start_with_fewer_than_two_participants(
        self, client: TestClient, teacher_headers
    ):
        experiment = create_experiment(client, teacher_headers)
        add_participants(client, teacher_headers, experiment["id"], 1)
        response = client.post(
            f"/api/v1/experiments/{experiment['id']}/start", headers=teacher_headers
        )
        assert response.status_code == 422

    def test_cannot_start_twice(self, client: TestClient, teacher_headers):
        experiment = create_experiment(client, teacher_headers)
        add_participants(client, teacher_headers, experiment["id"], 2)
        start(client, teacher_headers, experiment["id"])
        response = client.post(
            f"/api/v1/experiments/{experiment['id']}/start", headers=teacher_headers
        )
        assert response.status_code == 409

    def test_participants_cannot_be_added_after_start(
        self, client: TestClient, teacher_headers
    ):
        experiment = create_experiment(client, teacher_headers)
        add_participants(client, teacher_headers, experiment["id"], 2)
        start(client, teacher_headers, experiment["id"])
        response = client.post(
            f"/api/v1/experiments/{experiment['id']}/participants",
            json={"code": "LATE"},
            headers=teacher_headers,
        )
        assert response.status_code == 409


class TestRoundSubmission:
    def test_backend_computes_the_payoffs(self, client: TestClient, teacher_headers):
        experiment = create_experiment(client, teacher_headers)
        add_participants(client, teacher_headers, experiment["id"], 2)
        match = start(client, teacher_headers, experiment["id"])["pairs"][0]

        response = submit(
            client, teacher_headers, experiment["id"], match["id"], 1, "COOPERATE", "DEFECT"
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["player_a_payoff"] == 0
        assert data["player_b_payoff"] == 5

    def test_all_four_outcomes_score_correctly(
        self, client: TestClient, teacher_headers
    ):
        experiment = create_experiment(client, teacher_headers)
        add_participants(client, teacher_headers, experiment["id"], 2)
        match = start(client, teacher_headers, experiment["id"])["pairs"][0]

        expected = {
            ("COOPERATE", "COOPERATE"): (3, 3),
            ("COOPERATE", "DEFECT"): (0, 5),
            ("DEFECT", "COOPERATE"): (5, 0),
            ("DEFECT", "DEFECT"): (1, 1),
        }
        for index, ((action_a, action_b), payoffs) in enumerate(expected.items(), start=1):
            data = submit(
                client, teacher_headers, experiment["id"], match["id"], index, action_a, action_b
            ).json()["data"]
            assert (data["player_a_payoff"], data["player_b_payoff"]) == payoffs

    def test_running_score_accumulates_on_the_pair(
        self, client: TestClient, teacher_headers
    ):
        experiment = create_experiment(client, teacher_headers)
        add_participants(client, teacher_headers, experiment["id"], 2)
        match = start(client, teacher_headers, experiment["id"])["pairs"][0]
        for round_number in range(1, 4):
            submit(
                client,
                teacher_headers,
                experiment["id"],
                match["id"],
                round_number,
                "COOPERATE",
                "COOPERATE",
            )
        results = client.get(f"/api/v1/experiments/{experiment['id']}/results").json()["data"]
        assert results["matches"][0]["player_a_score"] == 9
        assert results["matches"][0]["rounds_recorded"] == 3

    def test_duplicate_round_is_a_conflict(self, client: TestClient, teacher_headers):
        experiment = create_experiment(client, teacher_headers)
        add_participants(client, teacher_headers, experiment["id"], 2)
        match = start(client, teacher_headers, experiment["id"])["pairs"][0]
        submit(client, teacher_headers, experiment["id"], match["id"], 1, "COOPERATE", "COOPERATE")
        second = submit(
            client, teacher_headers, experiment["id"], match["id"], 1, "DEFECT", "DEFECT"
        )
        assert second.status_code == 409

    def test_round_beyond_the_configured_total_is_rejected(
        self, client: TestClient, teacher_headers
    ):
        experiment = create_experiment(client, teacher_headers, rounds=3)
        add_participants(client, teacher_headers, experiment["id"], 2)
        match = start(client, teacher_headers, experiment["id"])["pairs"][0]
        response = submit(
            client, teacher_headers, experiment["id"], match["id"], 4, "COOPERATE", "COOPERATE"
        )
        assert response.status_code == 422

    def test_cannot_submit_before_start(self, client: TestClient, teacher_headers):
        experiment = create_experiment(client, teacher_headers)
        add_participants(client, teacher_headers, experiment["id"], 2)
        response = submit(
            client,
            teacher_headers,
            experiment["id"],
            "00000000-0000-0000-0000-000000000000",
            1,
            "COOPERATE",
            "COOPERATE",
        )
        assert response.status_code == 409

    def test_unknown_match_is_404(self, client: TestClient, teacher_headers):
        experiment = create_experiment(client, teacher_headers)
        add_participants(client, teacher_headers, experiment["id"], 2)
        start(client, teacher_headers, experiment["id"])
        response = submit(
            client,
            teacher_headers,
            experiment["id"],
            "00000000-0000-0000-0000-000000000000",
            1,
            "COOPERATE",
            "COOPERATE",
        )
        assert response.status_code == 404

    def test_invalid_action_is_422(self, client: TestClient, teacher_headers):
        experiment = create_experiment(client, teacher_headers)
        add_participants(client, teacher_headers, experiment["id"], 2)
        match = start(client, teacher_headers, experiment["id"])["pairs"][0]
        response = submit(
            client, teacher_headers, experiment["id"], match["id"], 1, "MAYBE", "COOPERATE"
        )
        assert response.status_code == 422

    def test_cannot_submit_after_completion(self, client: TestClient, teacher_headers):
        experiment = create_experiment(client, teacher_headers)
        add_participants(client, teacher_headers, experiment["id"], 2)
        match = start(client, teacher_headers, experiment["id"])["pairs"][0]
        client.post(
            f"/api/v1/experiments/{experiment['id']}/complete", headers=teacher_headers
        )
        response = submit(
            client, teacher_headers, experiment["id"], match["id"], 1, "COOPERATE", "COOPERATE"
        )
        assert response.status_code == 409


class TestExperimentStatistics:
    def _run_experiment(self, client: TestClient, headers: dict) -> str:
        experiment = create_experiment(client, headers, rounds=4)
        add_participants(client, headers, experiment["id"], 2)
        match = start(client, headers, experiment["id"])["pairs"][0]
        plays = [
            ("COOPERATE", "COOPERATE"),
            ("COOPERATE", "DEFECT"),
            ("DEFECT", "COOPERATE"),
            ("DEFECT", "DEFECT"),
        ]
        for index, (action_a, action_b) in enumerate(plays, start=1):
            submit(client, headers, experiment["id"], match["id"], index, action_a, action_b)
        return experiment["id"]

    def test_rates_are_computed(self, client: TestClient, teacher_headers):
        experiment_id = self._run_experiment(client, teacher_headers)
        data = client.get(f"/api/v1/experiments/{experiment_id}/statistics").json()["data"]

        assert data["rounds_recorded"] == 4
        assert data["decisions_recorded"] == 8
        assert data["cooperation_rate"] == 0.5
        assert data["defection_rate"] == 0.5
        assert data["mutual_cooperation_rate"] == 0.25
        assert data["mutual_defection_rate"] == 0.25
        assert data["cd_rate"] == 0.25
        assert data["dc_rate"] == 0.25

    def test_by_round_series_are_returned(self, client: TestClient, teacher_headers):
        experiment_id = self._run_experiment(client, teacher_headers)
        data = client.get(f"/api/v1/experiments/{experiment_id}/statistics").json()["data"]
        assert len(data["cooperation_rate_by_round"]) == 4
        assert data["cooperation_rate_by_round"][0]["cooperation_rate"] == 1.0
        assert data["cooperation_rate_by_round"][3]["cooperation_rate"] == 0.0

    def test_nash_prediction_flag_is_true_for_the_classic_matrix(
        self, client: TestClient, teacher_headers
    ):
        experiment_id = self._run_experiment(client, teacher_headers)
        data = client.get(f"/api/v1/experiments/{experiment_id}/statistics").json()["data"]
        assert data["nash_prediction_applies"] is True
        assert data["nash_prediction_cooperation_rate"] == 0.0

    def test_statistics_on_an_empty_experiment_are_zeroes(
        self, client: TestClient, teacher_headers
    ):
        experiment = create_experiment(client, teacher_headers)
        data = client.get(f"/api/v1/experiments/{experiment['id']}/statistics").json()["data"]
        assert data["rounds_recorded"] == 0
        assert data["cooperation_rate"] == 0.0

    def test_export_rounds_csv(self, client: TestClient, teacher_headers):
        experiment_id = self._run_experiment(client, teacher_headers)
        response = client.get(f"/api/v1/experiments/{experiment_id}/export/rounds.csv")
        assert response.status_code == 200
        lines = response.text.strip().splitlines()
        assert lines[0].startswith("pair_number,round_number")
        assert len(lines) == 5


class TestTrustSurvey:
    def _experiment_with_participants(self, client: TestClient, headers: dict):
        experiment = create_experiment(client, headers, rounds=2)
        participants = add_participants(client, headers, experiment["id"], 2)
        return experiment, participants

    def test_submit_a_survey_answer(self, client: TestClient, teacher_headers):
        experiment, participants = self._experiment_with_participants(
            client, teacher_headers
        )
        response = client.post(
            "/api/v1/surveys/trust",
            json={
                "experiment_id": experiment["id"],
                "participant_id": participants[0]["id"],
                "question_type": "EXPECTED_COOPERATION",
                "score": 4,
            },
            headers=teacher_headers,
        )
        assert response.status_code == 201
        assert response.json()["data"]["score"] == 4

    def test_score_outside_one_to_five_is_rejected(
        self, client: TestClient, teacher_headers
    ):
        experiment, participants = self._experiment_with_participants(
            client, teacher_headers
        )
        response = client.post(
            "/api/v1/surveys/trust",
            json={
                "experiment_id": experiment["id"],
                "participant_id": participants[0]["id"],
                "question_type": "TRUST_AFTER",
                "score": 9,
            },
            headers=teacher_headers,
        )
        assert response.status_code == 422

    def test_duplicate_answer_is_a_conflict(self, client: TestClient, teacher_headers):
        experiment, participants = self._experiment_with_participants(
            client, teacher_headers
        )
        payload = {
            "experiment_id": experiment["id"],
            "participant_id": participants[0]["id"],
            "question_type": "TRUST_AFTER",
            "score": 3,
        }
        client.post("/api/v1/surveys/trust", json=payload, headers=teacher_headers)
        second = client.post("/api/v1/surveys/trust", json=payload, headers=teacher_headers)
        assert second.status_code == 409

    def test_participant_from_another_experiment_is_404(
        self, client: TestClient, teacher_headers
    ):
        first, participants = self._experiment_with_participants(client, teacher_headers)
        other = create_experiment(client, teacher_headers, name="Other")
        response = client.post(
            "/api/v1/surveys/trust",
            json={
                "experiment_id": other["id"],
                "participant_id": participants[0]["id"],
                "question_type": "TRUST_AFTER",
                "score": 3,
            },
            headers=teacher_headers,
        )
        assert response.status_code == 404

    def test_survey_disabled_is_rejected(self, client: TestClient, teacher_headers):
        experiment = create_experiment(
            client, teacher_headers, trust_survey_enabled=False
        )
        participants = add_participants(client, teacher_headers, experiment["id"], 2)
        response = client.post(
            "/api/v1/surveys/trust",
            json={
                "experiment_id": experiment["id"],
                "participant_id": participants[0]["id"],
                "question_type": "TRUST_AFTER",
                "score": 3,
            },
            headers=teacher_headers,
        )
        assert response.status_code == 422

    def test_statistics_include_averages_and_the_caveat(
        self, client: TestClient, teacher_headers
    ):
        experiment, participants = self._experiment_with_participants(
            client, teacher_headers
        )
        for participant, score in zip(participants, (2, 4)):
            client.post(
                "/api/v1/surveys/trust",
                json={
                    "experiment_id": experiment["id"],
                    "participant_id": participant["id"],
                    "question_type": "EXPECTED_COOPERATION",
                    "score": score,
                },
                headers=teacher_headers,
            )

        data = client.get(
            f"/api/v1/experiments/{experiment['id']}/surveys/trust/statistics"
        ).json()["data"]
        assert data["responses"] == 2
        assert data["average_expected_cooperation"] == 3.0
        assert "do not establish that trust causes cooperation" in data["interpretation_note"]

    def test_correlation_is_null_with_too_few_responses(
        self, client: TestClient, teacher_headers
    ):
        experiment, participants = self._experiment_with_participants(
            client, teacher_headers
        )
        client.post(
            "/api/v1/surveys/trust",
            json={
                "experiment_id": experiment["id"],
                "participant_id": participants[0]["id"],
                "question_type": "EXPECTED_COOPERATION",
                "score": 5,
            },
            headers=teacher_headers,
        )
        data = client.get(
            f"/api/v1/experiments/{experiment['id']}/surveys/trust/statistics"
        ).json()["data"]
        assert data["correlation_expected_vs_actual"] is None

    def test_list_surveys_for_an_experiment(self, client: TestClient, teacher_headers):
        experiment, participants = self._experiment_with_participants(
            client, teacher_headers
        )
        client.post(
            "/api/v1/surveys/trust",
            json={
                "experiment_id": experiment["id"],
                "participant_id": participants[0]["id"],
                "question_type": "TRUST_AFTER",
                "score": 5,
            },
            headers=teacher_headers,
        )
        data = client.get(
            f"/api/v1/experiments/{experiment['id']}/surveys/trust"
        ).json()["data"]
        assert len(data) == 1
