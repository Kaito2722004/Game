"""Command line entry point.

    python main.py theory
    python main.py play --opponent TFT --rounds 10
    python main.py tournament --rounds 100 --outdir results
    python main.py experiment --data data/human_experiment.csv
    python main.py all
"""

import argparse
import json
import os
import sys

from . import experiment as human
from . import viz
from .payoffs import (
    P,
    R,
    S,
    T,
    check_dilemma_conditions,
    matrix_markdown,
)
from .play import list_opponents, play_interactive
from .stats import (
    calculate_statistics,
    cooperation_over_time,
    frame_markdown,
    head_to_head,
    matches_frame,
    round_log_frame,
    summary_markdown,
)
from .strategies import STRATEGIES, all_codes
from .tournament import run_tournament

DEFAULT_OUTDIR = "results"
DEFAULT_DATA = os.path.join("data", "human_experiment.csv")


# ----------------------------------------------------------------- theory ---
def cmd_theory(args):
    print()
    print("PRISONER'S DILEMMA - THEORY SUMMARY")
    print("=" * 62)
    print()
    print("Payoff matrix (A's payoff, B's payoff):")
    print(matrix_markdown())
    print()
    print("Notation: T={}, R={}, P/U={}, S={}".format(T, R, P, S))
    for condition, holds in check_dilemma_conditions().items():
        print("  {:<18} {}".format(condition, "holds" if holds else "FAILS"))
    print()
    print("Dominant strategy")
    print("  If B cooperates, A gets {} by cooperating and {} by defecting.".format(R, T))
    print("  If B defects,    A gets {} by cooperating and {} by defecting.".format(S, P))
    print("  Defection pays more in both cases, so D strictly dominates C for A,")
    print("  and by symmetry for B as well.")
    print()
    print("Nash equilibrium")
    print("  (D,D) with payoffs ({},{}). Neither player can gain by switching alone:".format(P, P))
    print("  a unilateral move to C drops that player from {} to {}.".format(P, S))
    print()
    print("Pareto comparison")
    print("  (C,C) pays ({},{}), which is better for BOTH players than ({},{}).".format(R, R, P, P))
    print("  So the equilibrium (D,D) is Pareto-inferior: individual rationality")
    print("  and collective benefit point in opposite directions. That is the dilemma.")
    print()
    print("Repeated play")
    print("  With repetition today's choice changes tomorrow's treatment, so")
    print("  cooperation can be sustained by the threat of future retaliation.")
    print("  Under a known finite horizon backward induction unravels this from")
    print("  the last round; uncertain continuation leaves room for cooperation.")
    print()
    return 0


# ------------------------------------------------------------------- play ---
def cmd_play(args):
    if args.opponent.upper() not in STRATEGIES:
        print("Unknown opponent {!r}. Available:".format(args.opponent))
        print(list_opponents())
        return 2
    try:
        play_interactive(
            opponent=args.opponent,
            rounds=args.rounds,
            seed=args.seed,
            reveal_opponent=args.reveal,
        )
    except (EOFError, KeyboardInterrupt):
        print("\nStopped.")
        return 1
    return 0


