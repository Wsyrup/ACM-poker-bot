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

#========================Post-flop==========================
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

RANKS = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']
SUITS = ['s','h','d','c']

def full_deck() -> list[str]:
    """Return full 52-card deck as strings like 'As','Td' (rank+suit)."""
    return [r + s for r in RANKS for s in SUITS]

def _normalize_card_list(cards: list[str]) -> set:
    """Helper to normalize and return set for fast membership checks."""
    return set(cards) if cards else set()

def build_villain_range(scalar: float,
                        hero_hole: list[str],
                        community_cards: list[str],
                        pot_bb: float | None = None,
                        min_cards: int = 2,
                        treat_scalar_as_multiplier: bool = False) -> list[str]:
    """
    Build a villain range list (contiguous subarray of the deck) whose length is determined by:
        length = int(round(10 * scalar))  (or base_len * scalar if treat_scalar_as_multiplier=True)

    Additionally, choose the START index of that contiguous window according to:
      - aggression-like scalar (0..1): low -> conservative, high -> aggressive
      - pot_bb: normalized pot size (higher pot -> stronger shift behavior)

    Args:
        scalar: aggression-like scalar (0..1) OR a multiplier if treat_scalar_as_multiplier True.
        hero_hole: hero's hole cards to remove from the deck
        community_cards: community cards to remove from the deck
        pot_bb: pot size in big blinds (float). If None, we assume small pot (no large shift).
        min_cards: minimum number of cards to include in range (>=2)
        treat_scalar_as_multiplier: if True, treat `scalar` as a multiplier on base_len=10
                                    (useful if you pass a range_multiplier like 0.7..1.6)
    Returns:
        list[str]: contiguous villain_range from the filtered deck
    """
    deck = full_deck()
    removed = _normalize_card_list(hero_hole) | _normalize_card_list(community_cards)
    deck_filtered = [c for c in deck if c not in removed]

    # Determine target length
    if treat_scalar_as_multiplier:
        base_len = 10
        raw_len = int(round(base_len * float(scalar)))
    else:
        raw_len = int(round(10.0 * float(scalar)))

    length = max(min_cards, min(len(deck_filtered), raw_len))

    # If length would consume entire deck, just return deck_filtered
    if length >= len(deck_filtered):
        return list(deck_filtered)

    # Normalize pot_bb into [0,1] (0 => tiny pot, 1 => very large pot)
    if pot_bb is None:
        pot_norm = 0.0
    else:
        # tune these caps to taste: consider pots up to 200 BB as "very large"
        pot_cap = 200.0
        pot_norm = max(0.0, min(1.0, pot_bb / pot_cap))

    # Interpret scalar as aggression in [0,1] when not treat_scalar_as_multiplier.
    # If treat_scalar_as_multiplier, derive an aggression proxy by mapping multiplier to [0,1].
    if treat_scalar_as_multiplier:
        # assume typical multipliers lie in ~[0.5,2.0]; map that to [0,1] with clamping
        mul = float(scalar)
        # choose sensible mapping parameters (tune if needed)
        mul_min, mul_max = 0.5, 2.0
        agg = (mul - mul_min) / (mul_max - mul_min)
        agg = max(0.0, min(1.0, agg))
    else:
        agg = max(0.0, min(1.0, float(scalar)))

    # Compute start fraction (0 => start of deck_filtered; 1 => farthest possible start)
    # Desired behavior:
    #  - If pot small (pot_norm~0) -> start_frac ~ 0 (little shift)
    #  - If pot large (pot_norm~1):
    #       conservative (agg=0) -> start_frac ~ 0.9 (near high cards)
    #       aggressive  (agg=1) -> start_frac ~ 0.5 (middle)
    #
    # We combine these with a simple convex blend:
    conservative_frac = 0.9  # where conservative should point when pot is maxed
    aggressive_frac = 0.5   # where aggressive should point when pot is maxed
    # start_frac ranges [0..1] scaled by pot_norm
    start_frac = pot_norm * ((1.0 - agg) * conservative_frac + agg * aggressive_frac)

    # Convert start_frac to a start index that ensures window fits in deck_filtered
    max_start = len(deck_filtered) - length
    start_index = int(round(start_frac * max_start))
    # clamp
    start_index = max(0, min(max_start, start_index))

    if (start_index + length > len(deck_filtered)):
        return deck_filtered[start_index:]
    else:
        # Return the contiguous window
        villain_range = deck_filtered[start_index : start_index + length]
    return villain_range


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

        # preflop_hand: preflop_bins

        preflop_hand = he.bin_preflop_hand(state.player_cards)

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
    

    players_in_pot = [(i, state.players[i]) for i, m in enumerate(state.bet_money) if m > 0]
    # collect aggressions:

    villain_aggs = {}
    for (i, player) in players_in_pot:
        est = memory.villain_aggro_map.get(player)
        stack_bb = (state.held_money[i] / big_blind) if big_blind > 0 else 0.0
        agg = est.aggression_score(stack_bb)
        villain_aggs[player_id] = agg

    #villain range is the full array of cards (52), and we select 
    #a subarray of length 10 * calculated scalar. 
    
    #remove hero from pot.
    players_in_pot.remove((state.index_to_action, state.players[i]))
    try:
        hero_hole = state.player_cards  # adjust if your hero index differs
    except Exception:
        hero_hole = []

    # collect community cards
    community = state.community_cards if hasattr(state, 'community_cards') else []

    # aggregator: mean aggression among opponents in pot (exclude hero if present)
    agg_values = []
    for (_, pid) in players_in_pot:
        # ensure we don't include hero; if your hero id is a known string, filter it out here.
        if pid in memory.villain_aggro_map:
            # find index for pid to get stack. If not found, default stack
            try:
                idx = state.players.index(pid)
                stack_bb = (state.held_money[idx] / state.big_blind) if state.big_blind > 0 else 0.0
            except ValueError:
                stack_bb = 0.0
            agg_values.append(memory.villain_aggro_map[pid].aggression_score(stack_bb))
    # fallback if no opponents found
    if len(agg_values) == 0:
        avg_agg = 0.15
    else:
        avg_agg = sum(agg_values) / len(agg_values)

    # Build villain_range: treat_scalar_as_multiplier=False assumes avg_agg in [0,1]
    villain_range = build_villain_range(avg_agg, hero_hole, community, min_cards=2, treat_scalar_as_multiplier=False)

    # Choose number of sims (tradeoff speed vs accuracy)
    num_sims = 300  # lower if you need speed; raise for accuracy

    # Call your provided Monte Carlo equity estimator.
    # Note: your estimator expects hero_hole (list[str]), villain_range (list[str]), num_opps (int), community_hand, num_sims
    equity = ec.estimate_equity(hero_hole=hero_hole,
                            villain_range=villain_range,
                            num_opps=max(1, len(players_in_pot)),
                            community_hand=community,
                            num_sims=num_sims)
        
    if equity >= 0.8:
        return (all_in(state=state), memory)
    elif equity >= 0.65:
        if (is_valid_bet(state=state, amount = int(round( (1+equity) * min_raise(state=state))))):
            return (int(round( (1+equity) * min_raise(state=state))), memory)
        elif (is_valid_bet(state=state, amount=amount_to_call)):
            return (call(state=state), memory)
        else:
            return (fold(), memory)
    elif equity >= 0.5:
        if (is_valid_bet(state=state, amount=amount_to_call)):
            return (call(state=state), memory)
        else:
            return (fold(), memory)
    elif equity >= 0.3:
        if (is_valid_bet(state=state, amount=check())):
            return (check(), memory)
        else:
            return (fold(), memory)
    else:
        if (get_round_name(state=state) == "Flop"):
            return (check(), memory)
        return (fold(), memory)

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