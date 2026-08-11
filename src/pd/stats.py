"""Turn raw tournament output into the tables the report needs."""

import pandas as pd

from .strategies import STRATEGIES, strategy_name


def matches_frame(results):
    """Raw match rows as a DataFrame."""
    return pd.DataFrame(results["matches"])


def round_log_frame(results):
    """Every round of every match as a DataFrame."""
    return pd.DataFrame(results["round_log"])


def calculate_statistics(results):
    """Per-strategy summary table, ranked by total score.

    Columns: Code, Strategy, Total Score, Average (per round), Cooperation
    Rate, Defection Rate, Rank. Scores are averaged over repeats so that the
    "Total Score" column always means "points earned in one full round robin".
    """
    df = matches_frame(results)
    repeats = results["meta"]["repeats"]

    grouped = df.groupby("strategy", sort=False).agg(
        total_score=("score", "sum"),
        rounds_played=("rounds", "sum"),
        cooperation_rate=("cooperation_rate", "mean"),
    )
    grouped["total_score"] = grouped["total_score"] / repeats
    grouped["rounds_played"] = grouped["rounds_played"] / repeats
    grouped["average_per_round"] = grouped["total_score"] / grouped["rounds_played"]
    grouped["defection_rate"] = 1.0 - grouped["cooperation_rate"]

    summary = grouped.reset_index()
    summary.insert(1, "name", summary["strategy"].map(strategy_name))
    summary = summary.sort_values("total_score", ascending=False).reset_index(drop=True)
    summary["rank"] = summary["total_score"].rank(ascending=False, method="min").astype(int)

    summary = summary[
        [
            "rank",
            "strategy",
            "name",
            "total_score",
            "average_per_round",
            "cooperation_rate",
            "defection_rate",
            "rounds_played",
        ]
    ]
    summary.columns = [
        "Rank",
        "Code",
        "Strategy",
        "Total Score",
        "Average",
        "Cooperation Rate",
        "Defection Rate",
        "Rounds Played",
    ]
    return summary.round(
        {
            "Total Score": 1,
            "Average": 3,
            "Cooperation Rate": 3,
            "Defection Rate": 3,
            "Rounds Played": 0,
        }
    )


def head_to_head(results):
    """Matrix of average score per round: row strategy against column opponent."""
    df = matches_frame(results)
    df = df.assign(per_round=df["score"] / df["rounds"])
    table = df.pivot_table(
        index="strategy", columns="opponent", values="per_round", aggfunc="mean"
    )
    order = [c for c in STRATEGIES if c in table.index]
    return table.reindex(index=order, columns=order).round(3)


def cooperation_over_time(results, bins=10):
    """Overall cooperation rate in each block of rounds.

    Used to show whether cooperation builds up or breaks down as a match runs.
    """
    log = round_log_frame(results)
    if log.empty:
        return pd.DataFrame(columns=["block", "cooperation_rate"])

    max_round = int(log["round"].max())
    block_size = max(1, max_round // bins)
    long = pd.concat(
        [
            log[["round", "action_a"]].rename(columns={"action_a": "action"}),
            log[["round", "action_b"]].rename(columns={"action_b": "action"}),
        ]
    )
    long["block"] = ((long["round"] - 1) // block_size) * block_size + 1
    out = (
        long.assign(cooperated=(long["action"] == "C").astype(float))
        .groupby("block", as_index=False)["cooperated"]
        .mean()
        .rename(columns={"cooperated": "cooperation_rate"})
    )
    return out.round(3)


def frame_markdown(df, index_label=""):
    """Render a DataFrame as a markdown table.

    Written by hand rather than using DataFrame.to_markdown so the project
    needs no `tabulate` dependency.
    """
    headers = [index_label] + [str(c) for c in df.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] + ["---:"] * len(df.columns)) + "|",
    ]
    for label, row in df.iterrows():
        cells = ["" if v != v else "{:g}".format(v) if isinstance(v, float) else str(v)
                 for v in row]
        lines.append("| " + " | ".join([str(label)] + cells) + " |")
    return "\n".join(lines)


def summary_markdown(summary):
    """Summary table in the markdown shape used by the guide."""
    lines = [
        "| Strategy | Total Score | Average | Cooperation Rate | Rank |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, row in summary.iterrows():
        lines.append(
            "| {} | {:.0f} | {:.3f} | {:.3f} | {} |".format(
                row["Code"],
                row["Total Score"],
                row["Average"],
                row["Cooperation Rate"],
                row["Rank"],
            )
        )
    return "\n".join(lines)
