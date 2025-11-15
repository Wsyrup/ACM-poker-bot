# test_bot.py
"""
Test harness for the poker bot.
Place this file next to your bot.py file and run `python test_bot.py`.

This harness:
 - injects stub modules (helpers, equity, opp_eval) before importing bot.py
 - runs 3 short simulated games (aggressive opponents, passive opponents, random opponents)
 - prints the hero (bot) decisions and state snapshots for inspection
"""

import sys
import types
import random
import pprint
from types import ModuleType

# ------------------------
# 1) Create stub 'helpers' module used by the bot
# ------------------------
helpers = ModuleType("helpers")
# Basic helper functions the bot expects. Minimal semantics to let bot run.
def amount_to_call(state=None):
    # simple calculation: highest bet among players - hero's bet
    if state is None:
        return 0
    max_bet = max(state.bet_money) if state.bet_money else 0
    hero_bet = state.bet_money[state.index_to_action] if state.bet_money else 0
    return max(0, max_bet - hero_bet)

def is_valid_bet(state=None, amount=0):
    # allow bets up to hero's held money + current bet
    if state is None:
        return True
    idx = state.index_to_action
    return amount <= (state.held_money[idx] + state.bet_money[idx])

def min_raise(state=None):
    # minimal raise: big blind or 2 * big blind
    if state is None:
        return 10
    return max(state.big_blind, 2 * state.big_blind)

def call(state=None):
    # return a symbolic value to indicate call; bot sometimes uses as amount
    return int(amount_to_call(state))

def fold():
    return -1

def check():
    return 0

def all_in(state=None):
    if state is None:
        return 9999
    idx = state.index_to_action
    return state.held_money[idx] + state.bet_money[idx]

# A special object for get_round_name so comparisons like (get_round_name == "Pre-Flop")
# evaluate properly AND so it is callable later as get_round_name(state=state).
class RoundName:
    def __init__(self, initial="Pre-Flop"):
        self.name = initial
    def __call__(self, state=None):
        # If state carries an attribute 'round_name_override', return that.
        if state and hasattr(state, "round_name_override"):
            return state.round_name_override
        return self.name
    def __eq__(self, other):
        return str(self.name) == str(other)

# attach to helpers module
helpers.amount_to_call = amount_to_call
helpers.is_valid_bet = is_valid_bet
helpers.min_raise = min_raise
helpers.call = call
helpers.fold = fold
helpers.check = check
helpers.all_in = all_in
helpers.get_round_name = RoundName("Pre-Flop")

# push into sys.modules BEFORE bot is imported
sys.modules["helpers"] = helpers

# ------------------------
# 2) Create stub equity.* modules
# ------------------------
# equity.hand_eval stub: bin_preflop_hand and preflop_bins
equity_hand_eval = ModuleType("equity.hand_eval")
# make a very small preflop_bins type that supports comparisons used by bot
class PreflopBins:
    # mimic numeric ordering with named attributes
    # smaller number == stronger hand in the bot's code? (we don't rely on exact meaning)
    OneHighSuited = 8
    SuitedAceLow = 5
    BWSuited = 2

def bin_preflop_hand(player_cards):
    # naive mapping: if hero has an Ace return low numeric; else return higher numeric
    if not player_cards or len(player_cards) < 2:
        return 10
    ranks = [c[0] for c in player_cards]
    if 'A' in ranks:
        return 4
    if ranks[0] == ranks[1]:
        return 3
    return 9

equity_hand_eval.preflop_bins = PreflopBins
equity_hand_eval.bin_preflop_hand = bin_preflop_hand
sys.modules["equity.hand_eval"] = equity_hand_eval

# equity.equity_calc stub: provide estimate_equity
equity_ec = ModuleType("equity.equity_calc")
def estimate_equity(hero_hole, villain_range, num_opps, community_hand, num_sims):
    # simple deterministic-ish function:
    # - if hero has an Ace -> higher equity
    # - increase with fewer opponents
    base = 0.15
    if hero_hole:
        ranks = [c[0] for c in hero_hole]
        if 'A' in ranks:
            base += 0.4
        elif ranks[0] == ranks[1]:
            base += 0.25
    base += 0.1 * max(0, (1.0 - min(1.0, num_opps/3.0)))
    # clamp 0..1
    return max(0.0, min(1.0, base + (random.random() * 0.05)))
