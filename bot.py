# <IMPORTS HERE>
from enum import Enum
from equity import equity_calc as ec, hand_eval as he
from equity.hand_eval import preflop_bins
from typing import TypedDict
from opp_eval.opp_eval import OpponentAggressionEstimator
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

class Position(Enum):
    SB = 0
    BB = 1
    BTN = 2
    OTHER = 3

class OpponentBet:
    bet: int
    pot: int
    stack_bb: float
    bet_ratio: float

    def __init__(bet: int, pot: int, stack_bb: float):
        bet = bet
        pot = pot
        stack_bb = stack_bb
        bet_ratio = bet / pot

class OpponentStatMap(TypedDict):
    id: list[OpponentBet]

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

def get_postflop_position(state: GameState) -> Position:
    player_index = state.index_to_action
    num_players = len(state.players)
    sb_index = state.index_of_small_blind
    clockwise_distance: int = 0

    relative_index = player_index - sb_index
    if relative_index < 0: #player behind sb, so add distance
        clockwise_distance = player_index + (num_players - sb_index)
    else:
        clockwise_distance = player_index - sb_index

    if clockwise_distance == num_players:
        return Position.BTN
    elif clockwise_distance <= num_players - 1:
        if clockwise_distance <= num_players - num_players - 1:
            return Position.BB
        elif clockwise_distance == 0:
            return Position.SB
        return Position.OTHER
        
    return Position.OTHER

""" Store any persistent data for your bot in this class """
class Memory:
    """
    Persistent per-game data. We keep:
      - villain_aggro_map: player_id -> OpponentAggressionEstimator instance
      - villain_last_bet: player_id -> last observed bet_money (int)
    """
    def __init__(self):
        # map player id -> OpponentAggressionEstimator
        self.villain_aggro_map: dict[str, OpponentAggressionEstimator] = {}
        # map player id -> last observed bet_money (int)
        self.villain_last_bet: dict[str, int] = {}
        # optional: population-level default aggression to blend during cold-start
        self.population_avg_aggression: float = 0.15


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
        else: #call everything. Don't preflop raise.
            bet = (1.5 + (1.0/preflop_hand)) * min_raise(state) 
            return (bet, memory)

    # any other round: 
    # mvp:
    # based on position in round, info on villains (bet size), calculate villain range
    #villain range is the full array of cards (52), and we select a subarray of length depending on the calculated scalar. 
    # among several hands (select cards, etc...)
    # then estimate equity of hand against them and bet / fold accordingly
    # Even on weak equity, do not fold on the flop unless another bot bets. 
    # with some randomness (i.e. 1/5 of the time we would fold go fishing on the river)
    pos: Position = get_postflop_position(state=state)
    est = OpponentAggressionEstimator()

    #if first after flop, just play on equity. 
    #if not, play off of info given.

    #map villains to aggressive / conservative based off current, past bets
    main_pot_value = state.pots[0].value if state.pots else 1
    big_blind = state.big_blind if state.big_blind > 0 else 1

    # iterate through players (max 6) but only update estimators for players whose bet_money changed
    for i, player_id in enumerate(state.players):
        try:
            curr_bet = int(state.bet_money[i])
        except Exception:
            curr_bet = 0

        last_bet = memory.villain_last_bet.get(player_id, None)

        # create estimator lazily if first time we see this player
        if player_id not in memory.villain_aggro_map:
            memory.villain_aggro_map[player_id] = OpponentAggressionEstimator()

        # If this is the first time we see them, initialize last_bet but do not necessarily treat it as an action
        if last_bet is None:
            memory.villain_last_bet[player_id] = curr_bet
            # Optionally: if curr_bet > 0 consider it an observed action and update estimator:
            if curr_bet > 0:
                bet_ratio = (curr_bet / main_pot_value) if main_pot_value > 0 else 0.0
                stack_bb = (state.held_money[i] / big_blind) if big_blind > 0 else 0.0
                memory.villain_aggro_map[player_id].update(bet_ratio=bet_ratio, stack_bb=stack_bb)
            continue

        # Update only when the bet amount for that player changed since last turn (they acted)
        if curr_bet != last_bet:
            # compute bet_ratio relative to pot (guard division)
            bet_ratio = (curr_bet / main_pot_value) if main_pot_value > 0 else 0.0
            stack_bb = (state.held_money[i] / big_blind) if big_blind > 0 else 0.0

            # update the estimator in-place
            memory.villain_aggro_map[player_id].update(bet_ratio=bet_ratio, stack_bb=stack_bb)

            # store the new last_bet
            memory.villain_last_bet[player_id] = curr_bet
        

    equity = ec.estimate_equity(state.player_cards)
    
        
        
    
    
    
    
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