"""Dominant strategies and pure-strategy Nash equilibria.

Everything here is computed from the payoff numbers. Nothing about the classic
Prisoner's Dilemma is assumed: the same functions give the right answer for a
Stag Hunt, a Chicken game, or a matrix with no equilibrium at all.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.game_theory.actions import Action, DominanceType, Outcome, Player
from app.game_theory.payoff import PayoffMatrix

_BOTH_ACTIONS = (Action.COOPERATE, Action.DEFECT)


@dataclass(frozen=True)
class DominantStrategy:
    """A player's dominant action, if one exists."""

    player: Player
    action: Action | None
    dominance: DominanceType | None
    explanation: str

    @property
    def exists(self) -> bool:
        return self.action is not None


@dataclass(frozen=True)
class NashEquilibrium:
    """A pure-strategy equilibrium cell and its payoffs."""

    outcome: Outcome
    player_a_action: Action
    player_b_action: Action
    player_a_payoff: float
    player_b_payoff: float
    explanation: str


def _payoffs_for(
    matrix: PayoffMatrix, player: Player, own: Action, other: Action
) -> float:
    return matrix.payoff_for(player is Player.A, own, other)


def find_dominant_strategy(matrix: PayoffMatrix, player: Player) -> DominantStrategy:
    """Find `player`'s dominant action, if any.

    An action strictly dominates when it pays strictly more against *every*
    action the opponent might choose. It weakly dominates when it pays at
    least as much against every action and strictly more against at least one.
    """
    candidates: list[tuple[Action, DominanceType]] = []

    for own in _BOTH_ACTIONS:
        alternative = Action.DEFECT if own is Action.COOPERATE else Action.COOPERATE
        comparisons = [
            (
                _payoffs_for(matrix, player, own, other),
                _payoffs_for(matrix, player, alternative, other),
            )
            for other in _BOTH_ACTIONS
        ]
        if all(mine > theirs for mine, theirs in comparisons):
            candidates.append((own, DominanceType.STRICT))
        elif all(mine >= theirs for mine, theirs in comparisons) and any(
            mine > theirs for mine, theirs in comparisons
        ):
            candidates.append((own, DominanceType.WEAK))

    if not candidates:
        return DominantStrategy(
            player=player,
            action=None,
            dominance=None,
            explanation=(
                f"Player {player.value} has no dominant action: neither action pays "
                "at least as much as the other against every opponent action."
            ),
        )

    # A strict dominance claim beats a weak one; both cannot be strict at once.
    candidates.sort(key=lambda item: 0 if item[1] is DominanceType.STRICT else 1)
    action, dominance = candidates[0]

    lines = []
    for other in _BOTH_ACTIONS:
        own_payoff = _payoffs_for(matrix, player, action, other)
        alternative = Action.DEFECT if action is Action.COOPERATE else Action.COOPERATE
        alt_payoff = _payoffs_for(matrix, player, alternative, other)
        lines.append(
            f"if the opponent plays {other.value}, {action.value} pays {own_payoff:g} "
            f"versus {alt_payoff:g}"
        )
    return DominantStrategy(
        player=player,
        action=action,
        dominance=dominance,
        explanation=(
            f"{action.value} {dominance.value.lower()}ly dominates for player "
            f"{player.value}: " + "; ".join(lines) + "."
        ),
    )


def find_nash_equilibria(matrix: PayoffMatrix) -> list[NashEquilibrium]:
    """All pure-strategy Nash equilibria of the matrix.

    A cell is an equilibrium when neither player can raise their own payoff by
    changing their action alone, holding the other player's action fixed.
    Mixed-strategy equilibria are out of scope for this project.
    """
    equilibria: list[NashEquilibrium] = []

    for outcome in Outcome:
        action_a, action_b = outcome.actions
        payoff_a, payoff_b = matrix.payoff(action_a, action_b)

        deviation_a = Action.DEFECT if action_a is Action.COOPERATE else Action.COOPERATE
        deviation_b = Action.DEFECT if action_b is Action.COOPERATE else Action.COOPERATE

        payoff_a_if_deviates = matrix.payoff(deviation_a, action_b)[0]
        payoff_b_if_deviates = matrix.payoff(action_a, deviation_b)[1]

        a_is_content = payoff_a >= payoff_a_if_deviates
        b_is_content = payoff_b >= payoff_b_if_deviates

        if a_is_content and b_is_content:
            equilibria.append(
                NashEquilibrium(
                    outcome=outcome,
                    player_a_action=action_a,
                    player_b_action=action_b,
                    player_a_payoff=payoff_a,
                    player_b_payoff=payoff_b,
                    explanation=(
                        f"({action_a.value}, {action_b.value}) is a Nash equilibrium: "
                        f"A switching alone would move from {payoff_a:g} to "
                        f"{payoff_a_if_deviates:g}, and B switching alone would move "
                        f"from {payoff_b:g} to {payoff_b_if_deviates:g}."
                    ),
                )
            )

    return equilibria