# ------------------------------------------------------------- tournament ---
def cmd_tournament(args):
    codes = [c.upper() for c in args.strategies] if args.strategies else all_codes()
    unknown = [c for c in codes if c not in STRATEGIES]
    if unknown:
        print("Unknown strategy code(s): {}".format(", ".join(unknown)))
        print(list_opponents())
        return 2

    os.makedirs(args.outdir, exist_ok=True)
    results = run_tournament(
        codes=codes,
        rounds=args.rounds,
        repeats=args.repeats,
        seed=args.seed,
        include_self=args.include_self,
    )

    summary = calculate_statistics(results)
    h2h = head_to_head(results)
    over_time = cooperation_over_time(results)

    summary.to_csv(os.path.join(args.outdir, "tournament_summary.csv"), index=False)
    h2h.to_csv(os.path.join(args.outdir, "head_to_head.csv"))
    over_time.to_csv(os.path.join(args.outdir, "cooperation_over_time.csv"), index=False)
    matches_frame(results).to_csv(
        os.path.join(args.outdir, "matches.csv"), index=False
    )
    if args.save_rounds:
        round_log_frame(results).to_csv(
            os.path.join(args.outdir, "round_log.csv"), index=False
        )
    with open(os.path.join(args.outdir, "tournament_meta.json"), "w") as fh:
        json.dump(results["meta"], fh, indent=2)

    charts = [] if args.no_plots else viz.plot_results(results, args.outdir)

    print()
    print("TOURNAMENT RESULTS")
    print("=" * 62)
    print("{} strategies, {} matches, {} rounds each, seed {}".format(
        len(codes), results["meta"]["matches_played"], args.rounds, args.seed))
    print()
    print(summary.to_string(index=False))
    print()
    print("Average payoff per round, row strategy vs column opponent:")
    print(h2h.to_string())
    print()
    winner = summary.iloc[0]
    print("Winner: {} ({}) with {:.0f} points, cooperating {:.0%} of the time.".format(
        winner["Strategy"], winner["Code"], winner["Total Score"], winner["Cooperation Rate"]))
    print()
    print("Written to {}/:".format(args.outdir))
    for name in sorted(os.listdir(args.outdir)):
        print("  " + name)
    if charts:
        print()
    _write_results_markdown(args.outdir, results, summary, h2h)
    return 0


