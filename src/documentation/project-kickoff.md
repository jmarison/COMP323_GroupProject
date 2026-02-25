# Team name
## Project Title
By Jacob Marison and Gabe Lazatin

## Pitch
- 

## Player and problem statement
- Our goal is to design a 2D top-down modular, scalable roguelite dungeon crawler. Our primary audience is towards fans of dungeon style games like the Legend of Zelda and the Binding of Isaac. 

## Core goals and top tasks
- Our core goal is replayability. Through generation of dungeons, random weapons and items, and varying enemies/bosses the player will have a new experience with each playthrough. Designed to be around 15 minute long and geared towards players who enjoy optimization (Min/Maxxing). 
- Player tasks
    - Clear rooms by killing all enemies and avoiding their attacks
    - Collect weapons and items to become stronger
    - Become strong enough to beat the dungeon boss
    - 

## Initial Specification
    - Core Features (MVP)
        - Modular weapons system
        - Stackable/Scalable items that impact either the player, enemies, or the player's weapon
    - Non-goals
        - 
    - Contraints
        - Platform : Desktop
        - Input Method: Keyboard
        - Time contraints: amount of enemies, items, bosses, room layouts, and weapons
        

## MVP definition
    - Loop:
        - Player ventures through a dungeon searching for items and weapons to become stronger and beat enemies and boss
        - Player enters room, enemies spawn and attack player, if room has multiple waves they spawn after all enemies defeated. Upon all waves cleared the doors unlock and player is allowed to continue forward or backward
    - Win/lose condition
        - Win: Clearing floor boss (potentiallty multiple times through)
        - Lose: Player loses all health
    - Restart Path: 
        - Player starts over with no items on a newly generated dungeon


## Translate gameplay into event > state > render
    

## State model (draft)
    - Game
        - title
        - paused
        - gameover
        - playing
    - Player
        -
    - Boss
        - standard
        - enraged (below half health, moves faster and does more damage)
    
## HUD plan (draft)

## First 3 commits (planned)

## Contributions to G1


