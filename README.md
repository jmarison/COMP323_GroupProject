# Consumed With Greed
Consumed with Greed is a top-down dungeon crawler where you play as an adventurer descending through procedural floors to defeat a powerful Boss. You must fight through rooms of enemies, collect coins, and strategically purchase items and weapons from pedestals to scale your power for the increasingly difficult dungeons.


## Setup
```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the game
python main.py
```

## Controls

| Action | Key |
| --- | --- |
| Move | WASD |
| Aim | Arrow Keys |
| Swap Weapons | E or Q |
| Weapon Slot 1 | 1 |
| Weapon Slot 2 | 2 |
| Pause/Resume | P |
| Quit | Escape |
| Start game | Enter or Space (title screen) |
| New dungeon | Y |


## Known issues

- Aura weapons can attack faster than intended by quick switching between weapons
- Enemy pathing, especially heavy enemies, can occasionally get snagged on corner

## Credits

- Built with [Pygame](https://www.pygame.org/) (LGPL)
- Player sprite from Snoblin (https://snoblin.itch.io/pixel-rpg-free-npc)
- Music tracks from AleXZavesa (https://pixabay.com/music/)
