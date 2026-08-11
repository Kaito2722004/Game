"""The payoff matrix value object.

A `PayoffMatrix` is any 2x2 two-person game. It is deliberately *not* assumed
to be a Prisoner's Dilemma: whether it is one is a question answered by
`app.game_theory.analysis`, computed from the numbers rather than assumed.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.game_theory.actions import Action, Outcome


@dataclass(frozen=True)
class PayoffPair:
    """Payoffs awarded to player A and player B for one outcome."""

    player_a: float
    player_b: float

    def as_tuple(self) -> tuple[float, float]:
        return (self.player_a, self.player_b)

    def for_player(self, player_a_perspective: bool) -> float:
        return self.player_a if player_a_perspective else self.player_b


@dataclass(frozen=True)
class PayoffMatrix:
    """A 2x2 payoff matrix in the standard Prisoner's Dilemma layout.

                     B: Cooperate    B: Defect
        A: Cooperate     cc             cd
        A: Defect        dc             dd

    Each cell holds the payoff to A and the payoff to B.
    """

    cc: PayoffPair
    cd: PayoffPair
    dc: PayoffPair
    dd: PayoffPair

    @classmethod
    def from_tuples(
        cls,
        cc: tuple[float, float],
        cd: tuple[float, float],
        dc: tuple[float, float],
        dd: tuple[float, float],
    ) -> "PayoffMatrix":
        return cls(
            cc=PayoffPair(*cc),
            cd=PayoffPair(*cd),
            dc=PayoffPair(*dc),
            dd=PayoffPair(*dd),
        )

    @classmethod
    def classic(cls) -> "PayoffMatrix":
        """The classic matrix used throughout the project: T=5, R=3, P=1, S=0."""
        return cls.from_tuples(cc=(3, 3), cd=(0, 5), dc=(5, 0), dd=(1, 1))

    def cell(self, outcome: Outcome) -> PayoffPair:
        return getattr(self, outcome.value.lower())

    def payoff(self, action_a: Action, action_b: Action) -> tuple[float, float]:
        """Payoffs (A, B) for one round of simultaneous play."""
        return self.cell(Outcome.from_actions(action_a, action_b)).as_tuple()

    def payoff_for(self, player_a_perspective: bool, own: Action, other: Action) -> float:
        """One player's payoff, from that player's own point of view.

        `own`/`other` are always ordered from the perspective of the player
        being asked about, so this works for either seat at the table.
        """
        if player_a_perspective:
            return self.payoff(own, other)[0]
        return self.payoff(other, own)[1]

    @property
    def outcomes(self) -> dict[Outcome, PayoffPair]:
        return {
            Outcome.CC: self.cc,
            Outcome.CD: self.cd,
            Outcome.DC: self.dc,
            Outcome.DD: self.dd,
        }

    @property
    def is_symmetric(self) -> bool:
        """True when both players face the same game.

        Symmetry requires the diagonal cells to pay both players equally and
        the off-diagonal cells to mirror each other.
        """
        return (
            self.cc.player_a == self.cc.player_b
            and self.dd.player_a == self.dd.player_b
            and self.cd.player_a == self.dc.player_b
            and self.cd.player_b == self.dc.player_a
        )

    def to_dict(self) -> dict[str, dict[str, float]]:
        return {
            key.value: {
                "player_a_payoff": pair.player_a,
                "player_b_payoff": pair.player_b,
            }
            for key, pair in self.outcomes.items()
        }
