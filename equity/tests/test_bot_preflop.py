#!/usr/bin/env python3
"""
Preflop decision architecture tests for bot.py

Tests the preflop betting logic, position calculation, and hand classification.
Covers position detection, hand binning, and preflop action selection.

Run via: python equity/tests/test_bot_preflop.py
"""

import os
import sys

# Add parent directories to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hand_eval import preflop_bins, bin_preflop_hand
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from bot import Preflop_Position, get_preflop_position, GameState, Memory, bet


class MockGameState(GameState):
    """Mock GameState for testing without full game engine."""
    def __init__(self, index_to_action=0, sb_index=0, player_cards=None, 
                 community_cards=None, small_blind=1, big_blind=2, 
                 held_money=None, bet_money=None, players=None):
        self.index_to_action = index_to_action
        self.index_of_small_blind = sb_index
        self.player_cards = player_cards or []
        self.community_cards = community_cards or []
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.held_money = held_money or [1000] * 6
        self.bet_money = bet_money or [0] * 6
        self.players = players or [f"Player{i}" for i in range(6)]
        self.pots = []


def test_position_small_blind():
    """Test position detection for small blind."""
    print("=" * 70)
    print("Test 1: Position detection - Small Blind (SB)")
    print("=" * 70)
    
    state = MockGameState(index_to_action=0, sb_index=0)
    pos = get_preflop_position(state)
    
    print(f"  Player at index 0, SB at index 0 -> position = {pos.name}")
    passed = pos == Preflop_Position.SB
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_position_big_blind():
    """Test position detection for big blind."""
    print("=" * 70)
    print("Test 2: Position detection - Big Blind (BB)")
    print("=" * 70)
    
    state = MockGameState(index_to_action=1, sb_index=0)
    pos = get_preflop_position(state)
    
    print(f"  Player at index 1, SB at index 0 -> position = {pos.name}")
    passed = pos == Preflop_Position.BB
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_position_utg():
    """Test position detection for Under The Gun."""
    print("=" * 70)
    print("Test 3: Position detection - Under The Gun (UTG)")
    print("=" * 70)
    
    state = MockGameState(index_to_action=2, sb_index=0)
    pos = get_preflop_position(state)
    
    print(f"  Player at index 2, SB at index 0 -> position = {pos.name}")
    passed = pos == Preflop_Position.UTG
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_position_button():
    """Test position detection for button."""
    print("=" * 70)
    print("Test 4: Position detection - Button (BTN)")
    print("=" * 70)
    
    state = MockGameState(index_to_action=5, sb_index=0)
    pos = get_preflop_position(state)
    
    print(f"  Player at index 5, SB at index 0 -> position = {pos.name}")
    passed = pos == Preflop_Position.BTN
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_position_with_offset_sb():
    """Test position detection when SB is not at index 0."""
    print("=" * 70)
    print("Test 5: Position detection with offset Small Blind")
    print("=" * 70)
    
    state = MockGameState(index_to_action=3, sb_index=2)
    pos = get_preflop_position(state)
    
    relative_distance = abs(3 - 2)
    print(f"  Player at index 3, SB at index 2 -> relative distance = {relative_distance}")
    print(f"  Position = {pos.name}")
    passed = pos == Preflop_Position.BB  # 3 - 2 = 1 = BB
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed

def test_position_with_hero_before_sb():
    """Test position detection when SB is not at index 0."""
    print("=" * 70)
    print("Test 6: Position detection with offset Small Blind")
    print("=" * 70)
    
    state = MockGameState(index_to_action=1, sb_index=3)
    pos = get_preflop_position(state)
    
    relative_distance = 1 + (6-3)
    print(f"  SB at index 3, player at index 1 -> clockwise distance = {relative_distance}")
    print(f"  Position = {pos.name}")
    passed = pos == Preflop_Position.CO  # 3 - 2 = 1 = BB
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed

