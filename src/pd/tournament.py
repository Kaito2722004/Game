"""Axelrod-style round-robin tournament engine."""

import itertools
import random

from .engine import cooperation_rate, play_match
from .strategies import all_codes


def run_tournament(codes=None, rounds=100, repeats=1, seed=42, include_self=False):
    """Play every strategy against every other strategy.

    Parameters
    ----------
    codes : list of strategy codes, defaults to all six from the guide.
    rounds : rounds per match (the guide suggests 100).
    repeats : how many times to replay the whole round robin. Only RAND is
        stochastic, so one repeat is enough to reproduce the guide's design;
        more repeats average out the luck in RAND's matches.
    seed : seed for the shared RNG, so a run is reproducible.
    include_self : if True, each strategy also plays a copy of itself. The
        guide says "every strategy plays every other strategy", so this is
        off by default.

    Returns a dict with three keys:
        "matches"    - one row per match played (per repeat)
        "round_log"  - one row per round of every match
        "meta"       - the settings used, for the report's methodology section
    """
    codes = list(codes) if codes else all_codes()
    rng = random.Random(seed)

    pairs = list(itertools.combinations(codes, 2))
    if include_self:
        pairs += [(c, c) for c in codes]

    matches = []
    round_log = []

    for repeat in range(1, repeats + 1):
        for code_a, code_b in pairs:
            result = play_match(code_a, code_b, rounds=rounds, rng=rng)

            for row in result.round_log:
                row = dict(row)
                row["repeat"] = repeat
                round_log.append(row)

            # Store the match twice, once from each player's point of view, so
            # that grouping by "strategy" gives that strategy's whole record.
            matches.append(
                {
                    "repeat": repeat,
                    "strategy": code_a,
                    "opponent": code_b,
                    "rounds": rounds,
                    "score": result.score_a,
                    "opponent_score": result.score_b,
                    "cooperation_rate": cooperation_rate(result.history_a),
                }
            )
            matches.append(
                {
                    "repeat": repeat,
                    "strategy": code_b,
                    "opponent": code_a,
                    "rounds": rounds,
                    "score": result.score_b,
                    "opponent_score": result.score_a,
                    "cooperation_rate": cooperation_rate(result.history_b),
                }
            )

    return {
        "matches": matches,
        "round_log": round_log,
        "meta": {
            "strategies": codes,
            "rounds_per_match": rounds,
            "repeats": repeats,
            "seed": seed,
            "include_self": include_self,
            "matches_played": len(pairs) * repeats,
        },
    }
