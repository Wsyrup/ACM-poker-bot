#file to calculate hand equity (preflop, flop, turn, river)
#using monte carlo simulation.

"""
Hand equity calculation module for poker bot decision making.

This module provides functions to estimate the probability that a given hand
will win against opponent hands using Monte Carlo simulation.

It uses the fast hand_eval module for quick hand comparison.
"""

from itertools import combinations
from hand_eval import evaluate_hand, evaluate_best_hand
import random

#simpler function, for more widespread use
def estimate_equity(hero_hole: list[str], villain_range: list[str], num_opps: int, community_hand: list[str], num_sims: int):
    wins = 0.0
    ties = 0.0
    hero_best_rank = 100000

    # Find best possible hand for hero
    for hand in combinations(hero_hole + community_hand, 5):
        hero_rank = evaluate_hand(hand)
        if hero_rank < hero_best_rank:
            hero_best_rank = hero_rank

    # Run Monte Carlo simulations: randomly sample opponent hands
    for _ in range(num_sims):
        best_opponent_rank = 100000
        
        # For each opponent, randomly sample 2 hole cards from villain range
        for _ in range(num_opps):
            # Sample opponent hole cards from the villain range
            if len(villain_range) >= 2:
                sampled_hole = random.sample(villain_range, 2)
            else:
                sampled_hole = villain_range
            
            # Find best 5-card hand for this opponent
            for hand in combinations(sampled_hole + community_hand, 5):
                opponent_rank = evaluate_hand(hand)
                if opponent_rank < best_opponent_rank:
                    best_opponent_rank = opponent_rank
        
        if hero_best_rank < best_opponent_rank:
            wins += 1
        elif hero_best_rank == best_opponent_rank:
            ties += 1
    
    # Equity = (wins + 0.5 * ties) / num_sims
    # This ensures ties split the equity equally regardless of num_opps
    return (wins + (0.5 * ties)) / num_opps / num_sims if villain_range else 0


# if __name__ == "__main__":
#     # Example usage
#     my_hand = ['as', 'ad', 'kh', 'qc', 'jh']
#     opp_hand1 = ['ks', 'kd', '9h', '8c', '7h']
#     opp_hand2 = ['2s', '3d', '4h', '5c', '6h']
    
#     equity = estimate_equity_5cards(my_hand, [opp_hand1, opp_hand2])
#     print(f"My hand {my_hand} has {equity:.2%} equity vs 2 opponents")
