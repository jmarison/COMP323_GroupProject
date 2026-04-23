# [Consumed with Greed] — Postmortem

**Team:** [Money Makers] </br>
**Members:** [Jacob Marison]</br>
**Date:** [4.23.26]</br>
**Repo:** https://github.com/jmarison/COMP323_GroupProject.git</br>

---

## What went well

### 1. [Specific thing that worked]

The implementation of a grid-based DungeonGenerator using Breadth-First Search (BFS) to calculate room distances worked exceptionally well. This allowed for a guaranteed path from the Start room to the Boss room while ensuring "special" rooms like Weapon Shops and item shops were placed at appropriate branch distances. The result is a high level of replayability where the layout feels logical rather than purely random.

### 2. [Specific thing that worked]

Changing enemy stats and item costs from hardcoded values into a floor-based scaling system was a major success. By using a price_multiplier and level-based modifiers in entities.py, the game naturally increases in difficulty as the player descends. This architecture made it easy to tune the entire game’s balance by changing just a few variables.


## What went wrong

### 1. [Specific problem]

I used the wrong project structure (had main.py in /src/ and the rest in a main folder inside /src/) for a long time of development. Having to go back and change all my imports and file paths was defintely a pain, but was more busy work than difficult. Also used built in fonts so going back and changing that was similar. 

### 2. [Specific problem]

I initially planned for a complex weapon reload system and multiple ammo types, which resulted in a messy weapon.py that was difficult to debug. This focus on "feature quantity" caused me to neglect the Boss logic until late in the project, leading to a critical crash during the Boss's triple shot attack. I wanted to make the boss more complex but just did not have the time for it after fixing a large number of issues. 


## What we would change

I think the player class became too heavy on content since it also handled a large number of item interactions. I should have made a dedicated item handler that would deal with the modifiers, etc. As of writing this, it is 570+ lines which without items would probably be down in the 300's and much easier to follow. 

## Iteration evidence

### Before

Some rooms were unreactable on entering that would result in unavoidable damage.

### Change

Implemented a grace period where neither the player or enemies can move to prevent being hit during room transitions. Also adjusted a large number of rooms to prevent enemies from being placed near the doors. 

### After

Initially 2 different testers reported the unfairness of certain rooms, but this changed to only a single report about the boss room if the door is placed at the North entrance. 

