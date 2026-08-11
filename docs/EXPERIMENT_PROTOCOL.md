# Human Experiment Protocol (Phase 2)

Run this before writing Chapter 5. The software cannot produce the human
results for you — it can only analyse the sheet you bring back.

## Setup

- Participants: about 20 students, forming 10 pairs (adjust to your class).
- Rounds: 10 per pair.
- Payoff matrix: the same one the simulation uses — CC=(3,3), CD=(0,5),
  DC=(5,0), DD=(1,1).
- Materials: one slip per player per round, or a folded answer sheet.

## Instructions to read aloud

> You and your partner will play 10 rounds. Each round you privately choose C
> or D and reveal at the same time. Points: if you both choose C you each get
> 3. If you both choose D you each get 1. If one chooses D and the other C,
> the one who chose D gets 5 and the other gets 0. Points are just points —
> try to earn as many as you can for yourself. Do not discuss your choice
> before revealing.

Tell participants that taking part is voluntary, that only C/D choices are
recorded, and that no names appear in the report. Follow whatever consent
procedure your school requires.

## Whether to announce the number of rounds

This is a real design decision and the report should state which you chose:

- **Announced 10 rounds** — a known finite horizon. Backward induction
  predicts defection from round 10 backwards, so watch for end-game
  unravelling in the by-round chart.
- **Unannounced / "we'll play for a while"** — uncertain continuation, which
  is the condition under which the theory allows cooperation to survive.

The default template assumes 10 announced rounds.

## Optional trust survey

Before play: "How likely do you think your opponent is to cooperate?" (1–5)
After play: "How much did you trust your opponent?" (1–5)

Record both in the CSV. The analysis reports a correlation with actual
cooperation. With ~20 participants this is descriptive only — never write it
up as evidence that trust *causes* cooperation.

## Recording the data

1. Copy `data/human_experiment_template.csv` to `data/human_experiment.csv`.
2. Fill in one row per pair per round: `pair, round, choice_a, choice_b`,
   plus the survey columns if you used them.
3. Do not enter payoffs — they are recomputed from the choices, which catches
   arithmetic slips made during the session.
4. Run:

   ```bash
   python main.py experiment --data data/human_experiment.csv
   ```

## What you get back

- `results/human_by_round.csv` and `.png` — cooperation rate per round
- `results/human_by_pair.csv` — cooperation rate and mean payoff per pair
- `results/human_summary.json` — headline rates and the Nash comparison
- `results/human_clean.csv` — validated data with recomputed payoffs

## Common problems

| Problem | Fix |
|---|---|
| `contains value(s) that are not C or D` | A cell has a stray letter, a blank, or a "1"/"0". Fix the sheet. |
| `duplicate pair/round entries` | The same round was entered twice for a pair. |
| A pair played fewer rounds | Fine — the loader does not require equal round counts, but say so in the limitations section. |
