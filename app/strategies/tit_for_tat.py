"""Tit-for-Tat."""

from __future__ import annotations

from app.game_theory.actions import Action, StrategyCategory
from app.strategies.base import History, Strategy, StrategyMetadata


class TitForTat(Strategy):
    """Cooperates first, then repeats the opponent's previous action.

    The strategy associated with Axelrod's tournaments. It is nice (never
    defects first), retaliatory (punishes a defection immediately), forgiving
    (returns to cooperation as soon as the opponent does) and clear (its rule
    is easy for an opponent to infer).
    """

    metadata = StrategyMetadata(
        id="TIT_FOR_TAT",
        name="Tit-for-Tat",
        description=(
            "Opens with cooperation and then copies whatever the opponent did "
            "in the previous round."
        ),
        rules=[
            "Play COOPERATE in the first round.",
            "In every later round, repeat the opponent's action from the previous round.",
        ],
        category=StrategyCategory.NICE,
        is_deterministic=True,
    )

    def choose_action(self, my_history: History, opponent_history: History) -> Action:
        if not opponent_history:
            return Action.COOPERATE
        return opponent_history[-1]
