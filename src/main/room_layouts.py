from __future__ import annotations
"""
Each layout is a dict with three keys:
    "walls"   : list of (x, y, w, h)
    "hazards" : list of (x, y, w, h, hazard_type)
    "enemies" : list of (x, y, enemy_type)

Coordinates are written for a 960x540 room.
WALL_THICKNESS = 16, so usable interior starts at x=16, y=16.
"""

from main.entities import HazardType, EnemyType
#hazard types
S = HazardType.SPIKE
L = HazardType.LAVA
#enemy types
BA = EnemyType.BASIC
FA = EnemyType.FAST
HE = EnemyType.HEAVY

W, H = 960, 540   # screen dimensions


NORMAL_ROOM_LAYOUTS: list[dict] = [


    # Layout 0 

    {
        "walls": [
            (680, 150, 80, 80),
            (200, 310, 80, 80),
            (200, 150, 80, 80),
            (680, 310, 80, 80),
        ],
        "hazards": [],
        "enemies": [
            (480, 200, HE),
            (480, 340, HE),
        ],
    },


    # Layout 1 
   
    {
        "walls": [
            (W // 4,  140, W // 2, 40),   # top wall
            (W // 4,  360, W // 2, 40),   # bottom wall
        ],
        "hazards": [

        ],
        "enemies": [
            (W - 100, H - 100, BA),
            (W//2,  H//2, BA),
            (100, 100, BA),
            (W//2 + 75, H//2, FA),
            (W//2 - 75, H//2, FA),
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
            (480, 150, HE),
            (480, 390, HE),
        ],
    },

    # Layout 3 
    #good
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
            (150, 100, 100, 100),
            (W - 250,  H - 200, 100, 100),
            (150, H - 200, 100, 100),
            (W - 250, 100, 100, 100),
        ],
        "hazards": [
            (250, 125, 175, 50, S),
            (535, 125, 175, 50, S),
            (250, H - 175, 175, 50, S),
            (535, H - 175, 175, 50, S),
        ],
        "enemies": [
            (240, 270, BA),
            (W - 240, 270, BA),
            (W // 2, H // 2 , HE),
        ],
    },
 

    # Layout 5

    {
        "walls": [
            (16, 200, 300, 30),
            (16, 310, 300, 30),
        ],
        "hazards": [
            #(330, 160, 32, 220, S),
            #(400, 160, 32, 220, S),
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