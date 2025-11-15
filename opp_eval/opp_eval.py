# ultra_light_aggression.py
# Pure Python, no external libs. One estimator instance per opponent.

import math

def _sigmoid(x, k=6.0):
    # Stable sigmoid in (0,1)
    return 1.0 / (1.0 + math.exp(-k * x))

class OpponentAggressionEstimator:
    """
    Tracks simple EWMAs and returns an aggression score in [0,1].
    Call update(bet_ratio, stack_bb) for each meaningful action where villain bets/raises (or call with ratio=0).
    """
    def __init__(self,
                 ewma_alpha=0.15,
                 big_bet_threshold=0.5,
                 w_avg=1.0,
                 w_big=1.2,
                 w_stack=-0.6,
                 sigmoid_k=6.0,
                 init_avg=0.15,
                 init_big_rate=0.05):
        # EWMA state
        self.ewma_alpha = ewma_alpha
        self.avg_bet_ratio = init_avg      # EWMA of bet / pot
        self.big_bet_rate = init_big_rate  # EWMA of (bet_ratio >= threshold)
        self.big_bet_threshold = big_bet_threshold

        # combination weights
        self.w_avg = w_avg
        self.w_big = w_big
        self.w_stack = w_stack
        self.sigmoid_k = sigmoid_k

        # counters (optional) to detect cold-start
        self.t = 0

    def update(self, bet_ratio, stack_bb):
        """
        Update EWMA stats for one observed bet action.
        bet_ratio: bet_size / pot_size (0 if check/call/no-bet)
        stack_bb: opponent effective stack in BB at that moment (float)
        Returns: aggression score in [0,1]
        """
        a = self.ewma_alpha
        # update avg bet ratio EWMA
        self.avg_bet_ratio = (1 - a) * self.avg_bet_ratio + a * bet_ratio

        # update big bet rate EWMA
        big_flag = 1.0 if bet_ratio >= self.big_bet_threshold else 0.0
        self.big_bet_rate = (1 - a) * self.big_bet_rate + a * big_flag

        self.t += 1

        return self.aggression_score(stack_bb)

    def aggression_score(self, stack_bb):
        """
        Compute aggression score in [0,1] from current EWMAs and stack.
        stack_bb: effective stack in BB
        """
        # normalize stack to [0,1] where 0=very small (~5bb), 1=very large (>=200bb).
        # adjust min/max to taste.
        min_stack, max_stack = 5.0, 200.0
        s = max(min(stack_bb, max_stack), min_stack)
        stack_norm = (s - min_stack) / (max_stack - min_stack)  # in [0,1]

        # feature vector (you can add more features if you want)
        x_avg = self.avg_bet_ratio     # expected 0..~2 (but usually <1)
        x_big = self.big_bet_rate      # 0..1
        x_stack = stack_norm           # 0..1

        # optionally scale x_avg to [0,1] by dividing by a reasonable cap (e.g., 1.0)
        x_avg_clipped = min(x_avg, 2.0) / 2.0   # now in [0,1] (cap to keep stability)

        # linear score
        linear = (self.w_avg * x_avg_clipped) + (self.w_big * x_big) + (self.w_stack * x_stack - 0.0)
        # apply sigmoid to squash to [0,1]
        agg = _sigmoid(linear, k=self.sigmoid_k)
        return agg

    # convenience: map aggression to range multiplier (how much wider the villain range)
    def range_multiplier(self, aggression, low=0.7, high=1.6):
        """
        Maps aggression∈[0,1] to multiplier in [low,high].
        Aggression=0 -> multiplier low (tighter range)
        Aggression=1 -> multiplier high (wider range)
        """
        return low + (high - low) * aggression

    # convenience: approximate adjusted equity against widened/tightened range
    def adjusted_equity(self, raw_equity, aggression, beta=0.9):
        """
        A light approximation: shrink equity when villain range widens.
        raw_equity: your equity vs baseline range (0..1)
        aggression: 0..1
        beta: exponent control (0<beta<=1). beta<1 makes effect milder.
        Formula: adj = raw_equity / (range_mult ** beta)
        """
        r = self.range_multiplier(aggression)
        adj = raw_equity / (r ** beta)
        # clamp to [0,1]
        adj = max(0.0, min(1.0, adj))
        return adj
