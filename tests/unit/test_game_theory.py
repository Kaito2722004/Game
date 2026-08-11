"""Payoff arithmetic, dilemma conditions, dominance, Nash and Pareto.

The classic matrix results are asserted here explicitly, but the same
functions are exercised against non-dilemma matrices to prove nothing is
hard-coded.
"""

from __future__ import annotations

import pytest

from app.game_theory.actions import Action, DominanceType, Outcome, Player
from app.game_theory.analysis import analyse_game, check_dilemma_conditions
from app.game_theory.equilibrium import find_dominant_strategy, find_nash_equilibria
from app.game_theory.pareto import (
    analyse_pareto,
    mutual_cooperation_dominates_mutual_defection,
)
from app.game_theory.payoff import PayoffMatrix


# --------------------------------------------------------------- payoffs ----
class TestPayoffCalculation:
    def test_all_four_cells(self, classic_matrix: PayoffMatrix):
        assert classic_matrix.payoff(Action.COOPERATE, Action.COOPERATE) == (3, 3)
        assert classic_matrix.payoff(Action.COOPERATE, Action.DEFECT) == (0, 5)
        assert classic_matrix.payoff(Action.DEFECT, Action.COOPERATE) == (5, 0)
        assert classic_matrix.payoff(Action.DEFECT, Action.DEFECT) == (1, 1)

    def test_payoff_is_symmetric_under_seat_swap(self, classic_matrix: PayoffMatrix):
        for action_a in Action:
            for action_b in Action:
                forward = classic_matrix.payoff(action_a, action_b)
                reverse = classic_matrix.payoff(action_b, action_a)
                assert forward == tuple(reversed(reverse))

    def test_payoff_for_works_from_either_seat(self, classic_matrix: PayoffMatrix):
        # A defecting against a cooperator earns T=5, and so does B.
        assert classic_matrix.payoff_for(True, Action.DEFECT, Action.COOPERATE) == 5
        assert classic_matrix.payoff_for(False, Action.DEFECT, Action.COOPERATE) == 5

    def test_classic_matrix_is_symmetric(self, classic_matrix: PayoffMatrix):
        assert classic_matrix.is_symmetric is True

    def test_asymmetric_matrix_is_detected(self):
        matrix = PayoffMatrix.from_tuples(cc=(3, 2), cd=(0, 5), dc=(5, 0), dd=(1, 1))
        assert matrix.is_symmetric is False


# ------------------------------------------------------------- conditions ----
class TestDilemmaConditions:
    def test_classic_matrix_is_a_prisoners_dilemma(self, classic_matrix: PayoffMatrix):
        conditions = check_dilemma_conditions(classic_matrix)
        assert conditions.is_prisoners_dilemma is True
        assert conditions.ordering_holds is True
        assert conditions.averaging_condition_holds is True
        assert conditions.failed_conditions == []

    def test_trps_values_are_extracted(self, classic_matrix: PayoffMatrix):
        ordering = check_dilemma_conditions(classic_matrix).player_a_ordering
        assert (ordering.temptation, ordering.reward) == (5, 3)
        assert (ordering.punishment, ordering.sucker) == (1, 0)

    def test_both_players_get_the_same_ordering_in_a_symmetric_game(
        self, classic_matrix: PayoffMatrix
    ):
        conditions = check_dilemma_conditions(classic_matrix)
        a, b = conditions.player_a_ordering, conditions.player_b_ordering
        assert (a.temptation, a.reward, a.punishment, a.sucker) == (
            b.temptation,
            b.reward,
            b.punishment,
            b.sucker,
        )

    def test_ordering_failure_is_reported(self):
        # R > T, so defection is no longer tempting: not a dilemma.
        matrix = PayoffMatrix.from_tuples(cc=(5, 5), cd=(0, 3), dc=(3, 0), dd=(1, 1))
        conditions = check_dilemma_conditions(matrix)
        assert conditions.is_prisoners_dilemma is False
        assert conditions.ordering_holds is False
        assert any("T > R > P > S" in reason for reason in conditions.failed_conditions)

    def test_averaging_condition_can_fail_alone(self):
        # T=10, R=3, P=1, S=0: ordering holds but R < (S+T)/2 = 5.
        matrix = PayoffMatrix.from_tuples(cc=(3, 3), cd=(0, 10), dc=(10, 0), dd=(1, 1))
        conditions = check_dilemma_conditions(matrix)
        assert conditions.ordering_holds is True
        assert conditions.averaging_condition_holds is False
        assert conditions.is_prisoners_dilemma is False