equity_ec.estimate_equity = estimate_equity
sys.modules["equity.equity_calc"] = equity_ec

# ------------------------
# 3) Create stub opp_eval.opp_eval
# ------------------------
opp_eval = ModuleType("opp_eval.opp_eval")
class OpponentAggressionEstimator:
    def __init__(self):
        self.history = []
    def update(self, bet_ratio=0.0, stack_bb=0.0):
        self.history.append((float(bet_ratio), float(stack_bb)))
    def aggression_score(self, stack_bb):
        if not self.history:
            return 0.15  # population default
        # return average bet_ratio (simple)
        avg = sum(b for b, s in self.history) / len(self.history)
        return float(avg)
opp_eval.OpponentAggressionEstimator = OpponentAggressionEstimator
sys.modules["opp_eval.opp_eval"] = opp_eval

# ------------------------
# 4) Now import the bot module (assumed to be named bot.py)
# ------------------------
# Replace 'bot' with the actual filename (without .py) if different.
import importlib

try:
    bot = importlib.import_module("bot")
except Exception as e:
    print("Error importing bot.py. Ensure bot.py is in the same directory as this test file.")
    raise

# For pretty printing game state
pp = pprint.PrettyPrinter(indent=2)

# ------------------------
# 5) Helper to make a GameState instance and initialize fields
# ------------------------
def make_empty_state(num_players=6):
    S = bot.GameState()
    S.index_to_action = 0
    S.index_of_small_blind = 0
    S.players = [f"P{i}" for i in range(num_players)]
    S.player_cards = []  # hero holecards (bot expects this)
    S.held_money = [1000 for _ in range(num_players)]
    S.bet_money = [0 for _ in range(num_players)]
    S.community_cards = []
    class Pot: pass
    p = Pot(); p.value = 0; p.players = S.players.copy()
    S.pots = [p]
    S.small_blind = 5
    S.big_blind = 10
    # optional override
    S.round_name_override = "Pre-Flop"
    return S

# ------------------------
# 6) Opponent behavior implementations
# ------------------------
def aggressive_opponent_action(state, idx):
    # raise aggressively: set bet_money to a sizable multiple of big blind
    raise_amt = state.big_blind * (2 + random.randint(0,3))
    state.bet_money[idx] = state.bet_money[idx] + raise_amt
    # reduce their held money
    state.held_money[idx] = max(0, state.held_money[idx] - raise_amt)
    # update main pot
    state.pots[0].value += raise_amt
    return ("raise", raise_amt)

def passive_opponent_action(state, idx):
    # call or check: match current max or check
    to_call = max(state.bet_money) - state.bet_money[idx]
    if to_call > 0:
        amt = to_call
        state.bet_money[idx] += amt
        state.held_money[idx] = max(0, state.held_money[idx] - amt)
        state.pots[0].value += amt
        return ("call", amt)
    else:
        return ("check", 0)

def random_opponent_action(state, idx):
    choice = random.choice(["fold", "call", "raise", "check"])
    if choice == "fold":
        # represent fold by setting bet_money to 0 and removing them from pot players
        state.bet_money[idx] = 0
        state.pots[0].players = [p for p in state.pots[0].players if p != state.players[idx]]
        return ("fold", 0)
    elif choice == "call":
        return passive_opponent_action(state, idx)
    elif choice == "raise":
        return aggressive_opponent_action(state, idx)
    else:
        return ("check", 0)

# Map behavior name -> function
BEHAVIORS = {
    "aggressive": aggressive_opponent_action,
    "passive": passive_opponent_action,
    "random": random_opponent_action
}

