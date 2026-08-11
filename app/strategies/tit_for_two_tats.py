"""Tit-for-Two-Tats."""

from __future__ import annotations

from app.game_theory.actions import Action, StrategyCategory
from app.strategies.base import History, Strategy, StrategyMetadata


class TitForTwoTats(Strategy):
    """Retaliates only after two consecutive defections by the opponent.

    More forgiving than Tit-for-Tat: an isolated defection is absorbed rather
    than answered, so two copies of this strategy cannot fall into a cycle of
    mutual recrimination after a single defection.
    """

    metadata = StrategyMetadata(
        id="TIT_FOR_TWO_TATS",
        name="Tit-for-Two-Tats",
        description=(
            "Cooperates unless the opponent defected in both of the two "
            "previous rounds."
        ),
        rules=[
            "Play COOPERATE in the first two rounds.",
            "Play DEFECT only when the opponent defected in each of the previous "
            "two rounds.",
            "Otherwise play COOPERATE.",
        ],
        category=StrategyCategory.NICE,
        is_deterministic=True,
    )

    def choose_action(self, my_history: History, opponent_history: History) -> Action:
        if len(opponent_history) < 2:
            return Action.COOPERATE
        if opponent_history[-1] is Action.DEFECT and opponent_history[-2] is Action.DEFECT:
            return Action.DEFECT
        return Action.COOPERATE
