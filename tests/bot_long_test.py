# test_long_game.py
"""
Long-game simulator for the poker bot.

Place this file next to your bot.py (the bot source you provided). Then run:
    python test_long_game.py

It will simulate a single long tabletop session (many turns) and print a concise log
and final memory summary to show the bot's behavior and that it doesn't crash in long runs.
"""

import os
import sys
import types
import random
import pprint
import importlib
from types import ModuleType, SimpleNamespace
from datetime import datetime
import csv

# csv init:
log = open("bot_test_log.csv", "w", newline="")
writer = csv.writer(log)
#only store data from rounds where the hero bets. 
writer.writerow([ # gamestate quantities, then hero inputs, then bot inputs, then calculated values
    "game_id", #internal gameid of test
    "game_round", # preflop, flop, turn, river
    "big_blind", #int
    "small_blind", #int
    "turn_num", #int
    "pot_value", #int
    "community_cards", # comma separated list of cards on board
    "hero_hole", # actor (hero or villain) holecards, string input, comma separated ex: "As, Kd"
    "hero_stack_before", # actor held money in big blinds
    "hero_bet_bbs", # actor bet money in big blinds" (-1 fold, 0 check, >0 bet)
    "villain_1_hole", # villain 1 holecards, string input, comma separated ex: "9h, 9d"
    "villain_1_stack_bbs", # villain 1 held money in big blinds
    "villain_1_bet_bbs", # villain 1 bet money in big blinds
    "villain_1_aggro", # villain 1 aggression score from memory
    "villain_2_hole", # villain 2
    "villain_2_stack_bbs",
    "villain_2_bet_bbs",
    "villain_2_aggro",
    "villain_3_hole", # villain 3
    "villain_3_stack_bbs",
    "villain_3_bet_bbs",
    "villain_3_aggro",
    "villain_4_hole", # villain 4
    "villain_4_stack_bbs",
    "villain_4_bet_bbs",
    "villain_4_aggro",
    "villain_5_hole", # villain 5
    "villain_5_stack_bbs",
    "villain_5_bet_bbs",
    "villain_5_aggro",
    "calculated_equity", # calculated equity from equity module, assuming correct calculation
    "villain_actual_range", # villain actual range used in equity calc
    "villain_calculated_range", # villain calculated range used in equity calc
    "hero_scaled_equity",
    "hero_decision", # final bot decision (bet amount)
    "hero_stack_after",
    "reward", # D(stack_after - stack_before)
    "timestamp"
])

pp = pprint.PrettyPrinter(indent=2)

# ------------------------
# 0) Config: change these if you want a different run length
# ------------------------
TOTAL_TURNS = 400          # total turns (acts) to simulate in one long game
NUM_PLAYERS = 6
HERO_NAME = "HERO"
LOG_EVERY = 25             # print a compact snapshot every LOG_EVERY turns
SEED = 2025129           # reproducible seed

# ------------------------
# Imports
# ------------------------
# Add parent directory to path so we can import bot modules
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers import (
    amount_to_call, is_valid_bet, min_raise, call, fold, check, all_in, get_round_name
)

from equity.hand_eval import preflop_bins, bin_preflop_hand
from equity.equity_calc import estimate_equity
from opp_eval.opp_eval import OpponentAggressionEstimator

import bot
# ------------------------
# 5) Utilities: create GameState instance consistent with bot.GameState
# ------------------------
def make_initial_state(num_players=NUM_PLAYERS):
    S = bot.GameState()
    S.index_to_action = 0
    S.index_of_small_blind = 0
    S.players = [f"P{i}" for i in range(num_players)]
    S.player_cards = []            # hero holecards (bot expects this)
    S.held_money = [1000] * num_players
    S.bet_money = [0] * num_players
    S.community_cards = []
    pot = bot.Pot()
    pot.value = 0
    pot.players = S.players.copy()
    S.pots = [pot]
    S.small_blind = 5
    S.big_blind = 10
    S.round_name_override = "Pre-Flop"
    return S

# Note: Old opponent behavior functions removed in favor of simplified random logic in simulate_long_game

# Deal a deck of cards: deal 2 cards to each active player
def deal_hole_cards(players_active, num_players):
    """Deal 2 random hole cards to each active player. Returns dict: player_idx -> [card1, card2]"""
    SUITS = ['s', 'h', 'd', 'c']
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 't', 'j', 'q', 'k', 'a']
    all_cards = [r + s for r in RANKS for s in SUITS]
    
    dealt = {}
    random.shuffle(all_cards)
    card_idx = 0
    
    for idx in range(num_players):
        if idx in players_active:
            dealt[idx] = [all_cards[card_idx], all_cards[card_idx + 1]]
            card_idx += 2
    
    return dealt

