"""Always Defect."""

from __future__ import annotations

from app.game_theory.actions import Action, StrategyCategory
from app.strategies.base import History, Strategy, StrategyMetadata


class AlwaysDefect(Strategy):
    """Defects in every round.

    In the classic matrix defection is the dominant action, so this strategy
    plays the one-shot Nash equilibrium move every round. Whether that is
    successful over a repeated tournament is a separate question, and one the
    tournament answers empirically.
    """

    metadata = StrategyMetadata(
        id="ALWAYS_DEFECT",
        name="Always Defect",
        description=(
            "Defects unconditionally. It plays the dominant action of the "
            "one-shot game in every round of the repeated game."
        ),
        rules=["Play DEFECT in every round."],
        category=StrategyCategory.NASTY,
        is_deterministic=True,
    )

    def choose_action(self, my_history: History, opponent_history: History) -> Action:
        return Action.DEFECT