def test_hand_bin_premium_pair():
    """Test hand binning for premium pairs (AA, KK)."""
    print("=" * 70)
    print("Test 7: Hand binning - Premium Pair (AA)")
    print("=" * 70)
    
    hand = ['as', 'ah']
    bin_result = bin_preflop_hand(hand)
    bin_enum = preflop_bins(bin_result)
    
    print(f"  Hand: {hand} -> bin = {bin_enum.name}")
    passed = bin_enum == preflop_bins.PremiumPair
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_hand_bin_nut_broadway_suited():
    """Test hand binning for nut broadway suited (AKs)."""
    print("=" * 70)
    print("Test 8: Hand binning - Nut Broadway Suited (AKs)")
    print("=" * 70)
    
    hand = ['as', 'ks']
    bin_result = bin_preflop_hand(hand)
    bin_enum = preflop_bins(bin_result)
    
    print(f"  Hand: {hand} -> bin = {bin_enum.name}")
    passed = bin_enum == preflop_bins.NutBWSuited
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_hand_bin_broadway_offsuit():
    """Test hand binning for broadway offsuit (AKo, KQo, etc.)."""
    print("=" * 70)
    print("Test 9: Hand binning - Broadway Offsuit (AKo)")
    print("=" * 70)
    
    hand = ['as', 'kh']
    bin_result = bin_preflop_hand(hand)
    bin_enum = preflop_bins(bin_result)
    
    print(f"  Hand: {hand} -> bin = {bin_enum.name}")
    passed = bin_enum == preflop_bins.BWOffsuit
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_hand_bin_ace_low_suited():
    """Test hand binning for ace-low suited (A2s, A5s, etc.)."""
    print("=" * 70)
    print("Test 10: Hand binning - Ace Low Suited (A5s)")
    print("=" * 70)
    
    hand = ['as', '5s']
    bin_result = bin_preflop_hand(hand)
    bin_enum = preflop_bins(bin_result)
    
    print(f"  Hand: {hand} -> bin = {bin_enum.name}")
    passed = bin_enum == preflop_bins.SuitedAceLow
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_hand_bin_trash():
    """Test hand binning for trash hands (low offsuit unconnected)."""
    print("=" * 70)
    print("Test 11: Hand binning - Trash Hand (3o7o)")
    print("=" * 70)
    
    hand = ['3h', '7c']
    bin_result = bin_preflop_hand(hand)
    bin_enum = preflop_bins(bin_result)
    
    print(f"  Hand: {hand} -> bin = {bin_enum.name}")
    passed = bin_enum == preflop_bins.TrashOffsuit
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_preflop_action_premium_pair():
    """Test preflop betting action for premium pair."""
    print("=" * 70)
    print("Test 12: Preflop action - Premium Pair (AA) should raise")
    print("=" * 70)
    
    state = MockGameState(
        index_to_action=2,
        sb_index=0,
        player_cards=['as', 'ah'],
        small_blind=1,
        big_blind=2
    )
    memory = Memory()
    
    bet_amount, _ = bet(state, memory)
    
    print(f"  Hand: {state.player_cards}, Position: {get_preflop_position(state).name}")
    print(f"  Bet amount: {bet_amount}")
    
    # Premium pair should raise (bet > 0)
    passed = bet_amount > 0
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_preflop_action_trash_hand():
    """Test preflop betting action for trash hand."""
    print("=" * 70)
    print("Test 13: Preflop action - Trash Hand should fold")
    print("=" * 70)
    
    state = MockGameState(
        index_to_action=2,
        sb_index=0,
        player_cards=['3h', '7c'],
        small_blind=1,
        big_blind=2
    )
    memory = Memory()
    
    bet_amount, _ = bet(state, memory)
    
    print(f"  Hand: {state.player_cards}, Position: {get_preflop_position(state).name}")
    print(f"  Bet amount: {bet_amount} (-1 = fold)")
    
    # Trash hand should fold (-1)
    passed = bet_amount == -1
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_memory_initialization():
    """Test that Memory initializes correctly."""
    print("=" * 70)
    print("Test 14: Memory initialization")
    print("=" * 70)
    
    memory = Memory()
    
    print(f"  Memory created with round_number = {memory.round_number}")
    passed = memory.round_number == 0
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def main():
    tests = [
        test_position_small_blind,
        test_position_big_blind,
        test_position_utg,
        test_position_button,
        test_position_with_offset_sb,
        test_position_with_hero_before_sb,
        test_hand_bin_premium_pair,
        test_hand_bin_nut_broadway_suited,
        test_hand_bin_broadway_offsuit,
        test_hand_bin_ace_low_suited,
        test_hand_bin_trash,
        test_preflop_action_premium_pair,
        test_preflop_action_trash_hand,
        test_memory_initialization,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"  ✗ FAIL: {e}\n")
            results.append(False)
    
    print("=" * 70)
    print(f"SUMMARY: {sum(results)}/{len(results)} tests passed")
    print("=" * 70)
    return all(results)


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)