def deal_community_cards(dealt_cards_count):
    """Deal community cards (flop = 3, turn = 1, river = 1). Returns list of community cards."""
    SUITS = ['s', 'h', 'd', 'c']
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 't', 'j', 'q', 'k', 'a']
    all_cards = [r + s for r in RANKS for s in SUITS]
    
    random.shuffle(all_cards)
    # Skip cards already dealt to players
    available = all_cards[dealt_cards_count:]
    
    return available[:5]  # Return up to 5 community cards (flop + turn + river)

# Helper to reset betting state for new round (preflop -> flop, etc.)
def reset_round_bets(bet_money):
    """Reset bet_money for the next betting round (players check through without acting again)."""
    return [0] * len(bet_money)

# Helper to determine the winning hand (simplified: assume showdown or last player standing wins)
def determine_hand_winner(players_active, hole_cards_dict):
    """Simplified winner determination: if only 1 player, they win. Otherwise, random selection."""
    active_list = list(players_active)
    if len(active_list) == 1:
        return active_list[0]
    # In a real implementation, you'd evaluate hands using evaluate_best_hand
    return random.choice(active_list)

# Main full-game simulator
def simulate_long_game(seed=SEED):
    """
    Simulate full games of poker until HERO wins all chips or runs out of money.
    
    Rules:
    - 6 players, all start with 7000 chips
    - Initial BB=100, SB=50
    - Blinds double every 25 rounds
    - Dealer (button) rotates each round
    - Continue until HERO wins or busts
    """
    random.seed(seed)
    
    # Initialize game state
    hero_index = 0
    num_players = NUM_PLAYERS
    player_names = []
    for i in range(num_players):
        if i == hero_index:
            player_names.append(HERO_NAME)
        else:
            player_names.append(f"Villain{i}")
    
    # Chip stacks: all start with 7000
    chip_stacks = {i: 7000 for i in range(num_players)}
    
    # Blinds
    bb = 100
    sb = 50
    dealer_idx = 0
    round_num = 0
    
    memory = None
    start_time = datetime.utcnow()
    game_stats = {
        "rounds_played": 0,
        "hero_wins": 0,
        "hero_loses": 0,
        "bot_errors": 0,
        "final_chip_stack": chip_stacks[hero_index]
    }
    
    # Continue playing rounds until HERO wins all chips or goes broke
    while True:
        round_num += 1
        
        # Blind progression: double every 25 rounds
        if round_num % 25 == 0 and round_num > 0:
            sb *= 2
            bb *= 2
            print(f"\n[ROUND {round_num}] BLIND PROGRESSION: SB={sb}, BB={bb}")
        
        # Identify active players (those with chips > 0)
        players_active = set(i for i in range(num_players) if chip_stacks[i] > 0)
        
        # Check end conditions
        if hero_index not in players_active:
            # HERO is out of chips
            print(f"\nHERO BUSTED after {round_num} rounds!")
            game_stats["rounds_played"] = round_num
            game_stats["final_chip_stack"] = 0
            break
        
        # Count active players; if only hero left, hero wins
        if len(players_active) == 1:
            # HERO wins all chips
            total_chips = sum(chip_stacks.values())
            print(f"\nHERO WINS! All opponents eliminated after {round_num} rounds!")
            print(f"Final chip stack: {chip_stacks[hero_index]} out of {total_chips}")
            game_stats["rounds_played"] = round_num
            game_stats["hero_wins"] = 1
            game_stats["final_chip_stack"] = chip_stacks[hero_index]
            break
        
        # Initialize round state
        state = make_initial_state(num_players)
        state.players = player_names
        state.small_blind = sb
        state.big_blind = bb
        state.index_of_small_blind = dealer_idx
        state.index_to_action = (dealer_idx + 2) % num_players  # UTG (after BB)
        
        # Deal hole cards
        hole_cards_dict = deal_hole_cards(players_active, num_players)
        if hero_index in hole_cards_dict:
            state.player_cards = hole_cards_dict[hero_index]
        else:
            state.player_cards = []
        
        # Initialize betting state
        state.bet_money = [0] * num_players
        state.held_money = [chip_stacks[i] for i in range(num_players)]
        
        # Post small blind and big blind
        sb_idx = dealer_idx
        bb_idx = (dealer_idx + 1) % num_players
        
        if sb_idx in players_active and chip_stacks[sb_idx] > 0:
            sb_amt = min(sb, chip_stacks[sb_idx])
            state.bet_money[sb_idx] = sb_amt
            chip_stacks[sb_idx] -= sb_amt
        
        if bb_idx in players_active and chip_stacks[bb_idx] > 0:
            bb_amt = min(bb, chip_stacks[bb_idx])
            state.bet_money[bb_idx] = bb_amt
            chip_stacks[bb_idx] -= bb_amt
        
        # Initialize pot
        pot = bot.Pot()
        pot.value = state.bet_money[sb_idx] + state.bet_money[bb_idx]
        pot.players = list(players_active)
        state.pots = [pot]
        
        state.round_name_override = "Pre-Flop"
        
        # Simulate preflop action
        print(f"\n=== ROUND {round_num} ===")
        print(f"Dealer: {player_names[dealer_idx]}, SB: {sb}, BB: {bb}")
        print(f"HERO hole cards: {state.player_cards}")
        print(f"Chip stacks: {[(player_names[i], chip_stacks[i]) for i in range(num_players)]}")
        
        # Simple preflop action loop (for now, simplified; in full version would iterate betting rounds)
        action_count = 0
        max_actions = 100  # Prevent infinite loop
        
        while action_count < max_actions:
            pid_idx = state.index_to_action % num_players
            
            # Skip inactive players
            if pid_idx not in players_active or chip_stacks[pid_idx] <= 0:
                state.index_to_action = (state.index_to_action + 1) % num_players
                action_count += 1
                continue
            
            pid = player_names[pid_idx]
            
            # HERO acts
            if pid == HERO_NAME:
                try:
                    bet_amt, memory = bot.bet(state=state, memory=memory)
                except Exception as e:
                    game_stats["bot_errors"] += 1
                    print(f"[ROUND {round_num}] Bot error: {e!r}")
                    bet_amt = -1  # Fold on error
                
                # Apply bet
                if bet_amt < 0:
                    # Fold
                    players_active.discard(hero_index)
                    print(f"HERO folds")
                    break
                elif bet_amt == 0:
                    # Check/call
                    print(f"HERO checks/calls")
                else:
                    # Bet/raise
                    amt = min(bet_amt, chip_stacks[pid_idx])
                    state.bet_money[pid_idx] += amt
                    chip_stacks[pid_idx] -= amt
                    state.pots[0].value += amt
                    print(f"HERO bets {amt}")
            else:
                # Opponent acts
                action = random.choices(["fold", "check/call", "raise"], 
                                      weights=[0.1, 0.6, 0.3])[0]
                if action == "fold":
                    players_active.discard(pid_idx)
                    print(f"{pid} folds")
                elif action == "raise":
                    amt = min(bb, chip_stacks[pid_idx])
                    state.bet_money[pid_idx] += amt
                    chip_stacks[pid_idx] -= amt
                    state.pots[0].value += amt
                    print(f"{pid} raises {amt}")
                else:
                    print(f"{pid} checks/calls")
            
            # Check if only one player left
            if len(players_active) == 1:
                break
            
            state.index_to_action = (state.index_to_action + 1) % num_players
            action_count += 1
        
        # Determine winner and distribute pot
        winner_idx = determine_hand_winner(players_active, hole_cards_dict)
        chip_stacks[winner_idx] += state.pots[0].value
        print(f"\n{player_names[winner_idx]} wins pot of {state.pots[0].value}")
        
        # Rotate dealer
        dealer_idx = (dealer_idx + 1) % num_players
        game_stats["rounds_played"] = round_num
        
        # Periodic status
        if round_num % LOG_EVERY == 0:
            print(f"[Status at round {round_num}] HERO stack: {chip_stacks[hero_index]}")
    
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    
    # Final summary
    print("\n=== GAME COMPLETE ===")
    print(f"Rounds played: {game_stats['rounds_played']}")
    print(f"Elapsed time: {elapsed:.2f}s")
    print(f"HERO final stack: {chip_stacks[hero_index]}")
    print(f"Bot errors: {game_stats['bot_errors']}")
    if memory:
        print("Memory summary (villain tracking enabled)")
    
    return {
        "rounds": game_stats["rounds_played"],
        "elapsed": elapsed,
        "hero_won": game_stats["hero_wins"] == 1,
        "final_stack": chip_stacks[hero_index],
        "memory": memory,
        "stats": game_stats
    }

# small wrappers to call helpers functions inside this harness (helpers in sys.modules)
def amount_to_call_wrapper(state):
    return amount_to_call(state)

def all_in_wrapper(state):
    return all_in(state)

# Removed old behavior functions; new simulator uses simple random opponent logic


# ------------------------
# Main entry point
# ------------------------
if __name__ == "__main__":
    print(f"Starting full poker game simulation. Seed = {SEED}")
    print(f"6 players, starting stack = 7000 chips")
    print(f"Initial BB = 100, SB = 50 (doubles every 25 rounds)")
    print("-" * 70)
    
    res = simulate_long_game(seed=SEED)
    
    print("\n" + "=" * 70)
    print("GAME RESULTS:")
    print(f"  Rounds played: {res['rounds']}")
    print(f"  Elapsed time: {res['elapsed']:.2f}s")
    print(f"  HERO won: {res['hero_won']}")
    print(f"  Final stack: {res['final_stack']} chips")
    print("=" * 70)
