# Python Implementation Plan

Recommended stack:
- Python
- pandas
- matplotlib
- optional: Streamlit for a simple interface

Architecture:

Strategy
  -> Game Engine
  -> Payoff Calculator
  -> Tournament Engine
  -> Data Storage
  -> Statistics
  -> Visualization

Core functions to build:
1. payoff(action_a, action_b)
2. strategy_always_cooperate(...)
3. strategy_always_defect(...)
4. strategy_tit_for_tat(...)
5. strategy_grim_trigger(...)
6. strategy_tit_for_two_tats(...)
7. strategy_random(...)
8. play_match(strategy_a, strategy_b, rounds)
9. run_tournament(strategies)
10. calculate_statistics(results)
11. plot_results(results)

Recommended first milestone:
Implement only AC, AD, and TFT and verify the payoff calculations manually before adding more strategies.