# --------------------------------------------------------------- dominance ----
class TestDominantStrategy:
    def test_defect_strictly_dominates_for_both_players(
        self, classic_matrix: PayoffMatrix
    ):
        for player in (Player.A, Player.B):
            dominant = find_dominant_strategy(classic_matrix, player)
            assert dominant.exists is True
            assert dominant.action is Action.DEFECT
            assert dominant.dominance is DominanceType.STRICT

    def test_explanation_cites_both_comparisons(self, classic_matrix: PayoffMatrix):
        explanation = find_dominant_strategy(classic_matrix, Player.A).explanation
        assert "COOPERATE" in explanation and "DEFECT" in explanation

    def test_cooperation_dominates_when_the_payoffs_say_so(self):
        matrix = PayoffMatrix.from_tuples(cc=(5, 5), cd=(3, 1), dc=(1, 3), dd=(0, 0))
        dominant = find_dominant_strategy(matrix, Player.A)
        assert dominant.action is Action.COOPERATE
        assert dominant.dominance is DominanceType.STRICT

    def test_no_dominant_action_in_a_coordination_game(self):
        # Stag hunt: the best action depends on what the other player does.
        matrix = PayoffMatrix.from_tuples(cc=(4, 4), cd=(0, 3), dc=(3, 0), dd=(2, 2))
        dominant = find_dominant_strategy(matrix, Player.A)
        assert dominant.exists is False
        assert dominant.action is None

    def test_weak_dominance_is_labelled_as_such(self):
        # Defect ties when the opponent cooperates and wins when they defect.
        matrix = PayoffMatrix.from_tuples(cc=(3, 3), cd=(0, 5), dc=(3, 0), dd=(1, 1))
        dominant = find_dominant_strategy(matrix, Player.A)
        assert dominant.action is Action.DEFECT
        assert dominant.dominance is DominanceType.WEAK


# ------------------------------------------------------------------- nash ----
class TestNashEquilibrium:
    def test_mutual_defection_is_the_unique_equilibrium(
        self, classic_matrix: PayoffMatrix
    ):
        equilibria = find_nash_equilibria(classic_matrix)
        assert len(equilibria) == 1
        assert equilibria[0].outcome is Outcome.DD
        assert (equilibria[0].player_a_payoff, equilibria[0].player_b_payoff) == (1, 1)

    def test_equilibrium_explanation_mentions_both_deviations(
        self, classic_matrix: PayoffMatrix
    ):
        explanation = find_nash_equilibria(classic_matrix)[0].explanation
        assert "A switching alone" in explanation
        assert "B switching alone" in explanation

    def test_coordination_game_has_two_equilibria(self):
        matrix = PayoffMatrix.from_tuples(cc=(4, 4), cd=(0, 3), dc=(3, 0), dd=(2, 2))
        outcomes = {eq.outcome for eq in find_nash_equilibria(matrix)}
        assert outcomes == {Outcome.CC, Outcome.DD}

    def test_matching_pennies_has_no_pure_equilibrium(self):
        matrix = PayoffMatrix.from_tuples(cc=(1, -1), cd=(-1, 1), dc=(-1, 1), dd=(1, -1))
        assert find_nash_equilibria(matrix) == []

    def test_every_cell_can_be_an_equilibrium_when_payoffs_are_flat(self):
        matrix = PayoffMatrix.from_tuples(cc=(1, 1), cd=(1, 1), dc=(1, 1), dd=(1, 1))
        assert len(find_nash_equilibria(matrix)) == 4


