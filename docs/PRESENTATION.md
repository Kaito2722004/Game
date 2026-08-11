# Presentation Notes (19 slides)

Follows `docs/guide/07_Presentation_Outline.md`. One line per slide is what goes
*on* the slide; the indented text is what you *say*.

**1. Title** — Prisoner's Dilemma Strategy Tournament. Your name, course, date.

**2. What is game theory?**
> The study of decisions where your outcome depends on what someone else
> chooses. Three ingredients: players, strategies, payoffs.

**3. What is the Prisoner's Dilemma?**
> Two players choose privately: cooperate or defect. Neither sees the other's
> choice first. Both would do better cooperating, and both are tempted not to.

**4. Payoff matrix** — put the matrix up and leave it up.

|              | B: Cooperate | B: Defect |
|--------------|-------------:|----------:|
| A: Cooperate | (3,3)        | (0,5)     |
| A: Defect    | (5,0)        | (1,1)     |

> T=5, R=3, P=1, S=0, with T > R > P > S and R > (S+T)/2.

**5. Dominant strategy**
> If they cooperate, I get 3 by cooperating and 5 by defecting. If they defect,
> I get 0 by cooperating and 1 by defecting. Defection is better *both* times,
> so it strictly dominates. Same for them.

**6. Nash equilibrium**
> (D,D). Neither of us can improve alone — switching to C alone drops me from
> 1 to 0. It is the unique pure-strategy equilibrium.

**7. Pareto inferiority**
> (C,C) pays 3 each. (D,D) pays 1 each. The equilibrium is worse for *both* of
> us than an outcome we both preferred. That is the dilemma in one sentence.

**8. Why cooperation is difficult**
> Cooperating is not irrational because it is kind — it is unstable because
> defecting always pays more *this round*.

**9. Repeated Prisoner's Dilemma**
> Play repeatedly and this round's choice changes how you are treated next
> round. If the end is known, backward induction unravels cooperation from the
> last round; if continuation is uncertain, cooperation can survive.

**10. Tit-for-Tat**
> Cooperate first, then copy their last move. Nice, retaliatory, forgiving,
> clear — four properties, worth naming each.

**11. Human classroom experiment** — participants, 10 rounds, method.
> *[report your actual cooperation rate here]*

**12. Computer tournament** — round robin, 100 rounds per match, 15 matches.

**13. Strategies** — AC, AD, TFT, GT, TF2T, RAND, one line each.

**14. Results / graphs** — `results/tournament_scores.png` and
`results/cooperation_rates.png`.
> The top three all refuse to defect first. Always Defect comes fourth.

**15. Human vs theoretical prediction** — three bars: Nash 0%, class *[fill]*,
simulation 59%.

**16. Discussion** — the headline finding:
> Tit-for-Tat never wins a single match. Zero wins, three draws, two losses.
> It still finishes second, because drawing at 3 points a round beats winning
> at 1. Being nice is not a moral point here — it is arithmetic.

**17. Limitations** — small sample, one matrix, no noise, fixed strategy set,
Grim Trigger's win depends on Random being in the pool.

**18. Conclusion** — repetition changes the game; strategies that cooperate
first and retaliate immediately do best; the class's behaviour departs from
the one-shot prediction.

**19. References** — Straffin Ch. 11–13, Axelrod (1984), Nash (1950).

---

## Live demo

Two options, both under two minutes:

1. **Class demo.** Pick two volunteers, play 5 rounds on the board with the
   matrix visible, tally scores, then reveal what theory predicted.
2. **Play the program.** Project a terminal and let the room vote each round:

   ```bash
   python main.py play --opponent TFT --rounds 8
   ```

   Do not use `--reveal`. Let the room guess the strategy from its behaviour,
   then show the name at the end. Guessing it *is* the point of slide 10's
   "clear" property.

Rehearse slides 3–7 until you can do them in two minutes; the checklist asks
for the game explained in under two.
