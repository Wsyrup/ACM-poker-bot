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

# ------------------------
# 6) Opponent behaviors - mixed table
# ------------------------
def aggressive_opponent_action(state, idx):
    # large raise (bounded by their stack)
    stack = state.held_money[idx]
    if stack <= 0:
        return ("allin", 0)
    raise_amt = min(stack, state.big_blind * (2 + random.randint(0, 4)))
    state.bet_money[idx] += raise_amt
    state.held_money[idx] -= raise_amt
    state.pots[0].value += raise_amt
    return ("raise", raise_amt)

def passive_opponent_action(state, idx):
    to_call = max(state.bet_money) - state.bet_money[idx]
    if to_call <= 0:
        return ("check", 0)
    amt = min(to_call, state.held_money[idx])
    state.bet_money[idx] += amt
    state.held_money[idx] -= amt
    state.pots[0].value += amt
    return ("call", amt)

def random_opponent_action(state, idx):
    choice = random.choices(["fold", "check", "call", "raise"], weights=[0.1, 0.3, 0.45, 0.15])[0]
    if choice == "fold":
        # represent fold by removing from players in pot list
        state.pots[0].players = [p for p in state.pots[0].players if p != state.players[idx]]
        return ("fold", 0)
    if choice == "check":
        return ("check", 0)
    if choice == "call":
        return passive_opponent_action(state, idx)
    return aggressive_opponent_action(state, idx)

# create mixed behavior table assignment
# e.g., players: [HERO, Aggressive, Passive, Random, Aggressive, Passive]
def make_behavior_list(num_players=NUM_PLAYERS, hero_pos=0):
    names = []
    for i in range(num_players):
        if i == hero_pos:
            names.append(HERO_NAME)
            continue
        # assign patterns: cycle Agg, Pass, Rand
        cycle = (i % 3)
        if cycle == 0:
            names.append("AGG")
        elif cycle == 1:
            names.append("PAS")
        else:
            names.append("RND")
    return names

BEHAVIOR_FUN = {
    "AGG": aggressive_opponent_action,
    "PAS": passive_opponent_action,
    "RND": random_opponent_action
}

