# \[ACM.Dev\] [Mann Vs Machine](https://wiki.teamfortress.com/wiki/Mann_vs._Machine): Poker Bot Starter Code

Welcome to the Poker Bot Tournament!
This repo contains the starter code to build a poker bot for our [poker bot tournament](https://acm-poker-tournament.vercel.app/).

To ensure smooth gameplay and fair evaluation, all teams must follow the submission guidelines outlined below. Any submissions not adhering to these rules may be disqualified.

## Important
- Please submit your code before **11:59 PM on November 6, 2025**, no late submission will not be accepted.
- Submission must be made on [your dashboard](https://acm-poker-tournament.vercel.app/dashboard), and all of your code must be in one file.
- Bots are called only during their own turn; they should not rely on global state or other bots’ internals. Keep this in mind when coding up your bot.
- Illegal moves will be automatically treated as folding. For example, checking when a raise is required or betting less than the required minimum.
- Your bot will be have a runtime limit of 5s each time its run.
- Additional helper functions/classes are allowed as long as they don’t interfere with the interface.


## Submission Rules
- You should only submit one file.
- Do not modify the `bet(state: GameState) -> int` function signature or class definitions in the code template.
- Do not modify the required function signatures or class definitions in the template.

## Input Format
- Your bot will receive the current game state (using the template schemas provided) and is expected to return a single valid poker action on its turn.

Every turn your poker bot will be invoke through system call and receives `state` as the input with the `GameState` type. The definition of `GameState` can be found below and inside `bot.py`.
```python
# cards are defined as a 2 character string [value][suite]
# where 1st char: a(2-9)tjqk, 2nd char: s d c h

class Pot:
    value: int
    players: list[str]

class GameState:
    index_to_action: int
    index_of_small_blind: int
    players: list[str]
    player_cards: list[str]
    held_money: list[int]
    bet_money: list[int]  # -1 for fold, 0 for check/hasn't bet
    community_cards: list[str]
    pots: list[Pot]
    small_blind: int
    big_blind: int
```
Example `GameState`:
```JSON
{
    "index_to_action": 2,
    "index_of_small_blind": 0,
    "players": ["team_id0", "team_id1", "team_id2"],
    "player_cards": ["2s", "7s"],
    "held_money": [100, 200, 300],
    "bet_money": [20, -1, 0],
    "community_cards": ["ac", "2h", "2d"],
    "pots": [{ "value": 50, "players": ["team_id0", "team_id2"] }],
    "small_blind": 5,
    "big_blind": 10
}
```
Example Interpretation:
- Betting round after the flop.
- Player 0 (`team_id0`) bet `20`, Player 1 folded, action is on Player 2.
- Player 2 has trips with 2s and 7s.


## Code Specification & Libraries
- Only Python 3.11 is allowed.
- We only allow some standard python libraries (support for mainstream external libraries will come next time)
- List of black listed standard libraries can be found [here](https://docs.google.com/document/d/1Q78tdVFAZIFt0ZWEgNG65nDDAlbt6rcG5o21waeZprA/edit?usp=sharing).


## Testing
- A local tournament simulator will be provided for participants.
- We strongly recommend testing your bot locally to ensure it:
  - Runs without errors
  - Complies with the template interface
  - Performs within the time limit


## Disqualification Criteria
- The bot throws errors or crashes during the game.
- It fails to follow the required interface.
- It uses illegal libraries or external resources.
- It exceeds time limits repeatedly.
- It makes illegal moves (see below).


## Additional Things to Note
- If you have special requests (e.g., library whitelisting, accommodations), contact us through Discord before the submission deadline.
- All submissions will undergo code reviews to ensure fairness and runtime safety. Non-compliant bots will be disqualified.
- ACM.Dev reserve the rights to disqualify participant at our discretion.


## Contact & Support
For technical issues or clarifications
- Join our [Discord server](https://discord.gg/p6rcUUjWaU)
- Or email us at: acm.dev.ucsb@gmail.com