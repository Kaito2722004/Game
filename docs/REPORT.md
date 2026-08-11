# Report Working Draft

Chapter structure follows `docs/guide/06_Report_Structure.md`. Theory sections
are written out. Sections that depend on data are marked **[fill from results]**
and must not be written until the corresponding run has actually happened.

Primary textbook: Philip D. Straffin, *Game Theory and Strategy* — Ch. 11
(Nash Equilibria), Ch. 12 (The Prisoner's Dilemma), Ch. 13 (Application to
Social Psychology). Add exact page numbers from your copy.

---

## Chapter 1 — Introduction

**Background.** Game theory studies decisions where each person's outcome
depends on what others choose. The Prisoner's Dilemma is its best known
example because it shows individually rational choices producing a collectively
poor outcome.

**Problem statement.** Standard theory predicts mutual defection, yet people
frequently cooperate. This project tests that prediction two ways: with a
classroom experiment and with a computer tournament between fixed strategies.

**Objectives.**
1. Analyse the game formally: dominance, Nash equilibrium, Pareto comparison.
2. Measure how a class actually plays a 10-round Prisoner's Dilemma.
3. Rank six strategies in a round-robin iterated tournament.
4. Compare all three against each other.

**Research questions.**
1. Does the Nash prediction of mutual defection match human behaviour?
2. How does repeated interaction affect cooperation?
3. Which strategy performs best in an iterated tournament?
4. Does expected cooperation / trust relate to actual cooperation?

**Scope.** One payoff matrix, one class, six strategies, no noise, no
evolutionary dynamics. Limitations are in Chapter 6.

---

## Chapter 2 — Literature Review

**2.1 Game theory.** Players, strategies, actions, outcomes, payoffs.

**2.2 Two-person non-zero-sum games.** Unlike zero-sum games, both players can
gain or lose together, so there is something to bargain over and cooperation
becomes meaningful.

**2.3 Nash equilibrium.** A profile where no player can improve their own
payoff by changing strategy alone.

**2.4 The Prisoner's Dilemma.** Payoffs T=5, R=3, P=1, S=0 satisfying
T > R > P > S and R > (S+T)/2. Defection strictly dominates cooperation.

**2.5 Pareto optimality.** An outcome is Pareto-inferior if another outcome
makes at least one player better off and none worse off. (D,D)=(1,1) is
Pareto-inferior to (C,C)=(3,3).

**2.6 Repeated Prisoner's Dilemma.** Repetition lets a current choice change
future treatment. Under a *known* finite horizon, backward induction unravels
cooperation from the last round; under uncertain continuation, cooperation can
be sustained.

**2.7 Tit-for-Tat and Axelrod.** Axelrod's tournaments found TFT the strongest
entry. Its properties: **nice** (never defects first), **retaliatory**
(punishes at once), **forgiving** (returns to cooperation immediately), and
**clear** (easy for an opponent to understand).

**2.8 Trust and social psychology.** Straffin Ch. 13 links the game to trust
and suspicion in experimental settings.

---

## Chapter 3 — Methodology

**Payoff matrix.**

|              | B: Cooperate | B: Defect |
|--------------|-------------:|----------:|
| A: Cooperate | (3,3)        | (0,5)     |
| A: Defect    | (5,0)        | (1,1)     |

**Human experiment.** See `docs/EXPERIMENT_PROTOCOL.md`: pairs, 10 rounds,
simultaneous secret choices, recorded per round, optional 1–5 trust survey
before and after.

**Computer simulation.** Six strategies (AC, AD, TFT, GT, TF2T, RAND),
round robin, every strategy against every other, 100 rounds per match, seeded
RNG for reproducibility.

**Evaluation metrics.** Total score, average payoff per round, cooperation
rate, defection rate, rank; plus head-to-head average payoff.

---

## Chapter 4 — Implementation

```
Strategy modules ─→ Game engine ─→ Payoff calculator
                         │
                         ▼
                 Tournament engine ─→ Data storage (CSV/JSON)
                                          │
                                          ▼
                                  Statistics ─→ Visualisation
```

| Component | File | Responsibility |
|---|---|---|
| Payoff calculator | `src/pd/payoffs.py` | matrix, `payoff()`, dilemma conditions |
| Strategy modules | `src/pd/strategies.py` | six strategy functions + registry |
| Game engine | `src/pd/engine.py` | `play_match()`, per-round log |
| Tournament engine | `src/pd/tournament.py` | `run_tournament()` round robin |
| Statistics | `src/pd/stats.py` | ranking table, head-to-head, time series |
| Visualisation | `src/pd/viz.py` | four charts |
| Experiment analysis | `src/pd/experiment.py` | load, validate, summarise class data |
| Interactive game | `src/pd/play.py` | human vs strategy, for the live demo |

Design points worth stating in the report:

- Strategies are **stateless functions of history**, so no strategy can carry
  state between matches or read the opponent's current move.
- Payoffs in the human data are **recomputed from the choices**, so a scoring
  mistake made in class cannot reach the results.
- The tournament is **seeded**, so every number in Chapter 5 can be regenerated
  exactly.
- Correctness is checked by 43 unit tests, including hand-calculated match
  outcomes (e.g. TFT vs AD over 10 rounds must be 9–14).

---

## Chapter 5 — Results

### 5.1 Human experiment

**[fill from results]** Run `python main.py experiment` on the real class data,
then report: overall cooperation rate, defection rate, mutual-cooperation and
mutual-defection rates, mean payoff, cooperation by round (chart), and the
trust correlation if collected.

### 5.2 Computer tournament

Copy the table and figures from `results/RESULTS.md`, which is regenerated by
`python main.py tournament`. Do not retype the numbers by hand.

See `docs/FINDINGS.md` for the interpretation of the run committed with this
project.

---

## Chapter 6 — Discussion

Points to cover, each tied to a number rather than an impression:

- **Nash prediction vs observed behaviour.** Any cooperation above 0 departs
  from the one-shot prediction. Explain why: repetition, reputation within the
  pair, and social norms the model omits.
- **Individual vs collective rationality.** Mutual defection pays 1 each while
  mutual cooperation pays 3 each; the equilibrium is the worse of the two.
- **Repeated interaction.** Compare cooperation in early rounds with the final
  round. A drop at the end supports the backward-induction argument.
- **Trust.** Report the correlation and immediately state that a class of ~20
  cannot establish causation.
- **Tit-for-Tat's properties.** Nice, retaliatory, forgiving, clear — check
  each against the head-to-head table.
- **Why the top strategies score as they do.** Note that a strategy can win a
  tournament without ever beating an opponent head-to-head: TFT never scores
  more than its opponent in any single match, but it avoids the mutual
  punishment that pulls exploitative strategies down.
- **Limitations.** Small sample, one payoff matrix, no noise (misimplemented
  moves), fixed strategy set, students who may know the game already, no
  repeated play across pairs.

---

## Chapter 7 — Conclusion

Summarise: the theory's prediction, what the class actually did, which strategy
won and why, and what that says about cooperation under repetition. Future
work: add noise, add more strategies, run an evolutionary tournament where
successful strategies reproduce, or vary the payoff matrix towards Chicken or
Stag Hunt.

---

## References

- Straffin, P. D. *Game Theory and Strategy*. Mathematical Association of
  America. (Ch. 11, 12, 13 — add page numbers.)
- Axelrod, R. *The Evolution of Cooperation*. Basic Books, 1984.
- Nash, J. "Equilibrium points in n-person games." *PNAS* 36(1), 1950.
- This project's source code and generated results.
