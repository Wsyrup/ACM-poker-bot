#!/usr/bin/env python3
"""
Offline equity calculation tests for `equity/equity_calc.py`.

These tests follow the same print-and-return style as the project's
hand-evaluator tests. They exercise deterministic 5-card and 7-card
equity functions and one Monte Carlo sanity check.
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


def test_identical_hands_tie():
    """If both players have exactly the same 5 cards, equity should be 0.5."""
    print("=" * 70)
    print("Test 1: Identical 5-card hands should tie (equity == 0.5)")
    print("=" * 70)

    my_hand = ['as', 'ks', 'qs', 'js', 'ts']
    opp_hand = list(my_hand)

    equity = ec.estimate_equity_5cards(my_hand, [opp_hand], num_simulations=1)
    print(f"  My hand: {my_hand} vs identical opponent -> equity = {equity}")

    passed = almost_equal(equity, 0.5)
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_single_opponent_win():
    """A clearly stronger 5-card hand should have 1.0 equity vs a weaker hand."""
    print("=" * 70)
    print("Test 2: Strong hand vs weak hand (deterministic win)")
    print("=" * 70)

    my_hand = ['as', 'ad', 'kh', 'qc', 'jh']  # Pair of Aces
    opp_hand = ['2s', '3d', '4h', '5c', '7h']  # High card 7

    equity = ec.estimate_equity_5cards(my_hand, [opp_hand], num_simulations=1)
    print(f"  My hand: {my_hand} vs {opp_hand} -> equity = {equity}")

    passed = almost_equal(equity, 1.0)
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_multiple_opponents():
    """Equity vs multiple opponents should be computed correctly (split ties appropriately).

    Here we use one strong hand and two weak hands; equity should be high (> 0.66).
    """
    print("=" * 70)
    print("Test 3: Multiple opponents")
    print("=" * 70)

    my_hand = ['as', 'ad', 'kh', 'qc', 'jh']
    opp1 = ['2s', '3d', '4h', '5c', '7h']
    opp2 = ['2h', '4d', '6c', '8s', '9h']

    equity = ec.estimate_equity_5cards(my_hand, [opp1, opp2], num_simulations=1)
    print(f"  My hand vs two weak opponents -> equity = {equity}")

    passed = equity > 0.66
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_7card_identical_tie_and_win():
    """Test 7-card (best-hand) deterministic tie and win cases."""
    print("=" * 70)
    print("Test 4: 7-card identical tie and clear win")
    print("=" * 70)

    # Identical 7-card sets -> tie
    my_cards = ['as', 'ks', 'qs', 'js', 'ts', '9s', '8s']
    opp_cards = list(my_cards)

    eq_tie = ec.estimate_equity_7cards(my_cards, [opp_cards], num_simulations=1)
    print(f"  Identical 7-card hands -> equity = {eq_tie}")

    # Clear win: opponent with much weaker 7-card set
    opp_weak = ['2s', '3d', '4h', '5c', '7h', '9d', '8c']
    eq_win = ec.estimate_equity_7cards(my_cards, [opp_weak], num_simulations=1)
    print(f"  Versus weak opponent -> equity = {eq_win}")

    passed = almost_equal(eq_tie, 0.5) and almost_equal(eq_win, 1.0)
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def test_monte_carlo_approximation():
    """Monte Carlo sanity check: identical hands should be ~0.5 with many sims (stable).

    We seed the RNG for reproducibility.
    """
    print("=" * 70)
    print("Test 5: Monte Carlo approximation consistency")
    print("=" * 70)

    random.seed(42)
    my_hand = ['as', 'ks', 'qs', 'js', 'ts']
    opp_hand = list(my_hand)

    equity = ec.estimate_equity_5cards(my_hand, [opp_hand], num_simulations=500)
    print(f"  Monte Carlo (identical hands, 500 sims) -> equity = {equity}")

    # Expect roughly 0.5; allow generous tolerance for a small sample
    passed = 0.4 <= equity <= 0.6
    print(f"  {'✓ PASS' if passed else '✗ FAIL'}\n")
    return passed


def main():
    tests = [
        test_identical_hands_tie,
        test_single_opponent_win,
        test_multiple_opponents,
        test_7card_identical_tie_and_win,
        test_monte_carlo_approximation,
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
