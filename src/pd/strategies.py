"""The six tournament strategies from the project guide.

Every strategy is a plain function with the same signature:

    strategy(my_history, opp_history, rng) -> "C" or "D"

`my_history` and `opp_history` are lists of past actions in the current match,
oldest first, so `opp_history[-1]` is the opponent's previous move. Both lists
are empty on round 1. `rng` is a `random.Random` instance, passed in so that a
whole tournament can be reproduced from a single seed.

Keeping the strategies stateless (they read history instead of remembering
things) means a strategy can never leak state from one match into the next.
"""

from .payoffs import COOPERATE, DEFECT


def strategy_always_cooperate(my_history, opp_history, rng=None):
    """AC - cooperate on every round, whatever happens."""
    return COOPERATE


def strategy_always_defect(my_history, opp_history, rng=None):
    """AD - defect on every round. This is the Nash equilibrium strategy."""
    return DEFECT


def strategy_tit_for_tat(my_history, opp_history, rng=None):
    """TFT - cooperate first, then copy the opponent's last move.

    Nice (never defects first), retaliatory (punishes immediately), forgiving
    (returns to cooperation as soon as the opponent does) and clear.
    """
    if not opp_history:
        return COOPERATE
    return opp_history[-1]


def strategy_grim_trigger(my_history, opp_history, rng=None):
    """GT - cooperate until the opponent defects once, then defect forever."""
    if DEFECT in opp_history:
        return DEFECT
    return COOPERATE


def strategy_tit_for_two_tats(my_history, opp_history, rng=None):
    """TF2T - like TFT but only retaliates after two defections in a row.

    More forgiving than TFT, so it is not provoked by a single defection.
    """
    if len(opp_history) >= 2 and opp_history[-1] == DEFECT and opp_history[-2] == DEFECT:
        return DEFECT
    return COOPERATE


def strategy_random(my_history, opp_history, rng=None):
    """RAND - cooperate or defect with probability 1/2, ignoring history."""
    if rng is None:
        import random as _random

        rng = _random
    return COOPERATE if rng.random() < 0.5 else DEFECT


# Registry: short code -> (full name, function). Order fixes the report's
# default column order.
STRATEGIES = {
    "AC": ("Always Cooperate", strategy_always_cooperate),
    "AD": ("Always Defect", strategy_always_defect),
    "TFT": ("Tit-for-Tat", strategy_tit_for_tat),
    "GT": ("Grim Trigger", strategy_grim_trigger),
    "TF2T": ("Tit-for-Two-Tats", strategy_tit_for_two_tats),
    "RAND": ("Random", strategy_random),
}


def get_strategy(code):
    """Look up a strategy function by its short code (case-insensitive)."""
    key = code.upper()
    if key not in STRATEGIES:
        raise KeyError(
            "unknown strategy {!r}; available: {}".format(code, ", ".join(STRATEGIES))
        )
    return STRATEGIES[key][1]


def strategy_name(code):
    return STRATEGIES[code.upper()][0]


def all_codes():
    return list(STRATEGIES)
