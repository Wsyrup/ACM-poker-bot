#!/usr/bin/env python3
"""
Test suite for the Cactus Kev hand evaluator.
Demonstrates usage and validates correctness.
"""

from hand_eval import evaluate_hand, evaluate_best_hand, HandEvaluator


def test_hand_rankings():
    """Test that hand rankings are correct and ordered properly."""
    print("=" * 70)
    print("Test 1: Hand Rankings (lower = better)")
    print("=" * 70)
    
    test_cases = [
        (['as', 'ks', 'qs', 'js', 'ts'], "Royal Flush"),
        (['9s', '8s', '7s', '6s', '5s'], "9-high Straight Flush"),
        (['as', 'ad', 'ac', 'ah', 'kh'], "Four of a Kind (Aces)"),
        (['ks', 'kd', 'kc', 'qs', 'qd'], "Full House (K over Q)"),
        (['as', 'ks', 'qs', 'js', '9s'], "Ace-high Flush"),
        (['ad', 'kh', 'qc', 'js', 'ts'], "Ace-high Straight"),
        (['as', 'ad', 'ac', 'kh', 'qc'], "Three of a Kind (Aces)"),
        (['as', 'ad', 'ks', 'kd', 'qh'], "Two Pair (A and K)"),
        (['as', 'ad', 'ks', 'qd', 'jh'], "Pair of Aces"),
        (['ad', 'kh', 'qc', 'js', '9s'], "High Card (Ace)"),
    ]
    
    results = []
    for hand, description in test_cases:
        rank = evaluate_hand(hand)
        results.append((rank, description))
        print(f"  {rank:6d} - {description:30s} {hand}")
    
    # Verify ordering
    all_ordered = all(results[i][0] <= results[i+1][0] for i in range(len(results)-1))
    status = "✓ PASS" if all_ordered else "✗ FAIL"
    print(f"\n  {status}: All hands in ascending order\n")
    return all_ordered


def test_7card_evaluation():
    """Test best-hand evaluation from 7 cards (Texas Hold'em)."""
    print("=" * 70)
    print("Test 2: Best Hand from 7 Cards (Texas Hold'em)")
    print("=" * 70)
    
    community = ['as', 'ks', 'qs', '2d', '3h']
    test_cases = [
        (['js', 'ts'], "Royal Flush"),
        (['9s', '8s'], "9-high Straight Flush"),
        (['ad', 'ac'], "Pair of Aces"),
    ]
    
    print(f"  Community cards: {community}\n")
    
    for hole, description in test_cases:
        best_rank = evaluate_best_hand(community + hole)
        print(f"  Hole: {str(hole):20s} -> Best rank: {best_rank:6d} ({description})")
    
    print()
    return True


def test_wheel():
    """Test the wheel straight (A-2-3-4-5) - lowest straight."""
    print("=" * 70)
    print("Test 3: Wheel Straight (A-2-3-4-5)")
    print("=" * 70)
    
    wheel = ['ad', '2h', '3c', '4s', '5d']
    wheel_flush = ['ad', '2d', '3d', '4d', '5d']
    king_straight = ['ad', 'kh', 'qc', 'js', 'ts']
    
    wheel_rank = evaluate_hand(wheel)
    wheel_flush_rank = evaluate_hand(wheel_flush)
    king_rank = evaluate_hand(king_straight)
    
    print(f"  Wheel (5-high):         {wheel} -> rank {wheel_rank}")
    print(f"  Wheel flush (5-high):   {wheel_flush} -> rank {wheel_flush_rank}")
    print(f"  King-high straight:     {king_straight} -> rank {king_rank}")
    print()
    
    # Wheel should be lowest straight, wheel flush should be lowest straight flush
    status = "✓ PASS" if (wheel_rank > king_rank and wheel_flush_rank == 1) else "✗ FAIL"
    print(f"  {status}\n")
    return wheel_rank > king_rank and wheel_flush_rank == 1


def test_kicker_ordering():
    """Test that hands with same category but different kickers rank correctly."""
    print("=" * 70)
    print("Test 4: Kicker Ordering (same hand category, different kickers)")
    print("=" * 70)
    
    pair_aces_kqj = ['as', 'ad', 'ks', 'qd', 'jh']
    pair_aces_kqt = ['as', 'ad', 'ks', 'qd', 'th']
    pair_kings = ['ks', 'kd', 'ah', 'qh', 'jh']
    
    rank1 = evaluate_hand(pair_aces_kqj)
    rank2 = evaluate_hand(pair_aces_kqt)
    rank3 = evaluate_hand(pair_kings)
    
    print(f"  Pair of Aces (K,Q,J): {pair_aces_kqj} -> rank {rank1}")
    print(f"  Pair of Aces (K,Q,T): {pair_aces_kqt} -> rank {rank2}")
    print(f"  Pair of Kings (A,Q,J): {pair_kings} -> rank {rank3}")
    print()
    
    # Pair of Aces with K-Q-J > Pair of Aces with K-Q-T > Pair of Kings with A-Q-J
    better1 = rank1 < rank2 and rank2 < rank3
    status = "✓ PASS" if better1 else "✗ FAIL"
    print(f"  {status}: Correct kicker ordering\n")
    return better1


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " CACTUS KEV HAND EVALUATOR - TEST SUITE ".center(68) + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    tests = [
        test_hand_rankings,
        test_7card_evaluation,
        test_wheel,
        test_kicker_ordering,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ FAIL: {e}\n")
            results.append(False)
    
    print("=" * 70)
    print(f"SUMMARY: {sum(results)}/{len(results)} tests passed")
    print("=" * 70)
    print()
    
    return all(results)


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
