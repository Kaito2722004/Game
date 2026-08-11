"""Playable version: a human plays the iterated game against a strategy.

Used for the live classroom demo on the last slide, and as a quick way to feel
why defection is tempting round by round.
"""

import random

from .engine import cooperation_rate
from .payoffs import COOPERATE, DEFECT, matrix_markdown, payoff
from .strategies import STRATEGIES, get_strategy, strategy_name


def _ask(prompt):
    """Read one C/D choice from the keyboard. Returns None if the user quits."""
    while True:
        raw = input(prompt).strip().upper()
        if raw in ("Q", "QUIT", "EXIT"):
            return None
        if raw in (COOPERATE, DEFECT):
            return raw
        if raw in ("COOPERATE", "DEFECT"):
            return raw[0]
        print("  Please type C (cooperate), D (defect), or Q to quit.")


def play_interactive(opponent="TFT", rounds=10, seed=None, reveal_opponent=False):
    """Play `rounds` rounds against `opponent`; returns the final scores."""
    code = opponent.upper()
    fn = get_strategy(code)
    rng = random.Random(seed)

    print()
    print("=" * 62)
    print("  PRISONER'S DILEMMA - {} rounds".format(rounds))
    print("=" * 62)
    print(matrix_markdown())
    print()
    if reveal_opponent:
        print("  Opponent: {} ({})".format(strategy_name(code), code))
    else:
        print("  Opponent: hidden. Try to work out how it is playing.")
    print("  Each round type C to cooperate or D to defect. Q quits early.")
    print()

    my_history, opp_history = [], []
    my_score = opp_score = 0

    for n in range(1, rounds + 1):
        choice = _ask("Round {}/{}  your move [C/D]: ".format(n, rounds))
        if choice is None:
            print("\n  Stopped early after {} completed rounds.".format(n - 1))
            break

        # The opponent decides from history only: it never sees this round's move.
        opp_choice = fn(list(opp_history), list(my_history), rng)
        pay_me, pay_opp = payoff(choice, opp_choice)
        my_score += pay_me
        opp_score += pay_opp
        my_history.append(choice)
        opp_history.append(opp_choice)

        print(
            "    you {}  opponent {}   ->  +{} / +{}   running total {} - {}".format(
                choice, opp_choice, pay_me, pay_opp, my_score, opp_score
            )
        )

    played = len(my_history)
    print()
    print("-" * 62)
    print("  Final after {} rounds:  you {}  |  opponent {}".format(
        played, my_score, opp_score))
    if played:
        print("  Your cooperation rate: {:.0%}".format(cooperation_rate(my_history)))
        print("  Their cooperation rate: {:.0%}".format(cooperation_rate(opp_history)))
        print("  You averaged {:.2f} points per round (mutual cooperation pays 3.00,"
              " mutual defection pays 1.00).".format(my_score / played))
    print("  The opponent was {} ({}).".format(strategy_name(code), code))
    print("-" * 62)
    print()
    return {
        "opponent": code,
        "rounds_played": played,
        "your_score": my_score,
        "opponent_score": opp_score,
        "your_history": "".join(my_history),
        "opponent_history": "".join(opp_history),
    }


def list_opponents():
    return "\n".join(
        "  {:<5} {}".format(code, name) for code, (name, _) in STRATEGIES.items()
    )
