"""Tests for the tournament engine, the statistics, and the human-data loader."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from pd.experiment import (  # noqa: E402
    compare_with_theory,
    cooperation_by_round,
    experiment_summary,
    load_experiment,
    trust_analysis,
)
from pd.stats import calculate_statistics, head_to_head  # noqa: E402
from pd.tournament import run_tournament  # noqa: E402

CSV = """pair,round,choice_a,choice_b,trust_before_a,trust_before_b,trust_after_a,trust_after_b
P01,1,C,C,4,4,5,5
P01,2,C,C,4,4,5,5
P02,1,D,C,2,5,1,2
P02,2,D,D,2,5,1,2
"""


class TestTournament(unittest.TestCase):
    def setUp(self):
        self.results = run_tournament(rounds=20, seed=1)

    def test_every_pair_plays_once(self):
        # 6 strategies choose 2 = 15 matches, each stored from both sides.
        self.assertEqual(self.results["meta"]["matches_played"], 15)
        self.assertEqual(len(self.results["matches"]), 30)

    def test_no_strategy_plays_itself_by_default(self):
        for row in self.results["matches"]:
            self.assertNotEqual(row["strategy"], row["opponent"])

    def test_self_play_can_be_enabled(self):
        results = run_tournament(rounds=5, seed=1, include_self=True)
        self.assertEqual(results["meta"]["matches_played"], 15 + 6)

    def test_round_log_covers_every_round(self):
        self.assertEqual(len(self.results["round_log"]), 15 * 20)

    def test_run_is_reproducible_from_the_seed(self):
        again = run_tournament(rounds=20, seed=1)
        self.assertEqual(
            [r["score"] for r in self.results["matches"]],
            [r["score"] for r in again["matches"]],
        )

    def test_different_seed_changes_only_random_matches(self):
        other = run_tournament(rounds=20, seed=999)
        summary_a = calculate_statistics(self.results).set_index("Code")["Total Score"]
        summary_b = calculate_statistics(other).set_index("Code")["Total Score"]
        # AC vs AD and similar deterministic pairings are unaffected; RAND is not.
        self.assertNotEqual(summary_a["RAND"], summary_b["RAND"])


class TestStatistics(unittest.TestCase):
    def setUp(self):
        self.results = run_tournament(rounds=100, seed=42)
        self.summary = calculate_statistics(self.results)

    def test_one_row_per_strategy(self):
        self.assertEqual(len(self.summary), 6)

    def test_ranked_best_first(self):
        scores = list(self.summary["Total Score"])
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(self.summary.iloc[0]["Rank"], 1)

    def test_rates_are_complementary(self):
        for _, row in self.summary.iterrows():
            self.assertAlmostEqual(
                row["Cooperation Rate"] + row["Defection Rate"], 1.0, places=2
            )

    def test_known_extremes(self):
        indexed = self.summary.set_index("Code")
        self.assertEqual(indexed.loc["AC", "Cooperation Rate"], 1.0)
        self.assertEqual(indexed.loc["AD", "Cooperation Rate"], 0.0)

    def test_average_is_score_over_rounds(self):
        for _, row in self.summary.iterrows():
            self.assertAlmostEqual(
                row["Average"],
                row["Total Score"] / row["Rounds Played"],
                places=2,
            )

    def test_head_to_head_diagonal_is_empty(self):
        table = head_to_head(self.results)
        for code in table.index:
            self.assertTrue(table.loc[code, code] != table.loc[code, code])  # NaN

    def test_repeats_do_not_inflate_the_total(self):
        # Averaging over repeats must keep "Total Score" on the scale of one
        # round robin. Checked without RAND so the totals are deterministic.
        deterministic = ["AC", "AD", "TFT", "GT", "TF2T"]
        once = calculate_statistics(
            run_tournament(deterministic, rounds=50, seed=3, repeats=1))
        thrice = calculate_statistics(
            run_tournament(deterministic, rounds=50, seed=3, repeats=3))
        self.assertEqual(
            once.set_index("Code").loc["AC", "Total Score"],
            thrice.set_index("Code").loc["AC", "Total Score"],
        )


class TestExperimentLoader(unittest.TestCase):
    def _write(self, text):
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".csv", delete=False, encoding="utf-8"
        )
        handle.write(text)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return handle.name

    def test_loads_and_recomputes_payoffs(self):
        df = load_experiment(self._write(CSV))
        self.assertEqual(len(df), 4)
        row = df[(df["pair"] == "P02") & (df["round"] == 1)].iloc[0]
        self.assertEqual((row["payoff_a"], row["payoff_b"]), (5, 0))

    def test_summary_counts_both_players(self):
        summary = experiment_summary(load_experiment(self._write(CSV)))
        self.assertEqual(summary["decisions"], 8)
        self.assertEqual(summary["pairs"], 2)
        self.assertAlmostEqual(summary["cooperation_rate"], 5 / 8)

    def test_cooperation_by_round(self):
        by_round = cooperation_by_round(load_experiment(self._write(CSV)))
        self.assertEqual(list(by_round["round"]), [1, 2])

    def test_compare_with_theory_reports_the_gap(self):
        summary = experiment_summary(load_experiment(self._write(CSV)))
        comparison = compare_with_theory(summary)
        self.assertEqual(comparison["gap"], summary["cooperation_rate"])

    def test_trust_analysis_returns_per_player_rows(self):
        trust = trust_analysis(load_experiment(self._write(CSV)))
        self.assertEqual(len(trust["per_player"]), 4)

    def test_trust_analysis_absent_without_survey_columns(self):
        stripped = "pair,round,choice_a,choice_b\nP01,1,C,C\n"
        self.assertIsNone(trust_analysis(load_experiment(self._write(stripped))))

    def test_rejects_invalid_choice(self):
        with self.assertRaises(ValueError):
            load_experiment(self._write("pair,round,choice_a,choice_b\nP01,1,C,X\n"))

    def test_rejects_missing_column(self):
        with self.assertRaises(ValueError):
            load_experiment(self._write("pair,round,choice_a\nP01,1,C\n"))

    def test_rejects_duplicate_pair_round(self):
        text = "pair,round,choice_a,choice_b\nP01,1,C,C\nP01,1,D,D\n"
        with self.assertRaises(ValueError):
            load_experiment(self._write(text))


if __name__ == "__main__":
    unittest.main()
