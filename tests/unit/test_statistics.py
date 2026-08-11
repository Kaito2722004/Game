"""Descriptive statistics, experiment statistics and trust-survey statistics."""

from __future__ import annotations

import pytest

from app.game_theory.actions import Action
from app.simulation.match import simulate_match
from app.simulation.tournament import run_tournament
from app.statistics.analysis import (
    cooperation_by_round,
    cumulative_scores,
    describe,
    head_to_head_matrix,
    outcome_frequency,
    outcome_rates,
    pearson_correlation,
    tournament_statistics,
)
from app.statistics.experiment_analysis import (
    HumanRoundRecord,
    TrustSurveyRecord,
    cooperation_rate_by_participant,
    experiment_statistics,
    trust_survey_statistics,
)

C = Action.COOPERATE
D = Action.DEFECT


def make_round(number: int, action_a: Action, action_b: Action) -> HumanRoundRecord:
    payoffs = {(C, C): (3, 3), (C, D): (0, 5), (D, C): (5, 0), (D, D): (1, 1)}
    payoff_a, payoff_b = payoffs[(action_a, action_b)]
    return HumanRoundRecord(
        round_number=number,
        player_a_action=action_a,
        player_b_action=action_b,
        player_a_payoff=payoff_a,
        player_b_payoff=payoff_b,
        match_id="match-1",
        player_a_id="participant-a",
        player_b_id="participant-b",
    )


class TestDescribe:
    def test_basic_statistics(self):
        stats = describe([1, 2, 3, 4, 5])
        assert stats.count == 5
        assert stats.mean == 3.0
        assert stats.median == 3.0
        assert stats.minimum == 1.0
        assert stats.maximum == 5.0
        assert stats.total == 15.0
        assert stats.standard_deviation == pytest.approx(1.5811, abs=1e-4)

    def test_empty_series_is_all_zero(self):
        stats = describe([])
        assert stats.count == 0 and stats.mean == 0.0 and stats.standard_deviation == 0.0

    def test_single_value_has_zero_deviation(self):
        assert describe([7]).standard_deviation == 0.0

    def test_median_of_an_even_length_series(self):
        assert describe([1, 2, 3, 4]).median == 2.5


class TestCorrelation:
    def test_perfect_positive_correlation(self):
        assert pearson_correlation([1, 2, 3, 4], [2, 4, 6, 8]) == pytest.approx(1.0)

    def test_perfect_negative_correlation(self):
        assert pearson_correlation([1, 2, 3, 4], [8, 6, 4, 2]) == pytest.approx(-1.0)

    def test_too_few_points_returns_none(self):
        assert pearson_correlation([1, 2], [3, 4]) is None

    def test_constant_series_returns_none(self):
        assert pearson_correlation([2, 2, 2, 2], [1, 2, 3, 4]) is None


class TestSimulationStatistics:
    def test_cumulative_scores_end_at_the_totals(self, classic_matrix):
        result = simulate_match("TIT_FOR_TAT", "RANDOM", 30, classic_matrix, seed=3)
        cumulative = cumulative_scores(result)
        assert len(cumulative) == 30
        assert cumulative[-1]["player_a_cumulative"] == result.player_a.total_payoff
        assert cumulative[-1]["player_b_cumulative"] == result.player_b.total_payoff

    def test_outcome_frequency_counts_every_round(self, classic_matrix):
        result = simulate_match("ALWAYS_COOPERATE", "ALWAYS_DEFECT", 10, classic_matrix)
        counts = outcome_frequency([result])
        assert counts["CD"] == 10
        assert sum(counts.values()) == 10

    def test_outcome_rates_sum_to_one(self, classic_matrix):
        result = run_tournament(
            ["TIT_FOR_TAT", "ALWAYS_DEFECT", "RANDOM"], 40, classic_matrix, seed=2
        )
        assert sum(outcome_rates(result.matches).values()) == pytest.approx(1.0)

    def test_cooperation_by_round_starts_high_for_nice_strategies(self, classic_matrix):
        result = run_tournament(
            ["TIT_FOR_TAT", "GRIM_TRIGGER", "ALWAYS_DEFECT"], 20, classic_matrix, seed=1
        )
        series = cooperation_by_round(result.matches)
        assert len(series) == 20
        assert series[0]["cooperation_rate"] > series[-1]["cooperation_rate"]

    def test_head_to_head_covers_every_ordered_pair(self, classic_matrix):
        result = run_tournament(
            ["TIT_FOR_TAT", "ALWAYS_DEFECT", "ALWAYS_COOPERATE"], 10, classic_matrix, seed=1
        )
        entries = head_to_head_matrix(result)
        assert len(entries) == 6  # 3 pairs, both directions

    def test_head_to_head_values_are_hand_checkable(self, classic_matrix):
        result = run_tournament(
            ["ALWAYS_COOPERATE", "ALWAYS_DEFECT"], 10, classic_matrix, seed=1
        )
        lookup = {
            (row["strategy_id"], row["opponent_id"]): row["average_payoff"]
            for row in head_to_head_matrix(result)
        }
        assert lookup[("ALWAYS_DEFECT", "ALWAYS_COOPERATE")] == 5.0
        assert lookup[("ALWAYS_COOPERATE", "ALWAYS_DEFECT")] == 0.0

    def test_tournament_statistics_payload(self, classic_matrix):
        result = run_tournament(
            ["TIT_FOR_TAT", "ALWAYS_DEFECT", "RANDOM"], 25, classic_matrix, seed=4
        )
        payload = tournament_statistics(result)
        assert payload["matches_played"] == 3
        assert payload["score_statistics"].count == 3
        assert len(payload["cooperation_by_round"]) == 25


