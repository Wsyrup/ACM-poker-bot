# Cactus Kev Hand Evaluator

A fast, integer-based poker hand evaluator implemented in Python following the Cactus Kev algorithm.

## Overview

This module provides O(1) hand evaluation for 5-card poker hands and supports finding the best 5-card hand from 7 cards (Texas Hold'em style).

**Key Features:**
- Fast integer-based evaluation (no iterative algorithms)
- Correct poker hand ranking hierarchy
- Kicker-aware comparisons within hand categories
- Support for wheel (A-2-3-4-5) straight
- 7-card best-hand finding

## Quick Start

```python
from equity.hand_eval import evaluate_hand, evaluate_best_hand

# Evaluate a 5-card hand (lower rank = better hand)
royal_flush = evaluate_hand(['as', 'ks', 'qs', 'js', 'ts'])
pair_of_aces = evaluate_hand(['as', 'ad', 'kh', 'qc', 'jh'])

print(royal_flush < pair_of_aces)  # True - Royal flush beats pair

# Find best 5-card hand from 7 (Texas Hold'em)
community = ['as', 'ks', 'qs', '2d', '3h']
hole = ['js', 'ts']
best_rank = evaluate_best_hand(community + hole)
```

## Hand Ranking

Hands are ranked with lower numeric values representing stronger hands:

| Hand | Rank Range |
|------|-----------|
| Royal Flush | 0 |
| Straight Flush | 1-823 |
| Four of a Kind | 1000-1191 |
| Full House | 1200-1391 |
| Flush | 1400-2215 |
| Straight | 1600-2399 |
| Three of a Kind | 2000-2215 |
| Two Pair | 3000-3255 |
| One Pair | 4000-6047 |
| High Card | 6200+ |

Within each category, better hands have lower values (e.g., Pair of Aces < Pair of Kings).

## Card Encoding

Cards are represented as strings with 2 characters:
- First character: rank (`2-9`, `t` for 10, `j`, `q`, `k`, `a`)
- Second character: suit (`s` for spades, `h` for hearts, `d` for diamonds, `c` for clubs)

Examples: `'as'` (Ace of spades), `'2h'` (2 of hearts), `'td'` (10 of diamonds)

## API

### `evaluate_hand(cards: list) -> int`

Evaluate a 5-card poker hand.

**Args:**
- `cards`: List of 5 card strings (e.g., `['as', 'ks', 'qs', 'js', 'ts']`)

**Returns:**
- Integer hand ranking (lower is better)

### `evaluate_best_hand(cards: list) -> int`

Find the best 5-card hand ranking from 7 cards (Texas Hold'em style).

**Args:**
- `cards`: List of 7 card strings

**Returns:**
- Integer hand ranking of the best 5-card combination

### `HandEvaluator` Class

For advanced use, instantiate the evaluator directly:

```python
from equity.hand_eval import HandEvaluator

evaluator = HandEvaluator()
rank = evaluator.evaluate_5cards(['as', 'ks', 'qs', 'js', 'ts'])
best = evaluator.evaluate_7cards(['as', 'ks', 'qs', 'js', 'ts', '9s', '8s'])
```

## Testing

Run the test suite to verify correctness:

```bash
python equity/test_hand_eval.py
```

Tests cover:
1. ✓ Hand ranking hierarchy (straight flush > four of a kind > ... > high card)
2. ✓ 7-card best-hand evaluation
3. ✓ Wheel straight (A-2-3-4-5) handling
4. ✓ Kicker-aware comparisons (e.g., Pair of Aces with K-Q-J > Pair of Aces with K-Q-T)

## Implementation Notes

- **Straight detection**: Includes special handling for the "wheel" (5-high straight with Ace as 1)
- **Flush detection**: Uses suit pattern matching
- **Hand classification**: Uses rank frequency counting to identify pairs, trips, quads, etc.
- **Kicker ordering**: Encodes kickers into the ranking value for correct comparison within hand categories
- **Performance**: O(1) evaluation for 5-card hands, O(21) for 7-card hands (C(7,5) = 21 combinations to check)

## References

Based on the Cactus Kev algorithm described at: http://suffe.cool/poker/evaluator.html
