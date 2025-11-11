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

This project includes a **polyglot build system** supporting both Python and C++ (via pybind11) for performance-critical components like hand equity calculation.

### Initial Setup

Run the setup script to initialize the virtualenv, install dependencies, and build the C++ extension:

```bash
./setup.sh
```

Or specify a Python version:
```bash
./setup.sh 3.11.4
```

This script will:
1. Install pyenv and pyenv-virtualenv (if needed)
2. Install the specified Python version
3. Create a virtual environment named `poker-cactus-<version>`
4. Install Python dependencies (pybind11, setuptools, wheel)
5. Build the C++ extension module via CMake
6. Write `.python-version` to auto-activate the virtualenv

### Activating the Virtual Environment

After setup, the virtualenv will be automatically activated when you enter the project directory (thanks to `.python-version`). To manually activate:

```bash
# If you're using bash/zsh with pyenv already initialized:
pyenv activate poker-cactus-3.11.4

# Or, if pyenv is not in your shell:
eval "$(pyenv init --path)" && eval "$(pyenv virtualenv-init -)" && pyenv activate poker-cactus-3.11.4
```

### Building the C++ Extension

If you need to rebuild the C++ module after modifying `cpp/module.cpp`:

```bash
cd build
cmake -S ../cpp -B . -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=$(which python)
cmake --build . --config Release
cd ..
```

**Note:** The build requires the virtualenv's Python interpreter. Make sure you've activated the virtualenv before building, otherwise CMake may use the system Python and fail to find pybind11.

### Troubleshooting: "Could not find pybind11"

If CMake cannot find pybind11 despite it being installed:

1. **Ensure pybind11 is installed in the active virtualenv:**
   ```bash
   pip list | grep pybind11
   ```
   If missing:
   ```bash
   pip install pybind11
   ```

2. **Use the correct Python interpreter in CMake:**
   ```bash
   which python  # Get the path to the active Python
   cmake -S ../cpp -B build -DPython3_EXECUTABLE=<path from above>
   ```

3. **Clear CMake cache and try again:**
   ```bash
   rm -rf build/CMakeCache.txt build/CMakeFiles
   cmake -S ../cpp -B build -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=$(which python)
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
