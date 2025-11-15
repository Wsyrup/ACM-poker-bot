# <IMPORTS HERE>
from enum import Enum
from equity import equity_calc as ec, hand_eval as he
from equity.hand_eval import preflop_bins
# </IMPORTS HERE>

# <DO NOT MODIFY>
from helpers import *

class Pot:
    value: int
    players: list[str]


class GameState:
    index_to_action: int
    index_of_small_blind: int
    players: list[str]
    player_cards: list[str]
    held_money: list[int]
    bet_money: list[int]
    community_cards: list[str]
    pots: list[Pot]
    small_blind: int
    big_blind: int
# </DO NOT MODIFY>

#====================== Preflop =============================== 
#calculate position based on number 
#of players and index of small blind,
#index to action.
class Preflop_Position(Enum): #value given by index from the sb.
    SB = 0
    BB = 1
    UTG = 2
    MP = 3
    CO = 4
    BTN = 5

#always with 6 players
def get_preflop_position(state: GameState) -> Preflop_Position:
    player_index = state.index_to_action
    sb_index = state.index_of_small_blind
    clockwise_distance: int = 0

    relative_index = player_index - sb_index
    if relative_index < 0: #player behind sb, so add distance
        clockwise_distance = player_index + (6 - sb_index)
    else:
        clockwise_distance = player_index - sb_index
        
    return Preflop_Position(clockwise_distance)




""" Store any persistent data for your bot in this class """
class Memory:
    round_number: int
    
    #initialized once per game
    def __init__(self):
        round_number: int = 0

    pass


""" Make a betting decision for the current turn.

    This function is called every time your bot needs to make a bet.

    Args:
        state (GameState): The current state of the game.
        memory (Memory | None): Your bot's memory from the previous turn, or None if this is the first turn.

    Returns:
        tuple[int, Memory | None]: A tuple containing:
            bet_amount: int - The amount you want to bet (-1 to fold, 0 to check, or any positive integer to raise)
            memory: Memory | None - Your bot's updated memory to be passed to the next turn
"""

def bet(state: GameState, memory: Memory | None=None) -> tuple[int, Memory | None]:
    #first round of the game
    if memory is None:
        memory = Memory()

    if (get_round_name == "Pre-Flop"):
        bb: int = state.big_blind
        bet: int = 0

        preflop_hand: preflop_bins

        preflop_hand = preflop_bins(he.bin_preflop_hand(state.player_cards))

        if get_preflop_position(state=state) == Preflop_Position.SB: #play if small blind in first round.
            return (state.small_blind, memory)
        if get_preflop_position(state=state) == Preflop_Position.BB:
            return (bb, memory)

        if preflop_hand > preflop_bins.OneHighSuited:
            return (fold(), memory)
        elif preflop_hand <= preflop_bins.OneHighSuited and preflop_hand > preflop_bins.SuitedAceLow:
            if amount_to_call(state=state) > bb:
                return (fold(), memory)
            return (call(), memory) # limp through
        elif preflop_hand <= preflop_bins.SuitedAceLow and preflop_hand > preflop_bins.BWSuited:
            return (call(), memory) #open to playing
        else:
            bet = (1.5 + (1.0/preflop_hand)) * min_raise(state) 
            return (bet, memory)

    elif (get_round_name(state=state) == "Flop"):
        equity = he._evaluator.evaluate_5cards(state.player_cards + state.community_cards)
        
        
    
    
    
    
    bet_amount = 0
    return (bet_amount, memory)

#bet strategy:
'''
1. calculate hand equity
2. based on equity and pot odds, decide on preflop action
3. then, use existing equity + classification model of opponents to determine postflop actions
4. adjust bet based on risk analysis and opponent classification.
    ^ use this to adjust input ranges on monte carlo sims in equity func.
    (e.g., if opponent is "tight", assume narrower range of hands / lower pot value)

5. implement bluffing strategy based on game dynamics and opponent tendencies.
    e.g., bluff against "tight" players, call "aggressive" players, etc...
6. continuously update opponent models based on observed behavior (throughout the game).


7. refine betting strategy using reinforcement learning techniques over multiple games 
(train analysis biases throughout weekend)?
linear regression / predictive model based on hands, types of opponents in pot
use that to adjust bet sizing and bluff frequency. 

    
'''