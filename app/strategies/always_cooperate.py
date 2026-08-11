"""Always Cooperate."""

from __future__ import annotations

from app.game_theory.actions import Action, StrategyCategory
from app.strategies.base import History, Strategy, StrategyMetadata


class AlwaysCooperate(Strategy):
    """Cooperates in every round regardless of what the opponent does."""

    metadata = StrategyMetadata(
        id="ALWAYS_COOPERATE",
        name="Always Cooperate",
        description=(
            "Cooperates unconditionally. It is exploited by any strategy that "
            "defects, but it never provokes retaliation."
        ),
        rules=["Play COOPERATE in every round."],
        category=StrategyCategory.NICE,
        is_deterministic=True,
    )

    def choose_action(self, my_history: History, opponent_history: History) -> Action:
        return Action.COOPERATE
