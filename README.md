# \[ACM.Dev\] [Mann Vs Machine](https://wiki.teamfortress.com/wiki/Mann_vs._Machine): Poker Bot Starter Code

Welcome to the Poker Bot Tournament!
This repo contains the starter code to build a poker bot for our [poker bot tournament](https://acm-poker-tournament.vercel.app/).

To ensure smooth gameplay and fair evaluation, all teams must follow the submission guidelines outlined below. Any submissions not adhering to these rules may be disqualified.

## Important
- Please submit your code before **11:59 PM on November 13, 2025**, late submissions will not be accepted.
- Submission must be made on [your dashboard](https://acm-poker-tournament.vercel.app/dashboard), and all of your code must be in one file.
- Bots are called only during their own turn; they should not rely on global state or other bots' internals. Keep this in mind when coding up your bot.
- Illegal moves will be automatically treated as folding. For example, checking when a raise is required or betting less than the required minimum.
- Your bot will have a runtime limit of 5s each time it's run.
- Additional helper functions/classes are allowed as long as they don’t interfere with the interface.
- In your final submission, please ensure that you do NOT include any **print statements** as these interfere with the bot's output.


## Submission Rules
- You should only submit one file.
- Do not modify the `bet(state: GameState) -> int` function signature or class definitions in the code template.
- Do not modify the required function signatures or class definitions in the template.

## Input Format
- Your bot will receive the current game state (using the template schemas provided) and is expected to return a single valid poker action on its turn.

Every turn, your poker bot will be invoked through a system call and receive `state` as the input with the `GameState` type. The definition of `GameState` can be found below and inside `bot.py`.
```python
# cards are defined as a 2 character string [value][suite]
# where 1st char: a(2-9)tjqk, 2nd char: s d c h

class Pot:
    value: int
    players: list[str]

class GameState:
    index_to_action: int # your index, for example, bet_money[index_to_action] is your bot's current betting amount
    index_of_small_blind: int
    players: list[str] # list of bots' id, ordered according to their seats
    player_cards: list[str] # list of your cards
    held_money: list[int]
    bet_money: list[int]  # -1 for fold, 0 for check/hasn't bet
    community_cards: list[str]
    pots: list[Pot] # a list of dicts that contain "value" and "players". "value" is the amount in that pot, "players" are the eligible players to win that pot.
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
Interpreting the example:
- Betting round after the flop.
- Player 0 (`team_id0`) bet `20`, Player 1 (`team_id1`) folded, action is on Player 2 (`team_id2`).
- You have triples with 2 spade (`2s`), 2 hearts (`2h`), and 2 diamonds (`2d`).


## Development Setup

This project uses a pure-Python implementation for the bot and equity calculations. The recommended workflow below uses pyenv/virtualenv to create an isolated Python 3.11 environment.

### Initial Setup

Run the setup script to initialize the virtualenv and install Python dependencies:

```bash
./setup.sh
```

Or specify a Python version explicitly:

```bash
./setup.sh 3.11.4
```

What the script does:
1. Install pyenv and pyenv-virtualenv (if configured in your environment)
2. Install the specified Python version (if missing)
3. Create a virtual environment named `poker-cactus-<version>`
4. Install Python dependencies listed by the project
5. Write `.python-version` to auto-activate the virtualenv (if you use pyenv)

### Activating the Virtual Environment

After setup, the virtualenv may be auto-activated when you enter the project directory (via `.python-version`). To manually activate:

```bash
# If you're using bash/zsh with pyenv already initialized:
pyenv activate poker-cactus-3.11.4

# Or, initialize pyenv in-session and activate:
eval "$(pyenv init --path)" && eval "$(pyenv virtualenv-init -)" && pyenv activate poker-cactus-3.11.4
```

If you don't use pyenv you can still create and activate a venv manually:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Code Specification & Libraries
- Only Python 3.11 is allowed.
- We only allow some standard Python libraries and numpy
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
- ACM.Dev reserve the rights to disqualify participants at our discretion.


## Contact & Support
For technical issues or clarifications
- Join our [Discord server](https://discord.gg/p6rcUUjWaU)
- Or email us at: [acm.dev.ucsb@gmail.com](mailto:acm.dev.ucsb@gmail.com)

## Technical specifications & implementation

This project is a Python poker bot implementation optimized for correctness and speed.

### Basic Decision Tree

#### Pre-Flop:
Bin pre-flop hand into one of 13 possible bins, and make a pre-flop betting decision based on the hand bin and the bot's pre-flop position. (fold, limp, call any, raise).

#### Flop, Turn, River:
Use a lightweight classifier on each villain to restrict the range of possible villain cards based on villain bets. 
Use this to restrict the villain range in the equity calculation. 
Calculate equity, and scale based on betting tendencies of opponents (i.e. versus loose opponents, effective equity might be higher, so call more often). 
Make betting decision based on the calculated equity of the hand.

- Runtime: Python 3.11 (pyenv / pyenv-virtualenv recommended).
- Performance: A pure-Python implementation of Cactus Kev's hand evaluator exists in `equity/hand_eval.py`. An optimization would be to use C++ to do these heavy integer calculations.
- Key modules:
    - `bot.py` — primary bot interface. Implement `bet(state: GameState) -> int` to return actions.
    - `equity/hand_eval.py` — Cactus Kev-style hand evaluator implemented in Python (fast integer-based evaluator).
    - `equity/equity_calc.py` — unified equity calculator (Monte Carlo sampling) used by decision logic.
    - `equity/tests/` — unit-style test scripts used to validate evaluator and equity calculations.

Design notes:
- The evaluator returns integer ranks where lower values indicate stronger hands (compatible with Cactus Kev ranking conventions).
- `equity/estimate_equity(...)` performs Monte Carlo sampling by randomly drawing hole cards for opponents from a provided villain pool. It supports preflop, flop, turn, and river by accepting 0–5 community cards.
- Tests are plain Python scripts (not pytest) and are executed directly; they print human-readable summaries and return non-zero exit codes on failures for CI compatibility.

Files of interest (quick):
- `bot.py` — main template and example decision code.
- `helpers.py` — small utility helpers used by the bot.
- `equity/hand_eval.py` — hand evaluator (pure Python implementation).
- `equity/equity_calc.py` — equity functions (Monte Carlo and deterministic helpers).
- `equity/tests/` — test harnesses: `test_hand_eval.py`, `test_equity_calc.py`, `test_bot_preflop.py`.

## Running & testing

Recommended, reproducible workflow (macOS / bash):

1. Install dependencies and create the virtualenv (recommended):

```bash
./setup.sh            # uses default Python version configured in script
# or explicitly:
./setup.sh 3.11.4
```

2. Activate the virtualenv (if not auto-activated by pyenv):

```bash
pyenv activate poker-cactus-3.11.4
```

4. Run the tests (scripts print summaries and return non-zero on failure):

```bash
python equity/tests/test_hand_eval.py
python equity/tests/test_equity_calc.py
python equity/tests/test_bot_preflop.py
```

Tips:
- Use the virtualenv Python to run tests to ensure pybind11 extension is discoverable.
- For faster, deterministic Monte Carlo runs, seed the RNG in tests by calling `random.seed(...)` before `estimate_equity`.

## Developer notes

- The equity functions expect `villain_range` to be a pool of cards (a list of card strings) — the Monte Carlo sampler picks hole cards from that pool each simulation. When you want to represent a set of possible opponent hole-card pairs, provide the union of their card sets or adapt the caller to supply explicit 2-card combos.
- Keep the public bot API (`bet(state: GameState) -> int`) stable. The tournament harness expects a single integer output for each invocation.
