#cactus kev hand evaluator implementation
"""
Cactus Kev's Poker Hand Evaluator

A fast, integer-based 5-card poker hand evaluator.
Uses bit manipulation and lookup tables for O(1) evaluation.

Card encoding:
- Cards are represented as 16-bit integers
- Bits 0-3:   rank (0-12, where 0=deuce, 12=ace)
- Bits 4-5:   suit (0-3)
- Bits 6-15:  derived fields for fast evaluation

References:
- http://suffe.cool/poker/evaluator.html
- Hand ranking: straight flush, four of a kind, full house, flush, straight, 
  three of a kind, two pair, pair, high card
"""

# === Card Rank/Suit Constants ===
DEUCE = 0
THREE = 1
FOUR = 2
FIVE = 3
SIX = 4
SEVEN = 5
EIGHT = 6
NINE = 7
TEN = 8
JACK = 9
QUEEN = 10
KING = 11
ACE = 12

SPADE = 0
HEART = 1
DIAMOND = 2
CLUB = 3

# Map string representations to rank/suit indices
RANK_MAP = {
    '2': DEUCE, '3': THREE, '4': FOUR, '5': FIVE, '6': SIX,
    '7': SEVEN, '8': EIGHT, '9': NINE, 't': TEN, 'j': JACK,
    'q': QUEEN, 'k': KING, 'a': ACE
}

SUIT_MAP = {'s': SPADE, 'h': HEART, 'd': DIAMOND, 'c': CLUB}

RANK_STR = ['2', '3', '4', '5', '6', '7', '8', '9', 't', 'j', 'q', 'k', 'a']
SUIT_STR = ['s', 'h', 'd', 'c']


def string_to_card(card_str: str) -> int:
    """
    Convert card string (e.g., '2s', 'As', 'Kd') to integer encoding.
    
    Args:
        card_str: 2-character string [rank][suit]
        
    Returns:
        Integer representation of card (16-bit)
    """
    rank_char = card_str[0].lower()
    suit_char = card_str[1].lower()
    
    if rank_char not in RANK_MAP or suit_char not in SUIT_MAP:
        raise ValueError(f"Invalid card string: {card_str}")
    
    rank = RANK_MAP[rank_char]
    suit = SUIT_MAP[suit_char]
    
    # Encode: bits 0-3=rank, bits 4-5=suit, bits 6-15=derived
    return (rank & 0xF) | ((suit & 0x3) << 4)


def card_to_string(card: int) -> str:
    """Convert integer card encoding back to string representation."""
    rank = card & 0xF
    suit = (card >> 4) & 0x3
    return RANK_STR[rank] + SUIT_STR[suit]


