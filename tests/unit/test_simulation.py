"""Iterated matches, tournaments, ranking and their edge cases.

Match outcomes are checked against hand calculations, so a regression in the
engine cannot hide behind self-consistent numbers.
"""

from __future__ import annotations

import pytest

from app.game_theory.actions import Action, Outcome
from app.game_theory.payoff import PayoffMatrix
from app.simulation.match import SimulationError, simulate_match
from app.simulation.tournament import build_rankings, run_tournament
from app.strategies.registry import UnknownStrategyError

C = Action.COOPERATE
D = Action.DEFECT

ALL_SIX = [
    "ALWAYS_COOPERATE",
    "ALWAYS_DEFECT",
    "TIT_FOR_TAT",
    "GRIM_TRIGGER",
    "TIT_FOR_TWO_TATS",
    "RANDOM",
]


class TestMatchArithmetic:
    """Every expected total here was worked out by hand from the matrix."""

    def test_mutual_cooperation_pays_the_reward_every_round(self, classic_matrix):
        result = simulate_match("ALWAYS_COOPERATE", "ALWAYS_COOPERATE", 10, classic_matrix)
        assert result.player_a.total_payoff == 30  # 10 x R
        assert result.player_b.total_payoff == 30

    def test_mutual_defection_pays_the_punishment_every_round(self, classic_matrix):
        result = simulate_match("ALWAYS_DEFECT", "ALWAYS_DEFECT", 10, classic_matrix)
        assert (result.player_a.total_payoff, result.player_b.total_payoff) == (10, 10)

    def test_total_exploitation(self, classic_matrix):
        result = simulate_match("ALWAYS_COOPERATE", "ALWAYS_DEFECT", 10, classic_matrix)
        assert result.player_a.total_payoff == 0  # 10 x S
        assert result.player_b.total_payoff == 50  # 10 x T

    def test_tit_for_tat_against_always_defect(self, classic_matrix):
        """Round 1 is (0,5); rounds 2-10 are (1,1). So 9 against 14."""
        result = simulate_match("TIT_FOR_TAT", "ALWAYS_DEFECT", 10, classic_matrix)
        assert result.player_a.total_payoff == 9
        assert result.player_b.total_payoff == 14
        assert [row.player_a_action for row in result.rounds] == [C] + [D] * 9

    def test_tit_for_tat_against_itself_cooperates_throughout(self, classic_matrix):
        result = simulate_match("TIT_FOR_TAT", "TIT_FOR_TAT", 100, classic_matrix)
        assert (result.player_a.total_payoff, result.player_b.total_payoff) == (300, 300)
        assert result.player_a.cooperation_rate == 1.0

    def test_grim_trigger_punishes_for_the_rest_of_the_match(self, classic_matrix):
        result = simulate_match("GRIM_TRIGGER", "ALWAYS_DEFECT", 10, classic_matrix)
        assert [row.player_a_action for row in result.rounds] == [C] + [D] * 9

    def test_tit_for_two_tats_stays_cooperative_against_a_nice_strategy(
        self, classic_matrix
    ):
        result = simulate_match("TIT_FOR_TWO_TATS", "GRIM_TRIGGER", 20, classic_matrix)
        assert (result.player_a.total_payoff, result.player_b.total_payoff) == (60, 60)

    def test_totals_equal_the_sum_of_the_round_payoffs(self, classic_matrix):
        result = simulate_match("TIT_FOR_TAT", "RANDOM", 50, classic_matrix, seed=3)
        assert result.player_a.total_payoff == sum(r.player_a_payoff for r in result.rounds)
        assert result.player_b.total_payoff == sum(r.player_b_payoff for r in result.rounds)

    def test_payoffs_follow_a_custom_matrix(self):
        matrix = PayoffMatrix.from_tuples(cc=(7, 7), cd=(0, 9), dc=(9, 0), dd=(2, 2))
        result = simulate_match("ALWAYS_COOPERATE", "ALWAYS_COOPERATE", 5, matrix)
        assert result.player_a.total_payoff == 35


