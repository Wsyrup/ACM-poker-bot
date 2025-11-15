# test_long_game.py
"""
Long-game simulator for the poker bot.

Place this file next to your bot.py (the bot source you provided). Then run:
    python test_long_game.py

It will simulate a single long tabletop session (many turns) and print a concise log
and final memory summary to show the bot's behavior and that it doesn't crash in long runs.
"""

import sys
import types
import random
import pprint
import importlib
from types import ModuleType, SimpleNamespace
from datetime import datetime

pp = pprint.PrettyPrinter(indent=2)

# ------------------------
# 0) Config: change these if you want a different run length
# ------------------------
TOTAL_TURNS = 400          # total turns (acts) to simulate in one long game
NUM_PLAYERS = 6
HERO_NAME = "HERO"
LOG_EVERY = 25             # print a compact snapshot every LOG_EVERY turns
SEED = 20251114            # reproducible seed

# ------------------------
# 1) Minimal helpers module expected by bot
# ------------------------
helpers = ModuleType("helpers")

def amount_to_call(state=None):
    if state is None: return 0
    max_bet = max(state.bet_money) if state.bet_money else 0
    hero_bet = state.bet_money[state.index_to_action] if state.bet_money else 0
    return max(0, max_bet - hero_bet)

def is_valid_bet(state=None, amount=0):
    if state is None: return True
    idx = state.index_to_action
    # allow check/call/fold/all-in; simply ensure not exceeding stack + current bet
    return amount <= (state.held_money[idx] + state.bet_money[idx])

def min_raise(state=None):
    if state is None: return 10
    return max(1, state.big_blind)

def call(state=None):
    return int(amount_to_call(state))

def fold():
    return -1

def check():
    return 0

def all_in(state=None):
    if state is None: return 9999
    idx = state.index_to_action
    return state.held_money[idx] + state.bet_money[idx]

# get_round_name helper that supports both "get_round_name == 'Pre-Flop'" style and callable
class RoundName:
    def __init__(self, initial="Pre-Flop"):
        self.name = initial
    def __call__(self, state=None):
        if state and hasattr(state, "round_name_override"):
            return state.round_name_override
        return self.name
    def __eq__(self, other):
        return str(self.name) == str(other)

helpers.amount_to_call = amount_to_call
helpers.is_valid_bet = is_valid_bet
helpers.min_raise = min_raise
helpers.call = call
helpers.fold = fold
helpers.check = check
helpers.all_in = all_in
helpers.get_round_name = RoundName("Pre-Flop")

# register in sys.modules so bot can import
sys.modules["helpers"] = helpers

# ------------------------
# 2) Minimal equity.hand_eval and equity.equity_calc stubs
# ------------------------
equity_hand_eval = ModuleType("equity.hand_eval")
class PreflopBins:
    OneHighSuited = 8
    SuitedAceLow = 5
    BWSuited = 2

def bin_preflop_hand(player_cards):
    # heuristic: A or pair => stronger (smaller numeric), else weaker
    if not player_cards or len(player_cards) < 2: return 10
    ranks = [c[0] for c in player_cards]
    if 'A' in ranks:
        return 4
    if ranks[0] == ranks[1]:
        return 3
    return 9

equity_hand_eval.preflop_bins = PreflopBins
equity_hand_eval.bin_preflop_hand = bin_preflop_hand
sys.modules["equity.hand_eval"] = equity_hand_eval

equity_ec = ModuleType("equity.equity_calc")
def estimate_equity(hero_hole, villain_range, num_opps, community_hand, num_sims):
    """
    Simple deterministic-ish equity proxy:
      - hero with Ace gets strong base
      - pocket pair gets decent base
      - fewer opponents increases equity
      - add tiny noise to avoid exact ties
    """
    base = 0.12
    if hero_hole and len(hero_hole) >= 2:
        ranks = [c[0] for c in hero_hole]
        if 'A' in ranks:
            base += 0.45
        elif ranks[0] == ranks[1]:
            base += 0.25
        elif ranks[0] in "TJQK":
            base += 0.18
        else:
            base += 0.06
    # fewer opponents -> slightly higher equity
    base += max(0.0, 0.15 * (1.0 - min(1.0, num_opps / 4.0)))
    # add small random noise
    return max(0.0, min(1.0, base + (random.random() - 0.5) * 0.04))

equity_ec.estimate_equity = estimate_equity
sys.modules["equity.equity_calc"] = equity_ec

# ------------------------
# 3) Minimal opp_eval.opp_eval stub
# ------------------------
opp_eval = ModuleType("opp_eval.opp_eval")
class OpponentAggressionEstimator:
    def __init__(self):
        self.history = []
    def update(self, bet_ratio=0.0, stack_bb=0.0):
        self.history.append((float(bet_ratio), float(stack_bb)))
    def aggression_score(self, stack_bb):
        if not self.history:
            return 0.15
        avg = sum(b for b, s in self.history) / len(self.history)
        return float(max(0.0, min(1.0, avg)))
opp_eval.OpponentAggressionEstimator = OpponentAggressionEstimator
sys.modules["opp_eval.opp_eval"] = opp_eval

# ------------------------
# 4) Import the bot module (user must have their bot code saved as bot.py)
# ------------------------
try:
    bot = importlib.import_module("bot")
except Exception as exc:
    print("Failed to import 'bot'. Make sure your bot code is saved as 'bot.py' in this folder.")
    raise

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
    pot = SimpleNamespace()
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