class HandEvaluator:
    """Fast 5-card poker hand evaluator using Cactus Kev algorithm."""
    
    def __init__(self):
        # Precompute lookup tables for fast evaluation
        self._build_tables()
    
    def _build_tables(self):
        """Build lookup tables for hand classification."""
        # Flush check: compute flushes based on suit patterns
        self.flush_table = self._build_flush_table()
        
        # Unique 5-card hand rankings (for non-flush hands)
        self.unique_table = self._build_unique_table()
    
    def _build_flush_table(self) -> dict:
        """Build table mapping rank patterns to flush hand rankings."""
        flush_table = {}
        
        # Generate all possible flush combinations (13 choose 5 = 1287)
        # Represented as 13-bit mask where bit i = 1 if rank i is in hand
        
        for mask in range(1 << 13):
            if bin(mask).count('1') != 5:
                continue
            
            # Extract the 5 ranks
            ranks = [i for i in range(13) if mask & (1 << i)]
            
            # Classify the hand
            rank_value = self._classify_hand(ranks)
            flush_table[mask] = rank_value
        
        return flush_table
    
    def _build_unique_table(self) -> dict:
        """Build table for unique 5-card non-flush hands."""
        unique_table = {}
        
        # For non-flush 5-card hands, create unique representation
        # by XORing rank bits
        for mask in range(1 << 13):
            if bin(mask).count('1') != 5:
                continue
            
            ranks = [i for i in range(13) if mask & (1 << i)]
            rank_value = self._classify_hand(ranks)
            
            # Use XOR of ranks as a key for quick lookup
            key = 0
            for rank in ranks:
                key ^= (1 << rank)
            
            unique_table[key] = rank_value
        
        return unique_table
    
    def _classify_hand(self, ranks: list) -> int:
        """
        Classify a 5-card hand by pairs/trips/quads (no straights/flushes).
        
        Ranking order (best to worst):
        - Four of a kind: 1000-1191
        - Full house: 1200-1391
        - Three of a kind: 2000-2215
        - Two pair: 3000-3255
        - Pair: 4000-6047
        - High card: 6200+
        
        Args:
            ranks: List of 5 rank indices (0-12)
            
        Returns:
            Integer ranking (lower is better)
        """
        ranks_sorted = sorted(ranks, reverse=True)
        
        # Count rank frequencies
        from collections import Counter
        freq = Counter(ranks_sorted)
        counts = sorted(freq.values(), reverse=True)
        
        if counts == [4, 1]:
            # Four of a kind
            quad_rank = [r for r in ranks_sorted if ranks.count(r) == 4][0]
            return 1000 + (12 - quad_rank)  # Aces highest
        elif counts == [3, 2]:
            # Full house
            trip_rank = [r for r in ranks_sorted if ranks.count(r) == 3][0]
            pair_rank = [r for r in ranks_sorted if ranks.count(r) == 2][0]
            return 1200 + (12 - trip_rank) * 13 + (12 - pair_rank)
        elif counts == [3, 1, 1]:
            # Three of a kind - encode kickers
            trip_rank = [r for r in ranks_sorted if ranks.count(r) == 3][0]
            kickers = sorted([r for r in ranks if ranks.count(r) == 1], reverse=True)
            kicker_value = sum((13 - k) * (100 >> (i * 2)) for i, k in enumerate(kickers[:2]))
            return 2000 + (12 - trip_rank) * 100 + kicker_value
        elif counts == [2, 2, 1]:
            # Two pair - encode both pairs and kicker
            pairs = sorted([r for r in ranks_sorted if ranks.count(r) == 2], reverse=True)
            kicker = [r for r in ranks if ranks.count(r) == 1][0]
            return 3000 + (12 - pairs[0]) * 100 + (12 - pairs[1]) * 10 + (12 - kicker)
        elif counts == [2, 1, 1, 1]:
            # One pair - need to encode kickers too
            pair_rank = [r for r in ranks_sorted if ranks.count(r) == 2][0]
            kickers = sorted([r for r in ranks if ranks.count(r) == 1], reverse=True)
            # Encode: base + pair_rank*1000 + kicker values
            kicker_value = sum((13 - k) * (100 >> (i * 2)) for i, k in enumerate(kickers[:3]))
            return 4000 + (12 - pair_rank) * 1000 + kicker_value
        else:
            # High card - kicker order matters
            high_card = ranks_sorted[0]
            return 6200 + (12 - high_card) * 1000 + sum(12 - r for r in ranks_sorted[1:])
    
    def _is_straight(self, ranks: list) -> bool:
        """Check if 5 ranks form a straight."""
        if len(ranks) != 5:
            return False
        
        sorted_ranks = sorted(set(ranks))
        
        # Normal straight
        if sorted_ranks[-1] - sorted_ranks[0] == 4 and len(set(ranks)) == 5:
            return True
        
        # Wheel straight (A-2-3-4-5)
        if set(sorted_ranks) == {0, 1, 2, 3, 12}:
            return True
        
        return False
    
    def evaluate_5cards(self, cards: list) -> int:
        """
        Evaluate a 5-card poker hand.
        
        Args:
            cards: List of 5 card integers or card strings
            
        Returns:
            Hand ranking (lower = better hand)
        """
        if len(cards) != 5:
            raise ValueError(f"Expected 5 cards, got {len(cards)}")
        
        # Convert strings to integers if needed
        card_ints = []
        for card in cards:
            if isinstance(card, str):
                card_ints.append(string_to_card(card))
            else:
                card_ints.append(card)
        
        return self._evaluate(card_ints)
    
    def evaluate_7cards(self, cards: list) -> int:
        """
        Evaluate the best 5-card hand from 7 cards.
        
        Args:
            cards: List of 7 card integers or card strings
            
        Returns:
            Hand ranking of the best 5-card hand (lower = better)
        """
        if len(cards) != 7:
            raise ValueError(f"Expected 7 cards, got {len(cards)}")
        
        # Convert strings to integers if needed
        card_ints = []
        for card in cards:
            if isinstance(card, str):
                card_ints.append(string_to_card(card))
            else:
                card_ints.append(card)
        
        # Try all combinations of 5 cards from 7
        from itertools import combinations
        best_rank = float('inf')
        
        for combo in combinations(card_ints, 5):
            rank = self._evaluate(list(combo))
            best_rank = min(best_rank, rank)
        
        return best_rank
    
    def _evaluate(self, card_ints: list) -> int:
        """Internal evaluation of exactly 5 cards."""
        # Extract suits and ranks
        suits = [(card >> 4) & 0x3 for card in card_ints]
        ranks = [card & 0xF for card in card_ints]
        
        # Check if all cards have same suit (flush)
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        ranks_sorted = sorted(ranks, reverse=True)
        is_straight = self._is_straight(ranks_sorted)
        
        if is_flush and is_straight:
            # Straight flush - best possible hands (0-823)
            high_rank = max(ranks)
            if set(ranks) == {0, 1, 2, 3, 12}:  # A-2-3-4-5
                return 1  # Wheel straight flush (lowest rank)
            return (12 - high_rank)  # Royal flush = 0, then increasing
        elif is_flush:
            # Regular flush (not straight) - 1400-2215
            ranks_sorted = sorted(ranks, reverse=True)
            high_card = ranks_sorted[0]
            return 1400 + (12 - high_card) * 1000 + sum(12 - r for r in ranks_sorted[1:])
        elif is_straight:
            # Straight (not a flush) - 1600-2399 (between flush and three-of-a-kind)
            high_rank = ranks_sorted[0]
            if set(ranks) == {0, 1, 2, 3, 12}:  # A-2-3-4-5
                return 1600 + 799  # Wheel is lowest straight
            return 1600 + (12 - high_rank)  # Higher card = lower value (better)
        else:
            # Non-flush, non-straight: classify by pairs
            return self._classify_hand(ranks)