# ----------------------------------------------------------------- pareto ----
class TestParetoAnalysis:
    def test_mutual_defection_is_pareto_inferior(self, classic_matrix: PayoffMatrix):
        statuses = {status.outcome: status for status in analyse_pareto(classic_matrix)}
        assert statuses[Outcome.DD].is_pareto_optimal is False
        assert Outcome.CC in statuses[Outcome.DD].dominated_by

    def test_the_other_three_outcomes_are_pareto_optimal(
        self, classic_matrix: PayoffMatrix
    ):
        optimal = {
            status.outcome
            for status in analyse_pareto(classic_matrix)
            if status.is_pareto_optimal
        }
        assert optimal == {Outcome.CC, Outcome.CD, Outcome.DC}

    def test_mutual_cooperation_pareto_dominates_mutual_defection(
        self, classic_matrix: PayoffMatrix
    ):
        assert mutual_cooperation_dominates_mutual_defection(classic_matrix) is True

    def test_cc_does_not_dominate_dd_when_payoffs_are_reversed(self):
        matrix = PayoffMatrix.from_tuples(cc=(1, 1), cd=(0, 5), dc=(5, 0), dd=(3, 3))
        assert mutual_cooperation_dominates_mutual_defection(matrix) is False


# ------------------------------------------------------- the whole analysis ----
class TestFullAnalysis:
    def test_the_three_textbook_results_for_the_classic_matrix(
        self, classic_matrix: PayoffMatrix
    ):
        """The three results the project must demonstrate, all computed."""
        analysis = analyse_game(classic_matrix)

        # 1. Defection is dominant for both players.
        assert analysis.dominant_strategy_a.action is Action.DEFECT
        assert analysis.dominant_strategy_b.action is Action.DEFECT

        # 2. (D,D) is a Nash equilibrium.
        assert [eq.outcome for eq in analysis.nash_equilibria] == [Outcome.DD]

        # 3. (C,C) Pareto-dominates (D,D), so the equilibrium is Pareto-inferior.
        assert analysis.mutual_cooperation_pareto_superior is True
        assert analysis.equilibrium_is_pareto_inferior is True

    def test_summary_describes_the_dilemma(self, classic_matrix: PayoffMatrix):
        summary = analyse_game(classic_matrix).summary
        assert "satisfies the Prisoner's Dilemma conditions" in summary
        assert "Pareto-inferior" in summary

    def test_non_dilemma_matrix_produces_a_different_analysis(self):
        matrix = PayoffMatrix.from_tuples(cc=(4, 4), cd=(0, 3), dc=(3, 0), dd=(2, 2))
        analysis = analyse_game(matrix)
        assert analysis.conditions.is_prisoners_dilemma is False
        assert analysis.dominant_strategy_a.exists is False
        assert analysis.equilibrium_is_pareto_inferior is True  # (D,D) is dominated by (C,C)
        assert "not a Prisoner's Dilemma" in analysis.summary

    @pytest.mark.parametrize(
        "cc,cd,dc,dd,expected",
        [
            ((3, 3), (0, 5), (5, 0), (1, 1), True),
            ((3, 3), (0, 10), (10, 0), (1, 1), False),  # averaging condition fails
            ((5, 5), (0, 3), (3, 0), (1, 1), False),  # ordering fails
            ((2, 2), (1, 3), (3, 1), (0, 0), False),  # P < S
        ],
    )
    def test_condition_detection_across_matrices(self, cc, cd, dc, dd, expected):
        matrix = PayoffMatrix.from_tuples(cc=cc, cd=cd, dc=dc, dd=dd)
        assert analyse_game(matrix).conditions.is_prisoners_dilemma is expected
