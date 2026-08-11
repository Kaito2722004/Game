"""Pareto analysis over the four pure outcomes of a 2x2 game."""

from __future__ import annotations

from dataclasses import dataclass

from app.game_theory.actions import Outcome
from app.game_theory.payoff import PayoffMatrix


@dataclass(frozen=True)
class ParetoStatus:
    """Whether one outcome is Pareto-optimal, and what dominates it if not."""

    outcome: Outcome
    player_a_payoff: float
    player_b_payoff: float
    is_pareto_optimal: bool
    dominated_by: list[Outcome]
    explanation: str


def _dominates(better: tuple[float, float], worse: tuple[float, float]) -> bool:
    """True when `better` is at least as good for both players and better for one."""
    return (
        better[0] >= worse[0]
        and better[1] >= worse[1]
        and (better[0] > worse[0] or better[1] > worse[1])
    )


def analyse_pareto(matrix: PayoffMatrix) -> list[ParetoStatus]:
    """Classify every outcome as Pareto-optimal or Pareto-inferior.

    An outcome is Pareto-inferior when another outcome exists that makes at
    least one player better off and neither player worse off. Outcomes that
    are not dominated by any other outcome are Pareto-optimal.
    """
    payoffs = {outcome: pair.as_tuple() for outcome, pair in matrix.outcomes.items()}
    statuses: list[ParetoStatus] = []

    for outcome, values in payoffs.items():
        dominated_by = [
            other
            for other, other_values in payoffs.items()
            if other is not outcome and _dominates(other_values, values)
        ]
        optimal = not dominated_by

        if optimal:
            explanation = (
                f"{outcome.value} is Pareto-optimal: no other outcome improves one "
                "player without making the other worse off."
            )
        else:
            names = ", ".join(
                f"{other.value} ({payoffs[other][0]:g},{payoffs[other][1]:g})"
                for other in dominated_by
            )
            explanation = (
                f"{outcome.value} ({values[0]:g},{values[1]:g}) is Pareto-inferior to "
                f"{names}."
            )

        statuses.append(
            ParetoStatus(
                outcome=outcome,
                player_a_payoff=values[0],
                player_b_payoff=values[1],
                is_pareto_optimal=optimal,
                dominated_by=dominated_by,
                explanation=explanation,
            )
        )

    return statuses


def mutual_cooperation_dominates_mutual_defection(matrix: PayoffMatrix) -> bool:
    """True when (C,C) Pareto-dominates (D,D).

    In the classic Prisoner's Dilemma this holds, which is what makes the
    equilibrium outcome Pareto-inferior and produces the conflict between
    individual and collective rationality.
    """
    return _dominates(matrix.cc.as_tuple(), matrix.dd.as_tuple())
