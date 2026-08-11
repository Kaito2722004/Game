"""Charts for the results chapter and the slide deck."""

import matplotlib

matplotlib.use("Agg")  # write files, never open a window
import matplotlib.pyplot as plt  # noqa: E402

from .stats import (  # noqa: E402
    calculate_statistics,
    cooperation_over_time,
    head_to_head,
)

FIGSIZE = (8, 5)
DPI = 150


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path


def plot_total_scores(results, path):
    summary = calculate_statistics(results)
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.bar(summary["Code"], summary["Total Score"], color="#3f6fb5")
    ax.set_title("Tournament score by strategy ({} rounds per match)".format(
        results["meta"]["rounds_per_match"]))
    ax.set_xlabel("Strategy")
    ax.set_ylabel("Total score (one full round robin)")
    for x, y in zip(summary["Code"], summary["Total Score"]):
        ax.text(x, y, "{:.0f}".format(y), ha="center", va="bottom", fontsize=9)
    ax.margins(y=0.12)
    return _save(fig, path)


def plot_cooperation_rates(results, path):
    summary = calculate_statistics(results).sort_values("Cooperation Rate", ascending=False)
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.bar(summary["Code"], summary["Cooperation Rate"], color="#4f9d69")
    ax.set_ylim(0, 1.05)
    ax.set_title("Cooperation rate by strategy")
    ax.set_xlabel("Strategy")
    ax.set_ylabel("Fraction of rounds cooperating")
    for x, y in zip(summary["Code"], summary["Cooperation Rate"]):
        ax.text(x, y, "{:.2f}".format(y), ha="center", va="bottom", fontsize=9)
    return _save(fig, path)


def plot_head_to_head(results, path):
    table = head_to_head(results)
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    im = ax.imshow(table.values, cmap="YlGnBu", vmin=0, vmax=5)
    ax.set_xticks(range(len(table.columns)), table.columns)
    ax.set_yticks(range(len(table.index)), table.index)
    ax.set_title("Average payoff per round\n(row strategy vs column opponent)")
    ax.set_xlabel("Opponent")
    ax.set_ylabel("Strategy")
    for i in range(len(table.index)):
        for j in range(len(table.columns)):
            value = table.values[i][j]
            if value == value:  # skip NaN (a strategy never plays itself)
                ax.text(
                    j, i, "{:.2f}".format(value),
                    ha="center", va="center", fontsize=9,
                    color="white" if value > 3.2 else "black",
                )
    fig.colorbar(im, ax=ax, label="Payoff per round")
    return _save(fig, path)


def plot_cooperation_over_time(results, path):
    data = cooperation_over_time(results)
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(data["block"], data["cooperation_rate"], marker="o", color="#b5573f")
    ax.set_ylim(0, 1.05)
    ax.set_title("Cooperation rate across the length of a match")
    ax.set_xlabel("Round block (first round of each block)")
    ax.set_ylabel("Cooperation rate, all strategies pooled")
    ax.grid(alpha=0.3)
    return _save(fig, path)


def plot_results(results, outdir):
    """Write every tournament chart into `outdir`. Returns the list of paths."""
    outdir = str(outdir).rstrip("/\\")
    return [
        plot_total_scores(results, outdir + "/tournament_scores.png"),
        plot_cooperation_rates(results, outdir + "/cooperation_rates.png"),
        plot_head_to_head(results, outdir + "/head_to_head.png"),
        plot_cooperation_over_time(results, outdir + "/cooperation_over_time.png"),
    ]


def plot_human_results(human_summary, path):
    """Bar chart of cooperation rate per round from the classroom experiment."""
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.bar(human_summary["round"], human_summary["cooperation_rate"], color="#7a5db5")
    ax.set_ylim(0, 1.05)
    ax.set_title("Human experiment: cooperation rate by round")
    ax.set_xlabel("Round")
    ax.set_ylabel("Fraction of players cooperating")
    ax.set_xticks(list(human_summary["round"]))
    return _save(fig, path)