class TestExperimentStatistics:
    def test_empty_experiment_reports_zeroes(self):
        stats = experiment_statistics([])
        assert stats["rounds_recorded"] == 0
        assert stats["cooperation_rate"] == 0.0
        assert stats["cooperation_rate_by_round"] == []

    def test_all_mutual_cooperation(self):
        rounds = [make_round(n, C, C) for n in range(1, 6)]
        stats = experiment_statistics(rounds)
        assert stats["cooperation_rate"] == 1.0
        assert stats["defection_rate"] == 0.0
        assert stats["mutual_cooperation_rate"] == 1.0
        assert stats["mutual_defection_rate"] == 0.0
        assert stats["average_payoff"] == 3.0

    def test_mixed_outcomes(self):
        rounds = [
            make_round(1, C, C),
            make_round(2, C, D),
            make_round(3, D, C),
            make_round(4, D, D),
        ]
        stats = experiment_statistics(rounds)
        assert stats["decisions_recorded"] == 8
        assert stats["cooperation_rate"] == 0.5
        assert stats["mutual_cooperation_rate"] == 0.25
        assert stats["mutual_defection_rate"] == 0.25
        assert stats["cd_rate"] == 0.25
        assert stats["dc_rate"] == 0.25
        assert stats["total_payoff"] == 3 + 3 + 0 + 5 + 5 + 0 + 1 + 1

    def test_cooperation_by_round_series(self):
        rounds = [make_round(1, C, C), make_round(2, C, D), make_round(3, D, D)]
        series = {row["round_number"]: row["cooperation_rate"] for row in
                  experiment_statistics(rounds)["cooperation_rate_by_round"]}
        assert series == {1: 1.0, 2: 0.5, 3: 0.0}

    def test_defection_rates_complement_cooperation_rates(self):
        rounds = [make_round(1, C, D), make_round(2, D, D)]
        stats = experiment_statistics(rounds)
        for coop, defect in zip(
            stats["cooperation_rate_by_round"], stats["defection_rate_by_round"]
        ):
            assert coop["cooperation_rate"] + defect["defection_rate"] == pytest.approx(1.0)

    def test_outcome_frequency_totals_the_rounds(self):
        rounds = [make_round(1, C, C), make_round(2, D, D), make_round(3, D, D)]
        counts = experiment_statistics(rounds)["outcome_frequency"]
        assert counts["CC"] == 1 and counts["DD"] == 2
        assert sum(counts.values()) == 3

    def test_cooperation_rate_by_participant(self):
        rounds = [make_round(1, C, D), make_round(2, C, D)]
        rates = cooperation_rate_by_participant(rounds)
        assert rates["participant-a"] == 1.0
        assert rates["participant-b"] == 0.0


class TestTrustSurveyStatistics:
    def test_no_responses(self):
        stats = trust_survey_statistics([], {})
        assert stats["responses"] == 0
        assert stats["average_expected_cooperation"] is None
        assert stats["correlation_expected_vs_actual"] is None

    def test_averages(self):
        surveys = [
            TrustSurveyRecord("p1", "EXPECTED_COOPERATION", 4),
            TrustSurveyRecord("p2", "EXPECTED_COOPERATION", 2),
            TrustSurveyRecord("p1", "TRUST_AFTER", 5),
        ]
        stats = trust_survey_statistics(surveys, {"p1": 1.0, "p2": 0.0})
        assert stats["responses"] == 3
        assert stats["average_expected_cooperation"] == 3.0
        assert stats["average_trust_after"] == 5.0

    def test_correlation_with_cooperation(self):
        surveys = [
            TrustSurveyRecord(f"p{i}", "EXPECTED_COOPERATION", score)
            for i, score in enumerate([1, 2, 3, 4, 5], start=1)
        ]
        cooperation = {f"p{i}": rate for i, rate in enumerate([0.0, 0.25, 0.5, 0.75, 1.0], start=1)}
        stats = trust_survey_statistics(surveys, cooperation)
        assert stats["correlation_expected_vs_actual"] == pytest.approx(1.0)

    def test_response_always_carries_the_no_causation_note(self):
        stats = trust_survey_statistics([], {})
        assert "do not establish that trust causes cooperation" in stats["interpretation_note"]
