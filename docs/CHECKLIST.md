# Project Checklist — current status

From `docs/guide/10_Checklist.md`. `[x]` done in this repository, `[ ]` still
yours to do.

## Theory
- [x] Payoff matrix — `src/pd/payoffs.py`, printed by `python main.py theory`
- [x] T > R > P/U > S verified in code and in a test
- [x] Dominant strategy explained
- [x] Nash equilibrium explained
- [x] Pareto comparison explained
- [x] Repeated-game discussion — `docs/REPORT.md` §2.6
- [x] Tit-for-Tat explanation — nice, retaliatory, forgiving, clear

## Experiment
- [x] Protocol written — `docs/EXPERIMENT_PROTOCOL.md`
- [x] Data sheet — `data/human_experiment_template.csv`
- [x] Analysis code — cooperation rate, defection rate, payoffs, by round, by pair, trust
- [ ] **Recruit participants and get whatever consent your school requires**
- [ ] **Run the session and fill in the sheet**
- [ ] **Run `python main.py experiment --data data/human_experiment.csv`**

## Software
- [x] Python environment — `requirements.txt` (pandas, matplotlib)
- [x] Game engine — `play_match()`
- [x] Six strategies
- [x] Round-robin tournament
- [x] Score table — `results/tournament_summary.csv`
- [x] Graphs — four PNGs in `results/`
- [x] 43 unit tests, all passing

## Report
- [x] Working draft with all theory chapters written — `docs/REPORT.md`
- [x] Results chapter for the simulation — `results/RESULTS.md`, `docs/FINDINGS.md`
- [ ] **Chapter 5.1 — human results (needs the experiment)**
- [ ] **Chapter 6 discussion comparing all three sources**
- [ ] **Chapter 7 conclusion**
- [ ] **References with real page numbers from your copy of Straffin**

## Presentation
- [x] Slide-by-slide notes — `docs/PRESENTATION.md`
- [x] Payoff matrix slide content
- [x] Tournament results and charts ready to drop in
- [x] Live demo scripted — `python main.py play`
- [ ] **Build the actual slide file**
- [ ] **Rehearse the game explanation to under 2 minutes**
- [ ] **Add your human results to slides 11 and 15**

## Order to work in
1. Read `docs/guide/08_Beginner_Learning_Roadmap.md` and be able to explain why
   (D,D) is a Nash equilibrium and Pareto-inferior to (C,C).
2. Run `python main.py theory` and check it matches your own reasoning.
3. Play a few rounds: `python main.py play -o TFT`, then `-o GT`, then `-o AD`.
4. Read `docs/FINDINGS.md`.
5. Run the classroom session.
6. Analyse it, then write Chapters 5–7.
