# Project Structure 
- once we pick a game idea, here we will document our project structure 

## Game.py

## Player.py
    - Attributes
        - MAX_WEAPONS : # of weapons player can hold
        - maxHealth : maximum player health
        - currHealth : player's current health
        - speed : player's movement speed
        - weaponInv: list of Weapons player has
        - currWeaponIndex: Index of the Weapon the player currently has in hand/is using
        - sprite: player sprite
        - pos: player's position
        - aim_dir : Vector for the direction the player is aiming in
    
    - Functions
        - _handle_movement
        - _handle_aim
        - _handle_weapon_switch
        - _cycle_weapons
        - _select_weapon
        - add_weapon
        - current_weapon -> Weapon
        - take_damage
        - heal
        - is_dead -> bool
        - _reset
        - _draw_aim_line

## Weapon.py
    - Attributes
        - name : Weapon's name
        - damage: How much HP each bullet does
        - range: Effective range of the weapon
        - fireRate: How fast the weapon fires
        - sprite: Sprite of weapon used for inhand of Player
        - maxAmmo: Maxiumum amount of ammo (-1 used for melee/infinte ammo weapons)
        - reserveClips: How many clips of ammo the gun has left
        - clipSize: how many bullets are in each clip
        - bullet: The bullet object the gun uses

    - Functions
        - reload
        - shoot
        - 

## Bullet.py
    - Attributes
        - bulletSpeed: how fast the bullet moves
        - bulletScale: effects the size of bullets
        - pierceCount: how many enemies the bullet pierces through 

    - Functions
        -

## Enemy.py

## Room.py

## RoomGeneration.py

## Main.py