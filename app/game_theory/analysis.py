"""Full game-theoretic analysis of a 2x2 matrix.

This module answers, from the numbers alone:

* is this matrix a Prisoner's Dilemma?
* what are T, R, P and S?
* does either player have a dominant action?
* which cells are pure-strategy Nash equilibria?
* which outcomes are Pareto-optimal, and which Pareto-inferior?
* is mutual cooperation Pareto-superior to mutual defection?

Nothing is hard-coded. Feeding in a non-dilemma matrix produces a
correspondingly different answer, which is the point: the classic result is a
consequence of the payoff ordering, not an assumption of the software.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.game_theory.actions import Action, Outcome, Player
from app.game_theory.equilibrium import (
    DominantStrategy,
    NashEquilibrium,
    find_dominant_strategy,
    find_nash_equilibria,
)
from app.game_theory.pareto import (
    ParetoStatus,
    analyse_pareto,
    mutual_cooperation_dominates_mutual_defection,
)
from app.game_theory.payoff import PayoffMatrix


@dataclass(frozen=True)
class PayoffOrdering:
    """T, R, P and S as seen by one player.

    T is the temptation payoff for defecting against a cooperator, R the
    reward for mutual cooperation, P the punishment for mutual defection, and
    S the sucker's payoff for cooperating against a defector.
    """

    player: Player
    temptation: float
    reward: float
    punishment: float
    sucker: float

    @property
    def ordering_holds(self) -> bool:
        """T > R > P > S."""
        return self.temptation > self.reward > self.punishment > self.sucker

    @property
    def averaging_condition_holds(self) -> bool:
        """R > (S + T) / 2.

        Without this, players alternating between exploiting each other would
        do better than steady mutual cooperation, and the repeated game would
        have a different character.
        """
        return self.reward > (self.sucker + self.temptation) / 2


@dataclass(frozen=True)
class DilemmaConditions:
    """Whether the matrix meets the definition of a Prisoner's Dilemma."""

    is_prisoners_dilemma: bool
    ordering_holds: bool
    averaging_condition_holds: bool
    is_symmetric: bool
    player_a_ordering: PayoffOrdering
    player_b_ordering: PayoffOrdering
    failed_conditions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GameAnalysis:
    """Everything the analysis engine can say about one matrix."""

    matrix: PayoffMatrix
    conditions: DilemmaConditions
    dominant_strategy_a: DominantStrategy
    dominant_strategy_b: DominantStrategy
    nash_equilibria: list[NashEquilibrium]
    pareto: list[ParetoStatus]
    mutual_cooperation_pareto_superior: bool
    equilibrium_is_pareto_inferior: bool
    summary: str


def _ordering_for(matrix: PayoffMatrix, player: Player) -> PayoffOrdering:
    """Extract T, R, P, S for one player from that player's own perspective."""
    if player is Player.A:
        temptation = matrix.dc.player_a  # A defects, B cooperates
        reward = matrix.cc.player_a
        punishment = matrix.dd.player_a
        sucker = matrix.cd.player_a  # A cooperates, B defects
    else:
        temptation = matrix.cd.player_b  # B defects, A cooperates
        reward = matrix.cc.player_b
        punishment = matrix.dd.player_b
        sucker = matrix.dc.player_b
    return PayoffOrdering(
        player=player,
        temptation=temptation,
        reward=reward,
        punishment=punishment,
        sucker=sucker,
    )


