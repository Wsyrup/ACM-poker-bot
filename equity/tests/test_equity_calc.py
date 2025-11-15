#!/usr/bin/env python3
"""
Offline equity calculation tests for `equity/equity_calc.py`.

These tests follow the same print-and-return style as the project's
hand-evaluator tests. They exercise the unified estimate_equity function
across preflop, flop, turn, and river scenarios.
"""

import os
import sys
import math

# Ensure the equity module (one level up) is importable as `equity_calc`.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import equity_calc as ec
import random


def almost_equal(a, b, tol=1e-6):
    return abs(a - b) <= tol


def test_identical_hands_preflop():
    """If both players have identical hole cards, equity should be 0.5 preflop."""
    print("=" * 70)
    print("Test 1: Identical hole cards preflop (equity == 0.5)")
    print("=" * 70)

    hero_hole = ['as', 'ks']
    villain_range = ['as', 'ks']  # Identical hole cards
    community_hand = []  # Empty preflop
    num_opps = 1

    equity = ec.estimate_equity(hero_hole, villain_range, num_opps, community_hand, num_sims=1)
    print(f"  Hero: {hero_hole} vs Villain: {villain_range}")
    print(f"  Community: (empty) -> equity = {equity}")

    passed = almost_equal(equity, 0.5)
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_strong_hand_vs_weak_hand_flop():
    """Test equity on the flop: strong hand (pair of aces) vs weak hand (high card)."""
    print("=" * 70)
    print("Test 2: Strong hand vs weak hand on flop")
    print("=" * 70)

    hero_hole = ['as', 'ad']  # Pair of Aces
    villain_range = ['2s', '3d']  # Weak hand
    community_hand = ['kh', 'qc', 'jh']  # Flop
    num_opps = 1

    equity = ec.estimate_equity(hero_hole, villain_range, num_opps, community_hand, num_sims=1)
    print(f"  Hero (flop): {hero_hole} -> best hand from community")
    print(f"  Villain (flop): {villain_range}")
    print(f"  Community: {community_hand}")
    print(f"  Equity: {equity}")

    # Hero should have very high equity (pair vs high card)
    passed = equity > 0.8
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_multiple_opponents_equity():
    """Test equity calculation with multiple opponents."""
    print("=" * 70)
    print("Test 3: Equity split across multiple opponents")
    print("=" * 70)

    hero_hole = ['as', 'ad']  # Pair of Aces (strong)
    villain_range = ['2s', '3d', '4h', '5c', '6h']  # Weak combined range
    community_hand = ['kh', 'qc', 'jh']
    num_opps = 2  # Two opponents

    equity = ec.estimate_equity(hero_hole, villain_range, num_opps, community_hand, num_sims=1)
    print(f"  Hero: {hero_hole}")
    print(f"  Villain range: {villain_range}")
    print(f"  Community: {community_hand}")
    print(f"  Opponents: {num_opps}")
    print(f"  Equity: {equity}")

    # Hero should have good equity vs multiple weak opponents
    passed = equity > 0.4
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_equity_on_turn():
    """Test equity calculation on the turn (4 community cards)."""
    print("=" * 70)
    print("Test 4: Equity on the turn (4 community cards)")
    print("=" * 70)

    hero_hole = ['as', 'ks']  # Big cards
    villain_range = ['2s', '3d', '4h', '5c', '6h']  # Weak cards
    community_hand = ['ad', 'kd', 'qd', 'jd']  # Turn: 4 community cards
    num_opps = 1

    equity = ec.estimate_equity(hero_hole, villain_range, num_opps, community_hand, num_sims=1)
    print(f"  Hero (turn): {hero_hole}")
    print(f"  Villain (turn): {villain_range}")
    print(f"  Community: {community_hand}")
    print(f"  Equity: {equity}")

    # Hero has good cards, should have reasonable equity
    passed = 0.0 <= equity <= 1.0  # Just check it's a valid equity
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_equity_on_river():
    """Test equity calculation on the river (all 5 community cards known)."""
    print("=" * 70)
    print("Test 5: Equity on the river (5 community cards)")
    print("=" * 70)

    hero_hole = ['as', 'ad']  # Pair of Aces (strong)
    villain_range = ['2s', '3d', '4h', '5c', '6h']  # High card 6
    community_hand = ['kh', 'qc', 'jh', '9s', '8d']  # River: all 5 community
    num_opps = 1

    equity = ec.estimate_equity(hero_hole, villain_range, num_opps, community_hand, num_sims=1)
    print(f"  Hero (river): {hero_hole}")
    print(f"  Villain (river): {villain_range}")
    print(f"  Community: {community_hand}")
    print(f"  Equity: {equity}")

    # On river with all cards known, hero should win (pair > high card)
    passed = almost_equal(equity, 1.0)
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_monte_carlo_consistency():
    """Monte Carlo sanity check: results should be stable with consistent seed."""
    print("=" * 70)
    print("Test 6: Monte Carlo consistency (seeded RNG)")
    print("=" * 70)

    random.seed(42)
    hero_hole = ['as', 'ks']
    villain_range = ['2s', '3d', '4h', '5c', '6h']
    community_hand = ['ad', 'kd']  # Flop
    num_opps = 1

    equity1 = ec.estimate_equity(hero_hole, villain_range, num_opps, community_hand, num_sims=100)
    
    # Reseed and run again
    random.seed(42)
    equity2 = ec.estimate_equity(hero_hole, villain_range, num_opps, community_hand, num_sims=100)
    
    print(f"  First run (seed 42): equity = {equity1}")
    print(f"  Second run (seed 42): equity = {equity2}")

    # With the same seed, should get identical results
    passed = almost_equal(equity1, equity2)
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_equity_range_validity():
    """Test that equity is always in the valid range [0, 1]."""
    print("=" * 70)
    print("Test 7: Equity is always valid (0 <= equity <= 1)")
    print("=" * 70)

    test_cases = [
        (['as', 'ad'], ['2s', '3d'], []),
        (['ks', 'kd'], ['2s', '3d'], ['5h', '6c']),
        (['as', 'ks'], ['2s', '3d'], ['5h', '6c', '7d']),
    ]

    all_valid = True
    for hero, villain, community in test_cases:
        equity = ec.estimate_equity(hero, villain, 1, community, num_sims=1)
        valid = 0.0 <= equity <= 1.0
        all_valid = all_valid and valid
        print(f"  Hero: {hero}, Community: {community} -> equity = {equity} {'✓' if valid else '✗'}")

    print(f"  {'✓ PASS' if all_valid else '✗ FAIL'}\n")
    return all_valid


def main():
    tests = [
        test_identical_hands_preflop,
        test_strong_hand_vs_weak_hand_flop,
        test_multiple_opponents_equity,
        test_equity_on_turn,
        test_equity_on_river,
        test_monte_carlo_consistency,
        test_equity_range_validity,
    ]

    results = []
    for t in tests:
        try:
            results.append(t())
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
