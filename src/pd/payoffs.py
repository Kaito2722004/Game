"""Payoff matrix for the Prisoner's Dilemma.

Notation follows the project guide (Straffin, Game Theory and Strategy):
    T = temptation (defect against a cooperator) = 5
    R = reward     (mutual cooperation)          = 3
    P = punishment (mutual defection)            = 1   (written U in the guide)
    S = sucker     (cooperate against a defector)= 0

Two conditions must hold for the game to be a genuine Prisoner's Dilemma:
    T > R > P > S            -> defection is dominant
    R > (S + T) / 2          -> alternating exploitation is worse than mutual
                                cooperation, so cooperation is the efficient
                                outcome in the repeated game
"""

COOPERATE = "C"
DEFECT = "D"
ACTIONS = (COOPERATE, DEFECT)

T = 5
R = 3
P = 1
S = 0

# U is the guide's name for P; kept as an alias so the code matches the report.
U = P

PAYOFFS = {
    (COOPERATE, COOPERATE): (R, R),
    (COOPERATE, DEFECT): (S, T),
    (DEFECT, COOPERATE): (T, S),
    (DEFECT, DEFECT): (P, P),
}


def payoff(action_a, action_b):
    """Return (payoff to A, payoff to B) for one round.

    >>> payoff("C", "D")
    (0, 5)
    """
    if action_a not in ACTIONS or action_b not in ACTIONS:
        raise ValueError(
            "actions must be 'C' or 'D', got {!r} and {!r}".format(action_a, action_b)
        )
    return PAYOFFS[(action_a, action_b)]


def check_dilemma_conditions():
    """Verify the matrix really is a Prisoner's Dilemma.

    Returns a dict of condition -> bool so the report can cite it rather than
    asserting it by hand.
    """
    return {
        "T > R > P > S": T > R > P > S,
        "R > (S + T) / 2": R > (S + T) / 2,
    }


def matrix_markdown():
    """The payoff matrix as a markdown table, for the report and the CLI."""
    return (
        "|              | B: Cooperate | B: Defect |\n"
        "|--------------|-------------:|----------:|\n"
        "| A: Cooperate | ({r},{r})        | ({s},{t})     |\n"
        "| A: Defect    | ({t},{s})        | ({p},{p})     |"
    ).format(r=R, s=S, t=T, p=P)
