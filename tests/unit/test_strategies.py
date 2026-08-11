"""Each strategy's rule, checked directly against its definition."""

from __future__ import annotations

import random

import pytest

from app.game_theory.actions import Action, StrategyCategory
from app.strategies.always_cooperate import AlwaysCooperate
from app.strategies.always_defect import AlwaysDefect
from app.strategies.grim_trigger import GrimTrigger
from app.strategies.random_strategy import RandomStrategy
from app.strategies.registry import UnknownStrategyError, strategy_registry
from app.strategies.tit_for_tat import TitForTat
from app.strategies.tit_for_two_tats import TitForTwoTats

C = Action.COOPERATE
D = Action.DEFECT


class TestAlwaysCooperate:
    def test_cooperates_on_the_first_move(self):
        assert AlwaysCooperate().choose_action([], []) is C

    def test_cooperates_even_after_being_exploited(self):
        assert AlwaysCooperate().choose_action([C, C, C], [D, D, D]) is C


class TestAlwaysDefect:
    def test_defects_on_the_first_move(self):
        assert AlwaysDefect().choose_action([], []) is D

    def test_defects_even_against_a_cooperator(self):
        assert AlwaysDefect().choose_action([D, D], [C, C]) is D


class TestTitForTat:
    def test_opens_with_cooperation(self):
        assert TitForTat().choose_action([], []) is C

    def test_copies_the_opponents_last_move(self):
        assert TitForTat().choose_action([C], [D]) is D
        assert TitForTat().choose_action([D], [C]) is C

    def test_only_the_most_recent_move_matters(self):
        assert TitForTat().choose_action([C, D, D], [D, D, C]) is C

    def test_is_nice(self):
        """It never defects first: against pure cooperation it always cooperates."""
        history: list[Action] = []
        strategy = TitForTat()
        for _ in range(20):
            action = strategy.choose_action(history, [C] * len(history))
            assert action is C
            history.append(action)


class TestGrimTrigger:
    def test_opens_with_cooperation(self):
        assert GrimTrigger().choose_action([], []) is C

    def test_keeps_cooperating_while_the_opponent_does(self):
        assert GrimTrigger().choose_action([C, C], [C, C]) is C

    def test_defects_after_a_single_defection(self):
        assert GrimTrigger().choose_action([C], [D]) is D

    def test_never_forgives(self):
        # One defection long ago, cooperation ever since: still defects.
        assert GrimTrigger().choose_action([C, D, D], [D, C, C]) is D


class TestTitForTwoTats:
    def test_cooperates_for_the_first_two_rounds(self):
        assert TitForTwoTats().choose_action([], []) is C
        assert TitForTwoTats().choose_action([C], [D]) is C

    def test_absorbs_an_isolated_defection(self):
        assert TitForTwoTats().choose_action([C, C], [C, D]) is C

    def test_retaliates_after_two_consecutive_defections(self):
        assert TitForTwoTats().choose_action([C, C], [D, D]) is D

    def test_forgives_once_the_opponent_cooperates_again(self):
        assert TitForTwoTats().choose_action([C, C, C], [D, D, C]) is C

    def test_two_defections_must_be_consecutive(self):
        assert TitForTwoTats().choose_action([C, C, C], [D, C, D]) is C


class TestRandomStrategy:
    def test_only_returns_valid_actions(self):
        strategy = RandomStrategy(rng=random.Random(1))
        seen = {strategy.choose_action([], []) for _ in range(200)}
        assert seen == {C, D}

    def test_is_reproducible_from_a_seed(self):
        first = [RandomStrategy(rng=random.Random(7)).choose_action([], [])]
        strategy_a = RandomStrategy(rng=random.Random(7))
        strategy_b = RandomStrategy(rng=random.Random(7))
        sequence_a = [strategy_a.choose_action([], []) for _ in range(50)]
        sequence_b = [strategy_b.choose_action([], []) for _ in range(50)]
        assert sequence_a == sequence_b
        assert first[0] == sequence_a[0]

    def test_different_seeds_diverge(self):
        a = [RandomStrategy(rng=random.Random(1)).choose_action([], []) for _ in range(1)]
        strategy_a = RandomStrategy(rng=random.Random(1))
        strategy_b = RandomStrategy(rng=random.Random(2))
        sequence_a = [strategy_a.choose_action([], []) for _ in range(50)]
        sequence_b = [strategy_b.choose_action([], []) for _ in range(50)]
        assert sequence_a != sequence_b
        assert a  # first draw is deterministic given the seed

    def test_is_roughly_balanced_over_many_draws(self):
        strategy = RandomStrategy(rng=random.Random(42))
        draws = [strategy.choose_action([], []) for _ in range(2000)]
        cooperation_rate = draws.count(C) / len(draws)
        assert 0.45 < cooperation_rate < 0.55


class TestRegistry:
    def test_all_six_strategies_are_registered(self):
        assert set(strategy_registry.ids()) == {
            "ALWAYS_COOPERATE",
            "ALWAYS_DEFECT",
            "TIT_FOR_TAT",
            "GRIM_TRIGGER",
            "TIT_FOR_TWO_TATS",
            "RANDOM",
        }

    def test_lookup_is_case_insensitive(self):
        assert strategy_registry.get("tit_for_tat") is TitForTat

    def test_unknown_strategy_raises(self):
        with pytest.raises(UnknownStrategyError) as exc_info:
            strategy_registry.get("NOT_A_STRATEGY")
        assert "available" in str(exc_info.value)

    def test_create_returns_a_fresh_instance(self):
        first = strategy_registry.create("TIT_FOR_TAT")
        second = strategy_registry.create("TIT_FOR_TAT")
        assert first is not second

    def test_metadata_is_complete_for_every_strategy(self):
        for metadata in strategy_registry.all_metadata():
            assert metadata.id and metadata.name and metadata.description
            assert metadata.rules
            assert isinstance(metadata.category, StrategyCategory)

    def test_only_random_is_non_deterministic(self):
        non_deterministic = [
            meta.id for meta in strategy_registry.all_metadata() if not meta.is_deterministic
        ]
        assert non_deterministic == ["RANDOM"]

    def test_registering_a_duplicate_id_is_rejected(self):
        with pytest.raises(ValueError):
            strategy_registry.register(TitForTat)