class TestMatchStatistics:
    def test_cooperation_and_defection_counts(self, classic_matrix):
        result = simulate_match("TIT_FOR_TAT", "ALWAYS_DEFECT", 10, classic_matrix)
        assert result.player_a.cooperation_count == 1
        assert result.player_a.defection_count == 9
        assert result.player_a.cooperation_rate == pytest.approx(0.1)
        assert result.player_a.defection_rate == pytest.approx(0.9)

    def test_average_payoff(self, classic_matrix):
        result = simulate_match("ALWAYS_COOPERATE", "ALWAYS_COOPERATE", 10, classic_matrix)
        assert result.player_a.average_payoff == 3.0

    def test_outcome_counts_add_up_to_the_rounds_played(self, classic_matrix):
        result = simulate_match("TIT_FOR_TAT", "RANDOM", 60, classic_matrix, seed=11)
        assert sum(result.outcome_counts.values()) == result.rounds_played

    def test_winner_and_draw_detection(self, classic_matrix):
        exploited = simulate_match("ALWAYS_COOPERATE", "ALWAYS_DEFECT", 10, classic_matrix)
        assert exploited.winner == "ALWAYS_DEFECT"
        assert exploited.is_draw is False

        drawn = simulate_match("TIT_FOR_TAT", "TIT_FOR_TAT", 10, classic_matrix)
        assert drawn.winner is None
        assert drawn.is_draw is True

    def test_round_numbers_are_sequential_from_one(self, classic_matrix):
        result = simulate_match("TIT_FOR_TAT", "GRIM_TRIGGER", 15, classic_matrix)
        assert [row.round_number for row in result.rounds] == list(range(1, 16))

    def test_outcome_is_derived_from_the_two_actions(self, classic_matrix):
        result = simulate_match("ALWAYS_COOPERATE", "ALWAYS_DEFECT", 3, classic_matrix)
        assert all(row.outcome is Outcome.CD for row in result.rounds)


class TestReproducibility:
    def test_the_same_seed_gives_the_same_match(self, classic_matrix):
        first = simulate_match("RANDOM", "TIT_FOR_TAT", 100, classic_matrix, seed=42)
        second = simulate_match("RANDOM", "TIT_FOR_TAT", 100, classic_matrix, seed=42)
        assert first.player_a.total_payoff == second.player_a.total_payoff
        assert [r.player_a_action for r in first.rounds] == [
            r.player_a_action for r in second.rounds
        ]

    def test_different_seeds_give_different_matches(self, classic_matrix):
        first = simulate_match("RANDOM", "TIT_FOR_TAT", 100, classic_matrix, seed=1)
        second = simulate_match("RANDOM", "TIT_FOR_TAT", 100, classic_matrix, seed=2)
        assert first.player_a.total_payoff != second.player_a.total_payoff

    def test_deterministic_strategies_need_no_seed(self, classic_matrix):
        first = simulate_match("TIT_FOR_TAT", "GRIM_TRIGGER", 50, classic_matrix)
        second = simulate_match("TIT_FOR_TAT", "GRIM_TRIGGER", 50, classic_matrix)
        assert first.player_a.total_payoff == second.player_a.total_payoff


class TestContinuationProbability:
    def test_probability_of_one_plays_every_round(self, classic_matrix):
        result = simulate_match(
            "TIT_FOR_TAT", "TIT_FOR_TAT", 50, classic_matrix, continuation_probability=1.0
        )
        assert result.rounds_played == 50

    def test_probability_of_zero_stops_after_one_round(self, classic_matrix):
        result = simulate_match(
            "TIT_FOR_TAT", "TIT_FOR_TAT", 50, classic_matrix, continuation_probability=0.0
        )
        assert result.rounds_played == 1

    def test_intermediate_probability_stops_early_but_within_bounds(self, classic_matrix):
        result = simulate_match(
            "TIT_FOR_TAT",
            "TIT_FOR_TAT",
            1000,
            classic_matrix,
            seed=5,
            continuation_probability=0.9,
        )
        assert 1 <= result.rounds_played <= 1000
        assert result.rounds_played < 1000  # ends by chance long before the cap

    def test_length_is_reproducible_from_the_seed(self, classic_matrix):
        kwargs = dict(rounds=500, matrix=classic_matrix, continuation_probability=0.95)
        first = simulate_match("TIT_FOR_TAT", "TIT_FOR_TAT", seed=9, **kwargs)
        second = simulate_match("TIT_FOR_TAT", "TIT_FOR_TAT", seed=9, **kwargs)
        assert first.rounds_played == second.rounds_played

    def test_statistics_use_rounds_actually_played(self, classic_matrix):
        result = simulate_match(
            "ALWAYS_COOPERATE",
            "ALWAYS_COOPERATE",
            500,
            classic_matrix,
            seed=4,
            continuation_probability=0.8,
        )
        assert result.player_a.total_payoff == 3 * result.rounds_played
        assert result.player_a.average_payoff == 3.0


