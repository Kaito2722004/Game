"""Game engine: play one iterated Prisoner's Dilemma match."""

import random
from collections import namedtuple

from .payoffs import COOPERATE, DEFECT, payoff
from .strategies import get_strategy, strategy_name

MatchResult = namedtuple(
    "MatchResult",
    [
        "code_a",
        "code_b",
        "rounds",
        "history_a",
        "history_b",
        "score_a",
        "score_b",
        "round_log",
    ],
)


def play_match(code_a, code_b, rounds=100, rng=None):
    """Play `rounds` rounds between two strategies and return a MatchResult.

    Both players choose simultaneously each round: neither strategy is shown
    the current round's move of the other, only the completed history.
    """
    if rounds < 1:
        raise ValueError("rounds must be at least 1, got {}".format(rounds))

    rng = rng or random.Random()
    fn_a = get_strategy(code_a)
    fn_b = get_strategy(code_b)

    history_a, history_b = [], []
    score_a = score_b = 0
    round_log = []

    for n in range(1, rounds + 1):
        # Snapshot copies so a strategy cannot mutate the shared history.
        action_a = fn_a(list(history_a), list(history_b), rng)
        action_b = fn_b(list(history_b), list(history_a), rng)

        pay_a, pay_b = payoff(action_a, action_b)
        score_a += pay_a
        score_b += pay_b

        history_a.append(action_a)
        history_b.append(action_b)
        round_log.append(
            {
                "round": n,
                "strategy_a": code_a,
                "strategy_b": code_b,
                "action_a": action_a,
                "action_b": action_b,
                "payoff_a": pay_a,
                "payoff_b": pay_b,
                "cum_a": score_a,
                "cum_b": score_b,
            }
        )

    return MatchResult(
        code_a=code_a,
        code_b=code_b,
        rounds=rounds,
        history_a=history_a,
        history_b=history_b,
        score_a=score_a,
        score_b=score_b,
        round_log=round_log,
    )


def cooperation_rate(history):
    """Fraction of rounds in which this player cooperated."""
    if not history:
        return 0.0
    return history.count(COOPERATE) / len(history)


def defection_rate(history):
    if not history:
        return 0.0
    return history.count(DEFECT) / len(history)


def describe_match(result):
    """One-line human-readable summary of a match."""
    return "{:<18} {:>5}  vs  {:<18} {:>5}   ({} rounds)".format(
        strategy_name(result.code_a),
        result.score_a,
        strategy_name(result.code_b),
        result.score_b,
        result.rounds,
    )
