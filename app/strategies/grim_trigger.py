"""Grim Trigger."""

from __future__ import annotations

from app.game_theory.actions import Action, StrategyCategory
from app.strategies.base import History, Strategy, StrategyMetadata


class GrimTrigger(Strategy):
    """Cooperates until the opponent defects once, then defects forever.

    Nice, retaliatory and clear, but never forgiving: a single defection ends
    cooperation permanently for the rest of the match.
    """

    metadata = StrategyMetadata(
        id="GRIM_TRIGGER",
        name="Grim Trigger",
        description=(
            "Cooperates until the opponent's first defection, then defects for "
            "the remainder of the match. Punishment is permanent."
        ),
        rules=[
            "Play COOPERATE while the opponent has never defected.",
            "Once the opponent has defected at least once, play DEFECT in every "
            "remaining round.",
        ],
        category=StrategyCategory.NICE,
        is_deterministic=True,
    )

    def choose_action(self, my_history: History, opponent_history: History) -> Action:
        if Action.DEFECT in opponent_history:
            return Action.DEFECT
        return Action.COOPERATE