class TestMatchEdgeCases:
    def test_one_round_is_allowed(self, classic_matrix):
        assert simulate_match("TIT_FOR_TAT", "TIT_FOR_TAT", 1, classic_matrix).rounds_played == 1

    def test_zero_rounds_is_rejected(self, classic_matrix):
        with pytest.raises(SimulationError, match="at least 1"):
            simulate_match("TIT_FOR_TAT", "TIT_FOR_TAT", 0, classic_matrix)

    def test_negative_rounds_is_rejected(self, classic_matrix):
        with pytest.raises(SimulationError, match="at least 1"):
            simulate_match("TIT_FOR_TAT", "TIT_FOR_TAT", -5, classic_matrix)

    def test_absurd_round_count_is_rejected(self, classic_matrix):
        with pytest.raises(SimulationError, match="exceed"):
            simulate_match("TIT_FOR_TAT", "TIT_FOR_TAT", 10_001, classic_matrix)

    def test_unknown_strategy_is_rejected(self, classic_matrix):
        with pytest.raises(UnknownStrategyError):
            simulate_match("NOPE", "TIT_FOR_TAT", 10, classic_matrix)

    def test_out_of_range_continuation_probability_is_rejected(self, classic_matrix):
        with pytest.raises(SimulationError, match="between 0 and 1"):
            simulate_match(
                "TIT_FOR_TAT", "TIT_FOR_TAT", 10, classic_matrix, continuation_probability=1.5
            )

    def test_a_strategy_can_play_itself(self, classic_matrix):
        result = simulate_match("GRIM_TRIGGER", "GRIM_TRIGGER", 10, classic_matrix)
        assert result.player_a.total_payoff == result.player_b.total_payoff == 30


class TestTournament:
    def test_every_pair_meets_once(self, classic_matrix):
        result = run_tournament(ALL_SIX, 20, classic_matrix, seed=1)
        assert len(result.matches) == 15  # 6 choose 2

    def test_no_self_play_by_default(self, classic_matrix):
        result = run_tournament(ALL_SIX, 10, classic_matrix, seed=1)
        assert all(m.strategy_a_id != m.strategy_b_id for m in result.matches)

    def test_self_play_can_be_enabled(self, classic_matrix):
        result = run_tournament(ALL_SIX, 10, classic_matrix, seed=1, include_self_play=True)
        assert len(result.matches) == 15 + 6

    def test_repetitions_multiply_the_matches(self, classic_matrix):
        result = run_tournament(ALL_SIX, 10, classic_matrix, seed=1, repetitions=3)
        assert len(result.matches) == 45

    def test_every_strategy_gets_a_record(self, classic_matrix):
        result = run_tournament(ALL_SIX, 20, classic_matrix, seed=1)
        assert len(result.rankings) == 6
        assert {r.strategy_id for r in result.rankings} == set(ALL_SIX)

    def test_match_counts_per_strategy(self, classic_matrix):
        result = run_tournament(ALL_SIX, 10, classic_matrix, seed=1)
        for ranking in result.rankings:
            assert ranking.matches_played == 5
            assert ranking.wins + ranking.draws + ranking.losses == 5

    def test_run_is_reproducible(self, classic_matrix):
        first = run_tournament(ALL_SIX, 50, classic_matrix, seed=7)
        second = run_tournament(ALL_SIX, 50, classic_matrix, seed=7)
        assert [r.total_score for r in first.rankings] == [
            r.total_score for r in second.rankings
        ]

    def test_known_extreme_cooperation_rates(self, classic_matrix):
        result = run_tournament(ALL_SIX, 100, classic_matrix, seed=42)
        rates = {r.strategy_id: r.cooperation_rate for r in result.rankings}
        assert rates["ALWAYS_COOPERATE"] == 1.0
        assert rates["ALWAYS_DEFECT"] == 0.0

    def test_scores_are_consistent_with_the_matches(self, classic_matrix):
        result = run_tournament(ALL_SIX, 30, classic_matrix, seed=2)
        for ranking in result.rankings:
            expected = sum(
                match.player_a.total_payoff
                if match.strategy_a_id == ranking.strategy_id
                else match.player_b.total_payoff
                for match in result.matches
                if ranking.strategy_id in (match.strategy_a_id, match.strategy_b_id)
            )
            assert ranking.total_score == expected

    def test_average_score_is_total_over_rounds(self, classic_matrix):
        result = run_tournament(ALL_SIX, 25, classic_matrix, seed=8)
        for ranking in result.rankings:
            assert ranking.average_score == pytest.approx(
                ranking.total_score / ranking.rounds_played
            )

    def test_cooperation_and_defection_rates_are_complementary(self, classic_matrix):
        result = run_tournament(ALL_SIX, 40, classic_matrix, seed=6)
        for ranking in result.rankings:
            assert ranking.cooperation_rate + ranking.defection_rate == pytest.approx(1.0)