def check_dilemma_conditions(matrix: PayoffMatrix) -> DilemmaConditions:
    """Test the matrix against the definition of a Prisoner's Dilemma.

    Both players must face T > R > P > S and R > (S + T) / 2.
    """
    ordering_a = _ordering_for(matrix, Player.A)
    ordering_b = _ordering_for(matrix, Player.B)

    ordering_holds = ordering_a.ordering_holds and ordering_b.ordering_holds
    averaging_holds = (
        ordering_a.averaging_condition_holds and ordering_b.averaging_condition_holds
    )

    failed: list[str] = []
    for ordering in (ordering_a, ordering_b):
        label = f"player {ordering.player.value}"
        if not ordering.ordering_holds:
            failed.append(
                f"T > R > P > S fails for {label}: "
                f"T={ordering.temptation:g}, R={ordering.reward:g}, "
                f"P={ordering.punishment:g}, S={ordering.sucker:g}"
            )
        if not ordering.averaging_condition_holds:
            failed.append(
                f"R > (S + T) / 2 fails for {label}: "
                f"R={ordering.reward:g}, (S + T) / 2="
                f"{(ordering.sucker + ordering.temptation) / 2:g}"
            )

    return DilemmaConditions(
        is_prisoners_dilemma=ordering_holds and averaging_holds,
        ordering_holds=ordering_holds,
        averaging_condition_holds=averaging_holds,
        is_symmetric=matrix.is_symmetric,
        player_a_ordering=ordering_a,
        player_b_ordering=ordering_b,
        failed_conditions=failed,
    )


def _build_summary(
    conditions: DilemmaConditions,
    dominant_a: DominantStrategy,
    dominant_b: DominantStrategy,
    equilibria: list[NashEquilibrium],
    equilibrium_is_pareto_inferior: bool,
) -> str:
    parts: list[str] = []

    if conditions.is_prisoners_dilemma:
        parts.append("This matrix satisfies the Prisoner's Dilemma conditions.")
    else:
        parts.append("This matrix is not a Prisoner's Dilemma.")

    if dominant_a.exists and dominant_b.exists:
        parts.append(
            f"Player A has a dominant action ({dominant_a.action.value}) and player B "
            f"has a dominant action ({dominant_b.action.value})."
        )
    elif dominant_a.exists or dominant_b.exists:
        who = "A" if dominant_a.exists else "B"
        action = dominant_a.action if dominant_a.exists else dominant_b.action
        parts.append(f"Only player {who} has a dominant action ({action.value}).")
    else:
        parts.append("Neither player has a dominant action.")

    if equilibria:
        cells = ", ".join(eq.outcome.value for eq in equilibria)
        parts.append(f"Pure-strategy Nash equilibria: {cells}.")
    else:
        parts.append("There is no pure-strategy Nash equilibrium.")

    if equilibrium_is_pareto_inferior:
        parts.append(
            "At least one equilibrium is Pareto-inferior, so individual rationality "
            "and collective benefit point to different outcomes."
        )

    return " ".join(parts)


def analyse_game(matrix: PayoffMatrix) -> GameAnalysis:
    """Run every analysis in this package against one matrix."""
    conditions = check_dilemma_conditions(matrix)
    dominant_a = find_dominant_strategy(matrix, Player.A)
    dominant_b = find_dominant_strategy(matrix, Player.B)
    equilibria = find_nash_equilibria(matrix)
    pareto = analyse_pareto(matrix)

    pareto_by_outcome = {status.outcome: status for status in pareto}
    equilibrium_is_pareto_inferior = any(
        not pareto_by_outcome[eq.outcome].is_pareto_optimal for eq in equilibria
    )

    return GameAnalysis(
        matrix=matrix,
        conditions=conditions,
        dominant_strategy_a=dominant_a,
        dominant_strategy_b=dominant_b,
        nash_equilibria=equilibria,
        pareto=pareto,
        mutual_cooperation_pareto_superior=mutual_cooperation_dominates_mutual_defection(
            matrix
        ),
        equilibrium_is_pareto_inferior=equilibrium_is_pareto_inferior,
        summary=_build_summary(
            conditions, dominant_a, dominant_b, equilibria, equilibrium_is_pareto_inferior
        ),
    )


def dominant_action_or_none(matrix: PayoffMatrix, player: Player) -> Action | None:
    """Convenience wrapper used by services that only need the action."""
    return find_dominant_strategy(matrix, player).action


__all__ = [
    "DilemmaConditions",
    "GameAnalysis",
    "Outcome",
    "PayoffOrdering",
    "analyse_game",
    "check_dilemma_conditions",
    "dominant_action_or_none",
]
