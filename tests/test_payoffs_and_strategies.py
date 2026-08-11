"""Verify the payoff arithmetic and each strategy by hand.

The guide's first milestone is "verify the payoff calculations manually before
adding more strategies" - these tests are that verification, kept permanently.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from pd import strategies as st  # noqa: E402
from pd.engine import cooperation_rate, play_match  # noqa: E402
from pd.payoffs import check_dilemma_conditions, payoff  # noqa: E402


class TestPayoffs(unittest.TestCase):
    def test_four_cells(self):
        self.assertEqual(payoff("C", "C"), (3, 3))
        self.assertEqual(payoff("C", "D"), (0, 5))
        self.assertEqual(payoff("D", "C"), (5, 0))
        self.assertEqual(payoff("D", "D"), (1, 1))

    def test_symmetry(self):
        for a in "CD":
            for b in "CD":
                self.assertEqual(payoff(a, b), tuple(reversed(payoff(b, a))))

    def test_dilemma_conditions_hold(self):
        for condition, holds in check_dilemma_conditions().items():
            self.assertTrue(holds, condition)

    def test_rejects_bad_action(self):
        with self.assertRaises(ValueError):
            payoff("C", "X")


class TestStrategies(unittest.TestCase):
    def test_always_cooperate(self):
        self.assertEqual(st.strategy_always_cooperate([], []), "C")
        self.assertEqual(st.strategy_always_cooperate(["C"], ["D", "D"]), "C")

    def test_always_defect(self):
        self.assertEqual(st.strategy_always_defect([], []), "D")
        self.assertEqual(st.strategy_always_defect(["D"], ["C", "C"]), "D")

    def test_tit_for_tat_opens_with_cooperation(self):
        self.assertEqual(st.strategy_tit_for_tat([], []), "C")

    def test_tit_for_tat_copies_last_move(self):
        self.assertEqual(st.strategy_tit_for_tat(["C"], ["D"]), "D")
        self.assertEqual(st.strategy_tit_for_tat(["D"], ["D", "C"]), "C")

    def test_grim_trigger_never_forgives(self):
        self.assertEqual(st.strategy_grim_trigger([], []), "C")
        self.assertEqual(st.strategy_grim_trigger(["C"], ["C", "C"]), "C")
        self.assertEqual(st.strategy_grim_trigger(["C"], ["D", "C", "C"]), "D")

    def test_tit_for_two_tats_needs_two_defections(self):
        self.assertEqual(st.strategy_tit_for_two_tats([], []), "C")
        self.assertEqual(st.strategy_tit_for_two_tats(["C"], ["D"]), "C")
        self.assertEqual(st.strategy_tit_for_two_tats(["C"], ["C", "D"]), "C")
        self.assertEqual(st.strategy_tit_for_two_tats(["C"], ["D", "D"]), "D")
        self.assertEqual(st.strategy_tit_for_two_tats(["C"], ["D", "D", "C"]), "C")

    def test_random_only_returns_valid_actions(self):
        import random

        rng = random.Random(1)
        seen = {st.strategy_random([], [], rng) for _ in range(200)}
        self.assertEqual(seen, {"C", "D"})

    def test_lookup_rejects_unknown_code(self):
        with self.assertRaises(KeyError):
            st.get_strategy("NOPE")


class TestMatches(unittest.TestCase):
    def test_ac_vs_ad_is_a_total_exploitation(self):
        result = play_match("AC", "AD", rounds=10)
        self.assertEqual(result.score_a, 0)      # 10 x S
        self.assertEqual(result.score_b, 50)     # 10 x T

    def test_ac_vs_ac_is_mutual_cooperation(self):
        result = play_match("AC", "AC", rounds=10)
        self.assertEqual((result.score_a, result.score_b), (30, 30))

    def test_ad_vs_ad_is_the_nash_outcome(self):
        result = play_match("AD", "AD", rounds=10)
        self.assertEqual((result.score_a, result.score_b), (10, 10))

    def test_tft_vs_ad_loses_only_the_first_round(self):
        result = play_match("TFT", "AD", rounds=10)
        # Round 1: (0,5). Rounds 2-10: (1,1) x 9.
        self.assertEqual(result.score_a, 9)
        self.assertEqual(result.score_b, 14)

    def test_tft_vs_tft_cooperates_throughout(self):
        result = play_match("TFT", "TFT", rounds=100)
        self.assertEqual((result.score_a, result.score_b), (300, 300))
        self.assertEqual(cooperation_rate(result.history_a), 1.0)

    def test_tf2t_absorbs_a_single_defection(self):
        # GT never defects first, so TF2T vs GT stays cooperative.
        result = play_match("TF2T", "GT", rounds=20)
        self.assertEqual((result.score_a, result.score_b), (60, 60))

    def test_grim_trigger_punishes_forever(self):
        result = play_match("GT", "AD", rounds=10)
        self.assertEqual(result.history_a, ["C"] + ["D"] * 9)

    def test_score_equals_sum_of_round_payoffs(self):
        result = play_match("TFT", "RAND", rounds=50)
        self.assertEqual(result.score_a, sum(r["payoff_a"] for r in result.round_log))
        self.assertEqual(result.score_b, sum(r["payoff_b"] for r in result.round_log))

    def test_rounds_must_be_positive(self):
        with self.assertRaises(ValueError):
            play_match("AC", "AD", rounds=0)


if __name__ == "__main__":
    unittest.main()