# ------------------------
# 7) Simulate a short game
# ------------------------
def simulate_game(opponent_type="aggressive", hero_index=0, hero_holecards=None, rounds=6, seed=42):
    random.seed(seed)
    state = make_empty_state(num_players=6)
    state.index_of_small_blind = 0
    state.index_to_action = 0
    # Place hero at hero_index
    # rotate players names so hero is P0 in bot indexing and test harness aligns
    players = [f"P{i}" for i in range(6)]
    # ensure hero occupies the requested hero_index
    # We'll set hero to "Hero" id to be clear in logs
    players[hero_index] = "HERO"
    # ensure unique names
    j = 0
    for i in range(6):
        if players[i] == f"P{i}":
            # assign next P tag that isn't used
            while f"P{j}" in players:
                j += 1
            players[i] = f"P{j}"
    state.players = players
    # hero cards
    if hero_holecards is None:
        # give hero a moderately good hand (As Kh)
        hero_holecards = ["As", "Kh"]
    state.player_cards = hero_holecards
    # initialize pot, bets
    state.bet_money = [0 for _ in range(6)]
    state.held_money = [1000 for _ in range(6)]
    # adjust hero held money slightly
    hero_idx = state.players.index("HERO")
    state.held_money[hero_idx] = 1000
    state.big_blind = 10
    state.small_blind = 5
    state.pots = []
    P = types.SimpleNamespace()
    P.value = 0
    P.players = state.players.copy()
    state.pots.append(P)

    # choose behavior function for opponents
    behavior = BEHAVIORS.get(opponent_type, random_opponent_action)

    print("\n--- Simulating game: opponents =", opponent_type, " hero at index =", hero_idx, " ---")
    memory = None

    # play 'rounds' simple turns rotating index_to_action
    for t in range(rounds):
        acting_idx = state.index_to_action % len(state.players)
        pid = state.players[acting_idx]
        print(f"\nTurn {t+1} - action index {acting_idx} ({pid}) - round_name={helpers.get_round_name(state)}")
        # if it's the hero, call the bot
        if pid == "HERO":
            try:
                bet_amt, memory = bot.bet(state=state, memory=memory)
            except Exception as e:
                print("Bot.bet raised exception:", e)
                bet_amt, memory = ("ERROR", memory)
            print(f"BOT decision: {bet_amt}")
            # If bot places numeric bet, apply to state (simple)
            if isinstance(bet_amt, int) and bet_amt > 0:
                # move amount from hero held_money into bet_money and pot
                state.bet_money[acting_idx] += bet_amt
                state.held_money[acting_idx] = max(0, state.held_money[acting_idx] - bet_amt)
                state.pots[0].value += bet_amt
            elif isinstance(bet_amt, int) and bet_amt == 0:
                # check - do nothing
                pass
            elif isinstance(bet_amt, int) and bet_amt < 0:
                # fold - remove from pot players list
                state.pots[0].players = [p for p in state.pots[0].players if p != pid]
        else:
            # opponent acts according to behavior
            action, amt = behavior(state, acting_idx)
            print(f"Opponent {pid} -> {action} {amt}")

        # advance action
        state.index_to_action = (state.index_to_action + 1) % len(state.players)

        # occasionally advance round name to exercise postflop logic
        if t == 1:
            state.round_name_override = "Flop"
        if t == 3:
            state.round_name_override = "Turn"
        if t == 4:
            state.round_name_override = "River"

        # print brief state snapshot
        print("State snapshot:")
        sshot = {
            "players": state.players,
            "index_to_action": state.index_to_action,
            "bet_money": state.bet_money,
            "held_money": state.held_money,
            "pot_value": state.pots[0].value,
            "pots_players": state.pots[0].players,
            "round": helpers.get_round_name(state)
        }
        pp.pprint(sshot)

    print("\nFinal memory (for HERO):")
    pp.pprint(memory.villain_aggro_map if memory else None)
    return memory

# ------------------------
# 8) Run three test games
# ------------------------
if __name__ == "__main__":
    random.seed(123)
    # 1) Hero vs 5 aggressive opponents
    simulate_game(opponent_type="aggressive", hero_index=0, rounds=6, seed=10)

    # 2) Hero vs 5 passive opponents
    simulate_game(opponent_type="passive", hero_index=2, rounds=6, seed=20)

    # 3) Hero vs random opponents
    simulate_game(opponent_type="random", hero_index=3, rounds=8, seed=30)

    print("\nDone. Inspect output above to review bot decisions and memory updates.")
