# Developer Log 
This document contains the a record of logs that Jacob Marison and Gabe Lazatin

## February 13, 2026 - Jacob Marison
 - Inital project setup 

## February 23, 2026 - Jacob Marison - Initial-Player-Design
 - Initial Documentation work
 - Basic player implemented with placeholder sprite
 - Player movement and aiming

 ## February 24, 2026 - Jacob Marison - Dungeon-Generation
 - <h3>Procedural Dungeon Generation</h3>
    - Dungeon is created on an 8x8 grid</br>
    - all dungeons must have a spawn room, boss room, and a mini game room alongside the varying amount of normal enemy rooms</br>
    - the boss room is a leaflet meaning it will only have a single door entrance</br>
    - the boss room is also the furthest node (using BFS) from the spawn room</br>
    - the mini-game room serves as a semi-safe room where the player can attempt challenges to be rewarded with an item or weapon</br>
    - F1 can be used to toggle the dungeon debug menu which shows Room Id, Room type, and door hitboxes</br>
    - Doors are used to travel between rooms of the dungeon. They are triggered by the player walking over an invisible rectangle by the door</br>
- <h3>Title Screen</h3>
    - Rudimentary title screen implemented</br>
    - Start/Quit buttons</br>
    - Settings is WIP</br>
- <h3>Future plans:</h3>
    - Design 2-3 basic weapons</br> 
    - Design 2-3 basic enemies (one that just does simple contact damage and one that shoots a basic slow projectile) </br>
    - Give each room a total_enemy_credit which is a number representing how many enemies will spawn in a room. Each enemy will have a corresponding enemy_credit which represents how much a single enemy type is worth. So stronger enemies will have a higher enemy_credit resulting in fewer total enemies spawning in the room but the enemies themselves are stronger. </br>
    - Could also add an increased difficulty by bumping the total_enemy_credit up</br>
    - Settings menu with rebindable keybinds</br>

 