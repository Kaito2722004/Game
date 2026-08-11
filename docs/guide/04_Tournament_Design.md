# Axelrod-Style Tournament Design

Strategies:
- AC: Always Cooperate
- AD: Always Defect
- TFT: Tit-for-Tat
- GT: Grim Trigger
- TF2T: Tit-for-Two-Tats
- RAND: Random

Match rules:
- Every strategy plays every other strategy.
- Each match has 100 rounds.
- Payoff matrix:
  CC=(3,3), CD=(0,5), DC=(5,0), DD=(1,1).
- Sum payoffs across rounds.
- Rank strategies by tournament score.

Suggested output:
| Strategy | Total Score | Average | Cooperation Rate | Rank |
|---|---:|---:|---:|---:|
| TFT | | | | |
| GT | | | | |
| AD | | | | |
| AC | | | | |
| TF2T | | | | |
| RAND | | | | |

Do not fill results before actually running the simulation.
