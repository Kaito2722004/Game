"""Random strategy."""

from __future__ import annotations

from app.game_theory.actions import Action, StrategyCategory
from app.strategies.base import History, Strategy, StrategyMetadata


class RandomStrategy(Strategy):
    """Cooperates or defects with equal probability, ignoring history.

    The random source is injected by the simulation engine, so a seeded run is
    exactly reproducible.
    """

    metadata = StrategyMetadata(
        id="RANDOM",
        name="Random",
        description=(
            "Chooses COOPERATE or DEFECT with probability 0.5 each, independently "
            "of the history of the match."
        ),
        rules=["Play COOPERATE with probability 0.5, otherwise DEFECT."],
        category=StrategyCategory.STOCHASTIC,
        is_deterministic=False,
    )

    def choose_action(self, my_history: History, opponent_history: History) -> Action:
        return Action.COOPERATE if self.rng.random() < 0.5 else Action.DEFECT
