"""Phase 2: the human classroom experiment.

Reads the CSV that the class fills in, checks it, recomputes the payoffs (so a
mis-typed payoff in the sheet cannot reach the report), and produces the
cooperation figures Chapter 5 needs.

Expected columns in the data file:
    pair        - pair identifier, e.g. P01
    round       - round number, 1..10
    choice_a    - "C" or "D"
    choice_b    - "C" or "D"
Optional survey columns (one value per pair, repeated on each row or filled in
on round 1 only):
    trust_before_a, trust_before_b   - 1..5, expected cooperation before play
    trust_after_a,  trust_after_b    - 1..5, trust felt after play
"""

import pandas as pd

from .payoffs import ACTIONS, payoff

REQUIRED_COLUMNS = ["pair", "round", "choice_a", "choice_b"]
TRUST_COLUMNS = [
    "trust_before_a",
    "trust_before_b",
    "trust_after_a",
    "trust_after_b",
]


def load_experiment(path):
    """Load and validate a human-experiment CSV. Raises ValueError if unusable."""
    df = pd.read_csv(path, comment="#")
    df.columns = [c.strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("missing required column(s): {}".format(", ".join(missing)))

    for col in ("choice_a", "choice_b"):
        df[col] = df[col].astype(str).str.strip().str.upper()
        bad = df.loc[~df[col].isin(ACTIONS), col].unique()
        if len(bad):
            raise ValueError(
                "{} contains value(s) that are not C or D: {}".format(col, list(bad))
            )

    df["round"] = df["round"].astype(int)
    if df.empty:
        raise ValueError("no data rows found in {}".format(path))

    duplicates = df.duplicated(subset=["pair", "round"])
    if duplicates.any():
        rows = df.loc[duplicates, ["pair", "round"]].to_dict("records")
        raise ValueError("duplicate pair/round entries: {}".format(rows))

    # Recompute payoffs from the choices rather than trusting the sheet.
    payoffs = df.apply(lambda r: payoff(r["choice_a"], r["choice_b"]), axis=1)
    df["payoff_a"] = [p[0] for p in payoffs]
    df["payoff_b"] = [p[1] for p in payoffs]
    return df


def _long_form(df):
    """One row per player-decision, so both players count equally."""
    a = df[["pair", "round", "choice_a", "payoff_a"]].rename(
        columns={"choice_a": "choice", "payoff_a": "payoff"}
    )
    b = df[["pair", "round", "choice_b", "payoff_b"]].rename(
        columns={"choice_b": "choice", "payoff_b": "payoff"}
    )
    long = pd.concat([a, b], ignore_index=True)
    long["cooperated"] = (long["choice"] == "C").astype(float)
    return long


def experiment_summary(df):
    """Headline numbers for the results chapter."""
    long = _long_form(df)
    outcomes = df.apply(lambda r: r["choice_a"] + r["choice_b"], axis=1)
    mutual_c = (outcomes == "CC").mean()
    mutual_d = (outcomes == "DD").mean()

    return {
        "pairs": int(df["pair"].nunique()),
        "rounds_per_pair": int(df["round"].max()),
        "decisions": int(len(long)),
        "cooperation_rate": round(float(long["cooperated"].mean()), 3),
        "defection_rate": round(float(1 - long["cooperated"].mean()), 3),
        "mutual_cooperation_rate": round(float(mutual_c), 3),
        "mutual_defection_rate": round(float(mutual_d), 3),
        "mean_payoff_per_decision": round(float(long["payoff"].mean()), 3),
        "max_possible_mean_payoff": 3.0,
    }


def cooperation_by_round(df):
    """Cooperation rate in each round - shows any end-game unravelling."""
    long = _long_form(df)
    return (
        long.groupby("round", as_index=False)["cooperated"]
        .mean()
        .rename(columns={"cooperated": "cooperation_rate"})
        .round(3)
    )


def cooperation_by_pair(df):
    long = _long_form(df)
    return (
        long.groupby("pair", as_index=False)
        .agg(cooperation_rate=("cooperated", "mean"), mean_payoff=("payoff", "mean"))
        .round(3)
    )


def trust_analysis(df):
    """Relate the trust survey to actual cooperation, if the columns are present.

    Returns None when no survey data was collected. The correlation is
    descriptive only: a classroom sample of this size cannot support a causal
    claim, and the report should say so.
    """
    present = [c for c in TRUST_COLUMNS if c in df.columns]
    if not present:
        return None

    rows = []
    for pair, group in df.groupby("pair"):
        group = group.sort_values("round")
        for side in ("a", "b"):
            before = group.get("trust_before_" + side)
            after = group.get("trust_after_" + side)
            rows.append(
                {
                    "pair": pair,
                    "player": side.upper(),
                    "trust_before": None if before is None else before.dropna().mean(),
                    "trust_after": None if after is None else after.dropna().mean(),
                    "cooperation_rate": (group["choice_" + side] == "C").mean(),
                }
            )

    table = pd.DataFrame(rows).dropna(subset=["cooperation_rate"])
    result = {"per_player": table.round(3), "correlations": {}}
    for col in ("trust_before", "trust_after"):
        sub = table[[col, "cooperation_rate"]].dropna()
        if len(sub) >= 3 and sub[col].nunique() > 1:
            result["correlations"][col] = round(
                float(sub[col].corr(sub["cooperation_rate"])), 3
            )
    return result


def compare_with_theory(summary):
    """Nash prediction versus what the class actually did."""
    return {
        "nash_prediction": "Mutual defection (D,D) in every round: cooperation rate 0.000",
        "observed_cooperation_rate": summary["cooperation_rate"],
        "observed_mutual_defection_rate": summary["mutual_defection_rate"],
        "gap": round(summary["cooperation_rate"] - 0.0, 3),
        "reading": (
            "Cooperation above 0 means observed play departs from the "
            "one-shot Nash prediction; repeated interaction gives players a "
            "reason to build and protect a cooperative record."
        ),
    }
