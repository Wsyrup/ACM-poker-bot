# <IMPORTS HERE>

# </IMPORTS HERE>

# <DO NOT MODIFY>
from helpers import *

class Pot:
    value: int
    players: list[str]


class GameState:
    index_to_action: int
    index_of_small_blind: int
    players: list[str]
    player_cards: list[str]
    held_money: list[int]
    bet_money: list[int]
    community_cards: list[str]
    pots: list[Pot]
    small_blind: int
    big_blind: int
# </DO NOT MODIFY>


""" Store any persistent data for your bot in this class """
class Memory:
    pass


""" Make a betting decision for the current turn.

    This function is called every time your bot needs to make a bet.

    Args:
        state (GameState): The current state of the game.
        memory (Memory | None): Your bot's memory from the previous turn, or None if this is the first turn.

    Returns:
        tuple[int, Memory | None]: A tuple containing:
            bet_amount: int - The amount you want to bet (-1 to fold, 0 to check, or any positive integer to raise)
            memory: Memory | None - Your bot's updated memory to be passed to the next turn
"""

def bet(state: GameState, memory: Memory | None=None) -> tuple[int, Memory | None]:
    bet_amount = 0
    return (bet_amount, memory)

#bet strategy:
'''
1. calculate hand equity
2. based on equity and pot odds, decide on preflop action
3. then, use existing equity + classification model of opponents to determine postflop actions
4. adjust bet based on risk analysis and opponent classification.
5. implement bluffing strategy based on game dynamics and opponent tendencies.
    e.g., bluff against "tight" players, call "aggressive" players, etc...
6. continuously update opponent models based on observed behavior (throughout the game).


7. refine betting strategy using reinforcement learning techniques over multiple games 
(train analysis biases throughout weekend)?
linear regression / predictive model based on hands, types of opponents in pot
use that to adjust bet sizing and bluff frequency. 

    
'''