# ------------------------
# 7) Long game simulation loop
# ------------------------
def simulate_long_game(total_turns=TOTAL_TURNS, seed=SEED):
    random.seed(seed)
    state = make_initial_state(NUM_PLAYERS)
    # place hero at index 0
    hero_index = 0
    players = make_behavior_list(NUM_PLAYERS, hero_pos=hero_index)
    # ensure unique names for others
    final_players = []
    idx_map = 0
    for p in players:
        if p == HERO_NAME:
            final_players.append(HERO_NAME)
        else:
            # unique label
            final_players.append(f"{p}{idx_map}")
            idx_map += 1
    state.players = final_players
    # hero holecards (kept constant for simplicity)
    state.player_cards = ["As", "Kh"]
    state.bet_money = [0] * NUM_PLAYERS
    state.held_money = [1000] * NUM_PLAYERS
    # reduce a couple of opponents stacks to create variety
    state.held_money[2] = 600
    state.held_money[4] = 300
    state.big_blind = 10
    state.small_blind = 5
    state.pots = [SimpleNamespace(value=0, players=state.players.copy())]

    memory = None
    last_exception = None
    start_time = datetime.utcnow()

    # track simple stats
    bot_actions = {"fold":0, "check":0, "call":0, "bet/raise":0, "allin":0, "errors":0}
    opponent_actions_count = 0

    for turn in range(total_turns):
        pid_idx = state.index_to_action % len(state.players)
        pid = state.players[pid_idx]
        # occasionally rotate small blind so preflop position changes
        if turn % 50 == 0 and turn > 0:
            state.index_of_small_blind = (state.index_of_small_blind + 1) % len(state.players)

        # occasionally advance round name to simulate postflop phases
        if turn % 40 == 0 and turn > 0:
            # cycle through Pre-Flop -> Flop -> Turn -> River -> Pre-Flop
            cycle = (turn // 40) % 5
            if cycle == 0:
                state.round_name_override = "Pre-Flop"
            elif cycle == 1:
                state.round_name_override = "Flop"
            elif cycle == 2:
                state.round_name_override = "Turn"
            elif cycle == 3:
                state.round_name_override = "River"
            else:
                state.round_name_override = "Showdown"

        # Hero acts
        if pid == HERO_NAME:
            try:
                bet_amt, memory = bot.bet(state=state, memory=memory)
            except Exception as e:
                last_exception = e
                bot_actions["errors"] += 1
                print(f"[TURN {turn}] Bot raised exception: {e!r}")
                # don't crash; continue but note the error
                bet_amt = -9999

            # interpret bot response
            if isinstance(bet_amt, int):
                if bet_amt < 0:
                    # fold
                    bot_actions["fold"] += 1
                    state.pots[0].players = [p for p in state.pots[0].players if p != HERO_NAME]
                elif bet_amt == 0:
                    bot_actions["check"] += 1
                elif bet_amt >= all_in_wrapper(state):
                    bot_actions["allin"] += 1
                    # apply all-in
                    idx = pid_idx
                    amount = min(state.held_money[idx], bet_amt)
                    state.bet_money[idx] += amount
                    state.held_money[idx] -= amount
                    state.pots[0].value += amount
                else:
                    # numeric bet (call/raise)
                    if bet_amt == amount_to_call_wrapper(state):
                        bot_actions["call"] += 1
                    else:
                        bot_actions["bet/raise"] += 1
                    idx = pid_idx
                    amount = min(state.held_money[idx], bet_amt)
                    state.bet_money[idx] += amount
                    state.held_money[idx] -= amount
                    state.pots[0].value += amount
            else:
                bot_actions["errors"] += 1

        else:
            # find behavior type by name prefix
            # behavior name is like 'AGG0','PAS1','RND2'
            btype = pid[:3]
            func = BEHAVIOR_FUN.get(btype, random_opponent_action)
            action, amt = func(state, pid_idx)
            opponent_actions_count += 1

        # advance the action pointer
        state.index_to_action = (state.index_to_action + 1) % len(state.players)

        # periodic compact log
        if (turn + 1) % LOG_EVERY == 0 or turn < 10:
            snapshot = {
                "turn": turn + 1,
                "round": helpers.get_round_name(state),
                "index_to_action": state.index_to_action,
                "pot": state.pots[0].value,
                "bet_money_snapshot": state.bet_money[:],
                "held_money_snapshot": state.held_money[:],
                "players_in_pot": state.pots[0].players[:]
            }
            print(f"[{datetime.utcnow().isoformat()}] Snapshot at turn {turn+1}:")
            pp.pprint(snapshot)

    elapsed = (datetime.utcnow() - start_time).total_seconds()

    # Final summary
    print("\n=== LONG GAME SUMMARY ===")
    print(f"Total turns simulated: {total_turns}")
    print(f"Elapsed time (wall): {elapsed:.2f}s")
    print("Bot action counts:", bot_actions)
    print("Opponent actions processed:", opponent_actions_count)
    # memory inspection
    if memory is None:
        print("Bot returned no memory (memory is None).")
    else:
        print("Memory summary (villain_aggro_map keys and sizes):")
        try:
            keys = list(memory.villain_aggro_map.keys())
            print("Tracked opponents:", keys)
            for k in keys:
                est = memory.villain_aggro_map[k]
                hist_len = len(est.history) if hasattr(est, "history") else "unknown"
                print(f" - {k}: history_len={hist_len}")
        except Exception as e:
            print("Error inspecting memory:", e)
    if last_exception:
        print("\nNOTE: Last exception encountered from bot during run:")
        print(repr(last_exception))
    print("\nFinal pot value:", state.pots[0].value)
    print("Players still listed in pot:", state.pots[0].players)
    print("Final bet_money:", state.bet_money)
    print("Final held_money:", state.held_money)
    return {
        "turns": total_turns,
        "elapsed": elapsed,
        "bot_actions": bot_actions,
        "memory": memory,
        "last_exception": last_exception,
        "final_state": state
    }

# small wrappers to call helpers functions inside this harness (helpers in sys.modules)
def amount_to_call_wrapper(state):
    return helpers.amount_to_call(state)

def all_in_wrapper(state):
    return helpers.all_in(state)

# ------------------------
# 8) Run it
# ------------------------
if __name__ == "__main__":
    print("Starting long-game simulation. Seed =", SEED)
    res = simulate_long_game()
    print("\nDone. If the run completed without crashing and memory shows tracked opponents, that's proof the bot handles a long session.")