# Global evaluator instance
_evaluator = HandEvaluator()


def evaluate_hand(cards: list) -> int:
    """
    Evaluate a 5-card poker hand.
    
    Args:
        cards: List of 5 cards (can be strings like '2s', 'As', etc. or integers)
        
    Returns:
        Integer hand ranking (lower = better hand)
    """
    return _evaluator.evaluate_5cards(cards)


def evaluate_best_hand(cards: list) -> int:
    """
    Evaluate the best 5-card hand from 7 cards (Texas Hold'em).
    
    Args:
        cards: List of 7 cards (can be strings or integers)
        
    Returns:
        Integer hand ranking of best 5-card hand (lower = better)
    """
    return _evaluator.evaluate_7cards(cards)


# === Hand rank classification helpers ===
def hand_rank_name(rank: int) -> str:
    """Get human-readable name for hand rank."""
    if rank < 1000:
        if rank >= 4096:
            return "Straight"
        elif rank >= 2048:
            if rank >= 3072:
                return "Four of a Kind"
            elif rank >= 2560:
                return "Full House"
            elif rank >= 2560:
                return "Flush"
            elif rank >= 2304:
                return "Three of a Kind"
            elif rank >= 2176:
                return "Two Pair"
            elif rank >= 2144:
                return "Pair"
            else:
                return "High Card"
    else:
        return "Flush"


if __name__ == "__main__":
    # Test the evaluator
    eval = HandEvaluator()
    
    # Test royal flush (5-card hand)
    hand1 = ['as', 'ks', 'qs', 'js', 'ts']
    rank1 = eval.evaluate_5cards(hand1)
    print(f"Royal Flush: {hand1} -> rank {rank1}")
    
    # Test pair
    hand2 = ['as', 'ad', 'kh', 'qc', 'jh']
    rank2 = eval.evaluate_5cards(hand2)
    print(f"Pair of Aces: {hand2} -> rank {rank2}")
    
    # Test best hand from 7 cards
    hand3 = ['as', 'ks', 'qs', 'js', 'ts', '9s', '8s']
    rank3 = eval.evaluate_7cards(hand3)
    print(f"Best from 7: {hand3} -> rank {rank3}")
    
    print(f"\nRoyal Flush < Pair: {rank1 < rank2}")
