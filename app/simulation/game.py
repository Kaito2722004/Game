"""Round-level mechanics shared by the match and tournament engines."""

from __future__ import annotations

import random
from dataclasses import dataclass

from app.game_theory.actions import Action, Outcome
from app.game_theory.payoff import PayoffMatrix
from app.strategies.base import Strategy


@dataclass(frozen=True)
class RoundResult:
    """One completed round of simultaneous play."""

    round_number: int
    player_a_action: Action
    player_b_action: Action
    player_a_payoff: float
    player_b_payoff: float

    @property
    def outcome(self) -> Outcome:
        return Outcome.from_actions(self.player_a_action, self.player_b_action)


def play_round(
    round_number: int,
    strategy_a: Strategy,
    strategy_b: Strategy,
    history_a: list[Action],
    history_b: list[Action],
    matrix: PayoffMatrix,
) -> RoundResult:
    """Resolve one round.

    Both strategies choose before either result is known, and each is handed a
    copy of the history so it cannot mutate the shared record or read the
    other's choice for this round.
    """
    action_a = strategy_a.choose_action(tuple(history_a), tuple(history_b))
    action_b = strategy_b.choose_action(tuple(history_b), tuple(history_a))

    if not isinstance(action_a, Action) or not isinstance(action_b, Action):
        raise TypeError("strategies must return an Action")

    payoff_a, payoff_b = matrix.payoff(action_a, action_b)
    return RoundResult(
        round_number=round_number,
        player_a_action=action_a,
        player_b_action=action_b,
        player_a_payoff=payoff_a,
        player_b_payoff=payoff_b,
    )


def should_continue(
    completed_rounds: int,
    max_rounds: int,
    continuation_probability: float | None,
    rng: random.Random,
) -> bool:
    """Decide whether another round is played.

    With no continuation probability the match is a fixed-length repeated
    game of `max_rounds` rounds. With one, each completed round is followed by
    another with that probability, which models a repeated game whose end is
    uncertain; `max_rounds` then acts as an upper bound so a simulation with a
    probability of 1.0 still terminates.

    This function only implements the model. It makes no claim about which
    behaviour is optimal under it.
    """
    if completed_rounds >= max_rounds:
        return False
    if continuation_probability is None:
        return True
    if continuation_probability >= 1.0:
        return True
    if continuation_probability <= 0.0:
        return False
    return rng.random() < continuation_probability