def _write_results_markdown(outdir, results, summary, h2h):
    """Chapter 5 skeleton with the real numbers already substituted in."""
    meta = results["meta"]
    winner = summary.iloc[0]
    lines = [
        "# Tournament Results",
        "",
        "Generated by `python main.py tournament`. Numbers below come from an",
        "actual simulation run, not from an estimate.",
        "",
        "## Settings",
        "",
        "| Setting | Value |",
        "|---|---|",
        "| Strategies | {} |".format(", ".join(meta["strategies"])),
        "| Rounds per match | {} |".format(meta["rounds_per_match"]),
        "| Matches played | {} |".format(meta["matches_played"]),
        "| Repeats | {} |".format(meta["repeats"]),
        "| Random seed | {} |".format(meta["seed"]),
        "| Self-play included | {} |".format("yes" if meta["include_self"] else "no"),
        "",
        "## Ranking",
        "",
        summary_markdown(summary),
        "",
        "Winner: **{} ({})** with {:.0f} points and a cooperation rate of {:.1%}.".format(
            winner["Strategy"], winner["Code"], winner["Total Score"],
            winner["Cooperation Rate"]),
        "",
        "## Head-to-head (average payoff per round)",
        "",
        frame_markdown(h2h, index_label="vs →"),
        "",
        "## Figures",
        "",
        "- `tournament_scores.png` - total score by strategy",
        "- `cooperation_rates.png` - cooperation rate by strategy",
        "- `head_to_head.png` - payoff matrix between strategies",
        "- `cooperation_over_time.png` - cooperation across the length of a match",
        "",
    ]
    path = os.path.join(outdir, "RESULTS.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return path


# ------------------------------------------------------------- experiment ---
def cmd_experiment(args):
    if not os.path.exists(args.data):
        print("No data file at {}.".format(args.data))
        print("Copy data/human_experiment_template.csv, fill in the class results,")
        print("and pass it with --data.")
        return 2

    try:
        df = human.load_experiment(args.data)
    except ValueError as exc:
        print("Could not use {}: {}".format(args.data, exc))
        return 2

    os.makedirs(args.outdir, exist_ok=True)
    summary = human.experiment_summary(df)
    by_round = human.cooperation_by_round(df)
    by_pair = human.cooperation_by_pair(df)
    comparison = human.compare_with_theory(summary)
    trust = human.trust_analysis(df)

    df.to_csv(os.path.join(args.outdir, "human_clean.csv"), index=False)
    by_round.to_csv(os.path.join(args.outdir, "human_by_round.csv"), index=False)
    by_pair.to_csv(os.path.join(args.outdir, "human_by_pair.csv"), index=False)
    with open(os.path.join(args.outdir, "human_summary.json"), "w") as fh:
        json.dump({"summary": summary, "vs_theory": comparison}, fh, indent=2)
    if not args.no_plots:
        viz.plot_human_results(by_round, os.path.join(args.outdir, "human_by_round.png"))

    print()
    print("HUMAN EXPERIMENT - {}".format(args.data))
    print("=" * 62)
    for key, value in summary.items():
        print("  {:<28} {}".format(key.replace("_", " "), value))
    print()
    print("Cooperation by round:")
    print(by_round.to_string(index=False))
    print()
    print("Nash prediction vs observed:")
    print("  predicted: {}".format(comparison["nash_prediction"]))
    print("  observed cooperation rate: {}".format(comparison["observed_cooperation_rate"]))
    print("  observed mutual defection: {}".format(comparison["observed_mutual_defection_rate"]))
    print()
    if trust:
        print("Trust survey (descriptive only, not causal):")
        if trust["correlations"]:
            for key, value in trust["correlations"].items():
                print("  correlation({}, cooperation rate) = {}".format(key, value))
        else:
            print("  not enough variation in the survey answers to correlate.")
        print()
    print("Written to {}/".format(args.outdir))
    return 0


# -------------------------------------------------------------------- all ---
def cmd_all(args):
    rc = cmd_theory(args)
    tournament_args = argparse.Namespace(
        strategies=None,
        rounds=args.rounds,
        repeats=args.repeats,
        seed=args.seed,
        include_self=False,
        outdir=args.outdir,
        no_plots=args.no_plots,
        save_rounds=True,
    )
    rc |= cmd_tournament(tournament_args)
    if os.path.exists(args.data):
        experiment_args = argparse.Namespace(
            data=args.data, outdir=args.outdir, no_plots=args.no_plots
        )
        rc |= cmd_experiment(experiment_args)
    else:
        print("Skipping the human experiment: no data file at {}.".format(args.data))
        print("That phase needs real classroom data before it can be reported.")
    return rc


# ------------------------------------------------------------------ parse ---
def build_parser():
    parser = argparse.ArgumentParser(
        prog="prisoners-dilemma",
        description="Prisoner's Dilemma: theory, classroom experiment, and "
                    "Axelrod-style strategy tournament.",
    )
    sub = parser.add_subparsers(dest="command")

    p_theory = sub.add_parser("theory", help="print the theory summary")
    p_theory.set_defaults(func=cmd_theory)

    p_play = sub.add_parser("play", help="play against a strategy yourself")
    p_play.add_argument("--opponent", "-o", default="TFT",
                        help="strategy code: " + ", ".join(STRATEGIES))
    p_play.add_argument("--rounds", "-n", type=int, default=10)
    p_play.add_argument("--seed", type=int, default=None)
    p_play.add_argument("--reveal", action="store_true",
                        help="name the opponent before play instead of after")
    p_play.set_defaults(func=cmd_play)

    p_tour = sub.add_parser("tournament", help="run the round-robin tournament")
    p_tour.add_argument("--strategies", "-s", nargs="+", default=None)
    p_tour.add_argument("--rounds", "-n", type=int, default=100)
    p_tour.add_argument("--repeats", "-r", type=int, default=1)
    p_tour.add_argument("--seed", type=int, default=42)
    p_tour.add_argument("--include-self", action="store_true",
                        help="also let each strategy play a copy of itself")
    p_tour.add_argument("--outdir", default=DEFAULT_OUTDIR)
    p_tour.add_argument("--no-plots", action="store_true")
    p_tour.add_argument("--save-rounds", action="store_true",
                        help="also write the full round-by-round log")
    p_tour.set_defaults(func=cmd_tournament)

    p_exp = sub.add_parser("experiment", help="analyse the human experiment CSV")
    p_exp.add_argument("--data", default=DEFAULT_DATA)
    p_exp.add_argument("--outdir", default=DEFAULT_OUTDIR)
    p_exp.add_argument("--no-plots", action="store_true")
    p_exp.set_defaults(func=cmd_experiment)

    p_all = sub.add_parser("all", help="theory + tournament + experiment if present")
    p_all.add_argument("--rounds", "-n", type=int, default=100)
    p_all.add_argument("--repeats", "-r", type=int, default=1)
    p_all.add_argument("--seed", type=int, default=42)
    p_all.add_argument("--data", default=DEFAULT_DATA)
    p_all.add_argument("--outdir", default=DEFAULT_OUTDIR)
    p_all.add_argument("--no-plots", action="store_true")
    p_all.set_defaults(func=cmd_all)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        print("\nStrategies:")
        print(list_opponents())
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
