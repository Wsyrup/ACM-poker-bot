#file to calculate hand equity (preflop, flop, turn, river)
#using monte carlo simulation.

"""
Hand equity calculation module for poker bot decision making.

This module provides functions to estimate the probability that a given hand
will win against opponent hands using Monte Carlo simulation.

It uses the fast hand_eval module for quick hand comparison.
"""

from hand_eval import evaluate_hand, evaluate_best_hand
import random


def estimate_equity_5cards(my_hand, opponent_hands, num_simulations=10000):
    """
    Estimate equity for a 5-card hand.
    
    Args:
        my_hand: List of 5 cards (my hole cards + community)
        opponent_hands: List of opponent hand predictions (each a list of cards)
        num_simulations: Number of Monte Carlo simulations
        
    Returns:
        Float between 0 and 1 representing win probability
    """
    if len(my_hand) != 5:
        raise ValueError("my_hand must be exactly 5 cards")
    
    wins = 0
    ties = 0
    
    my_rank = evaluate_hand(my_hand)
    
    for _ in range(num_simulations):
        # Evaluate each opponent's hand
        best_opponent_rank = float('inf')
        for opp_hand in opponent_hands:
            if len(opp_hand) == 5:
                opp_rank = evaluate_hand(opp_hand)
            best_opponent_rank = min(best_opponent_rank, opp_rank)
        
        if my_rank < best_opponent_rank:
            wins += 1
        elif my_rank == best_opponent_rank:
            ties += 1
    
    # Equity = wins + (ties / num_opponents)
    return (wins + ties / len(opponent_hands)) / num_simulations if opponent_hands else 0


def estimate_equity_7cards(my_cards, opponent_cards, num_simulations=10000):
    """
    Estimate equity from 7 cards (Texas Hold'em).
    
    Args:
        my_cards: List of 7 cards (2 hole + 5 community)
        opponent_cards: List of opponent 7-card hands
        num_simulations: Number of Monte Carlo simulations
        
    Returns:
        Float between 0 and 1 representing win probability
    """
    if len(my_cards) != 7:
        raise ValueError("my_cards must be exactly 7 cards")
    
    wins = 0
    ties = 0
    
    my_best_rank = evaluate_best_hand(my_cards)
    
    for _ in range(num_simulations):
        best_opponent_rank = float('inf')
        for opp_cards in opponent_cards:
            if len(opp_cards) != 7:
                raise ValueError("Each opponent hand must be exactly 7 cards")
            opp_best_rank = evaluate_best_hand(opp_cards)
            best_opponent_rank = min(best_opponent_rank, opp_best_rank)
        
        if my_best_rank < best_opponent_rank:
            wins += 1
        elif my_best_rank == best_opponent_rank:
            ties += 1
    
    return (wins + ties / len(opponent_cards)) / num_simulations if opponent_cards else 0


if __name__ == "__main__":
    # Example usage
    my_hand = ['as', 'ad', 'kh', 'qc', 'jh']
    opp_hand1 = ['ks', 'kd', '9h', '8c', '7h']
    opp_hand2 = ['2s', '3d', '4h', '5c', '6h']
    
    equity = estimate_equity_5cards(my_hand, [opp_hand1, opp_hand2])
    print(f"My hand {my_hand} has {equity:.2%} equity vs 2 opponents")