class TestRanking:
    def test_ranked_by_total_score_descending(self, classic_matrix):
        result = run_tournament(ALL_SIX, 100, classic_matrix, seed=42)
        scores = [r.total_score for r in result.rankings]
        assert scores == sorted(scores, reverse=True)
        assert result.rankings[0].rank == 1

    def test_winner_matches_the_top_of_the_table(self, classic_matrix):
        result = run_tournament(ALL_SIX, 100, classic_matrix, seed=42)
        assert result.winner_id == result.rankings[0].strategy_id

    def test_tied_scores_share_a_rank_and_break_deterministically(self):
        from app.simulation.tournament import StrategyRecord

        records = {
            "B_STRATEGY": StrategyRecord("B_STRATEGY", total_score=100, rounds_played=50,
                                         matches_played=1, cooperation_count=25,
                                         defection_count=25),
            "A_STRATEGY": StrategyRecord("A_STRATEGY", total_score=100, rounds_played=50,
                                         matches_played=1, cooperation_count=25,
                                         defection_count=25),
            "C_STRATEGY": StrategyRecord("C_STRATEGY", total_score=50, rounds_played=50,
                                         matches_played=1, cooperation_count=25,
                                         defection_count=25),
        }
        rankings = build_rankings(records)
        assert [r.strategy_id for r in rankings] == [
            "A_STRATEGY",
            "B_STRATEGY",
            "C_STRATEGY",
        ]
        assert [r.rank for r in rankings] == [1, 1, 3]

    def test_ranking_is_not_hard_coded_to_a_strategy(self):
        """With a matrix that rewards cooperation, the order changes."""
        cooperative_matrix = PayoffMatrix.from_tuples(
            cc=(10, 10), cd=(8, 0), dc=(0, 8), dd=(1, 1)
        )
        result = run_tournament(ALL_SIX, 100, cooperative_matrix, seed=42)
        assert result.winner_id == "ALWAYS_COOPERATE"

        classic = run_tournament(ALL_SIX, 100, PayoffMatrix.classic(), seed=42)
        assert classic.winner_id != "ALWAYS_COOPERATE"


class TestTournamentEdgeCases:
    def test_empty_strategy_list_is_rejected(self, classic_matrix):
        with pytest.raises(SimulationError, match="at least one strategy"):
            run_tournament([], 10, classic_matrix)

    def test_single_strategy_without_self_play_is_rejected(self, classic_matrix):
        with pytest.raises(SimulationError, match="at least two strategies"):
            run_tournament(["TIT_FOR_TAT"], 10, classic_matrix)

    def test_single_strategy_with_self_play_is_allowed(self, classic_matrix):
        result = run_tournament(["TIT_FOR_TAT"], 10, classic_matrix, include_self_play=True)
        assert len(result.matches) == 1

    def test_duplicate_strategies_are_rejected(self, classic_matrix):
        with pytest.raises(SimulationError, match="[Dd]uplicate"):
            run_tournament(["TIT_FOR_TAT", "TIT_FOR_TAT"], 10, classic_matrix)

    def test_unknown_strategy_is_rejected(self, classic_matrix):
        with pytest.raises(UnknownStrategyError):
            run_tournament(["TIT_FOR_TAT", "NOT_REAL"], 10, classic_matrix)

    def test_zero_rounds_is_rejected(self, classic_matrix):
        with pytest.raises(SimulationError, match="at least 1"):
            run_tournament(ALL_SIX, 0, classic_matrix)

    def test_zero_repetitions_is_rejected(self, classic_matrix):
        with pytest.raises(SimulationError, match="at least 1"):
            run_tournament(ALL_SIX, 10, classic_matrix, repetitions=0)

    def test_strategy_ids_are_normalised_to_upper_case(self, classic_matrix):
        result = run_tournament(["tit_for_tat", "always_defect"], 10, classic_matrix)
        assert {r.strategy_id for r in result.rankings} == {
            "TIT_FOR_TAT",
            "ALWAYS_DEFECT",
        }
