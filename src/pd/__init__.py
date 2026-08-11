"""Prisoner's Dilemma strategy tournament.

Package layout mirrors the architecture in the project guide:

    payoffs.py    payoff matrix and the T > R > P > S conditions
    strategies.py the six tournament strategies
    engine.py     plays one match
    tournament.py round-robin over all strategies
    stats.py      score tables, head-to-head matrix, cooperation over time
    viz.py        charts
    experiment.py the human classroom experiment
    play.py       interactive human-vs-strategy game
    cli.py        command line entry point
"""

__version__ = "1.0.0"

from .engine import play_match  # noqa: F401
from .payoffs import payoff  # noqa: F401
from .stats import calculate_statistics  # noqa: F401
from .tournament import run_tournament  # noqa: F401
