from __future__ import annotations
"""
room_layouts.py
---------------
Each layout is a dict with three keys:
    "walls"   : list of (x, y, w, h)
    "hazards" : list of (x, y, w, h, hazard_type)
    "enemies" : list of (x, y, enemy_type)

Coordinates are written for a 960x540 room.
WALL_THICKNESS = 16, so usable interior starts at x=16, y=16.

Add as many layouts as you like — the dungeon generator will pick one at
random for each NORMAL room.
"""

from main.entities import HazardType, EnemyType

# Shorthand so layouts stay readable
S = HazardType.SPIKE
L = HazardType.LAVA
BA = EnemyType.BASIC
FA = EnemyType.FAST
HE = EnemyType.HEAVY

W, H = 960, 540   # screen dimensions


NORMAL_ROOM_LAYOUTS: list[dict] = [


    # Layout 0 
    
    {
        "walls": [
           # (200, 160, 80, 80),
            (680, 160, 80, 80),
            (200, 300, 80, 80),
            (680, 300, 80, 80),
        ],
        "hazards": [],
        "enemies": [
            (480, 200, BA),
            (480, 340, BA),
        ],
    },

    
    # Layout 1 
   
    {
        "walls": [
            (16,  140, 680, 40),   # top wall
            (16,  360, 680, 40),   # bottom wall
        ],
        "hazards": [
            #(200, 190, 40, 160, S),
            (340, 190, 40, 160, S),
            (480, 190, 40, 160, S),
        ],
        "enemies": [
            (820, 270, BA),
            (820, 200, FA),
            (820, 340, FA),
        ],
    },

   
    # Layout 2 

    {
        "walls": [
            (300, 160, 40, 220),   
            (620, 160, 40, 220),  
        ],
        "hazards": [
            (340, 200, 280, 140, L),
        ],
        "enemies": [
            (480, 420, HE),
        ],
    },

    # Layout 3 

    {
        "walls": [],
        "hazards": [],
        "enemies": [
            (100, 100, FA),
            (860, 100, FA),
            (100, 440, FA),
            (860, 440, FA),
            (480, 270, BA),
        ],
    },

    # Layout 4 
   
    {
        "walls": [
            (160, 100, 40, 200),
            (320, 240, 40, 200),
            (500, 100, 40, 180),
            (660, 220, 40, 200),
            (820, 100, 40, 160),
        ],
        "hazards": [
            (160, 420, 120, 32, S),
            (580, 380, 120, 32, S),
        ],
        "enemies": [
            (240, 270, BA),
            (600, 160, BA),
            (750, 400, HE),
        ],
    },


    # Layout 5

    {
        "walls": [
            (16, 200, 300, 30),
            (16, 310, 300, 30),
        ],
        "hazards": [
            (330, 160, 32, 220, S),
            (400, 160, 32, 220, S),
            (470, 160, 32, 220, S),
            (540, 160, 32, 220, S),
        ],
        "enemies": [
            (750, 180, FA),
            (750, 270, FA),
            (750, 360, FA),
        ],
    },
]