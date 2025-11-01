# <DO NOT MODIFY>
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

# Store any persistent data for your bot in this class
class Memory:
    pass

# DO NOT MODIFY THE FUNCTION SIGNATURE
# This function is called every time your bot needs to make a bet
# INPUT: state: GameState - The current state of the game
#        memory: Memory | None - Your bot's memory from the previous turn, or None if this is the first turn
# OUTPUT: A tuple containing:
#        bet_amount: int - The amount you want to bet (-1 to fold, 0 to check, or any positive integer to raise)
#        memory: Memory | None - Your bot's updated memory to be passed to the next turn
def bet(state: GameState, memory: Memory | None=None) -> tuple[int, Memory | None]:
    bet_amount = 0
    return (bet_amount, memory)
