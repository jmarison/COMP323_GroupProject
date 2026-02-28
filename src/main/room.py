from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from main.entities import Wall, Hazard, Enemy
import pygame


class RoomType(Enum):
    NORMAL    = "normal"
    START     = "start"
    BOSS      = "boss"
    MINI_GAME = "mini_game"


class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST  = "east"
    WEST  = "west"

    def opposite(self) -> "Direction":
        return {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST:  Direction.WEST,
            Direction.WEST:  Direction.EAST,
        }[self]


ROOM_W, ROOM_H     = 960, 540        # normal room pixel size (matches screen)
BOSS_W, BOSS_H     = 960, 540        # boss room is same screen size; we just
                                      # mark it visually differently

DOOR_SIZE          = 64              # width/height of the door opening
LOADING_ZONE_DEPTH = 48              # how deep the trigger rect is
WALL_THICKNESS     = 16

# Colors
COL_FLOOR_NORMAL   = pygame.Color("#1a1a2e")
COL_FLOOR_START    = pygame.Color("#16213e")
COL_FLOOR_BOSS     = pygame.Color("#2e0a0a")
COL_FLOOR_MINI     = pygame.Color("#0a2e1a")
COL_WALL           = pygame.Color("#3a3a5c")
COL_DOOR_OPEN      = pygame.Color("#c8a96e")
COL_DOOR_FRAME     = pygame.Color("#7a5c2e")
COL_LOADING_ZONE   = pygame.Color("#ffffff")   # debug so alpha low
COL_LABEL          = pygame.Color("#ffffff")


@dataclass
class Door:
    direction: Direction
    target_room_id: int               # id of the room this door leads to
    rect: pygame.Rect = field(init=False)
    loading_zone: pygame.Rect = field(init=False)

    def __post_init__(self) -> None:
        self.rect         = pygame.Rect(0, 0, 0, 0)
        self.loading_zone = pygame.Rect(0, 0, 0, 0)

    def build_rects(self, screen_w: int, screen_h: int) -> None:
        cx = screen_w // 2
        cy = screen_h // 2
        ds = DOOR_SIZE
        lz = LOADING_ZONE_DEPTH
        wt = WALL_THICKNESS

        if self.direction == Direction.NORTH:
            self.rect = pygame.Rect(cx - ds // 2, 0,ds, wt)
            self.loading_zone = pygame.Rect(cx - ds // 2, 0, ds, lz)
        elif self.direction == Direction.SOUTH:
            self.rect = pygame.Rect(cx - ds // 2, screen_h - wt, ds, wt)
            self.loading_zone = pygame.Rect(cx - ds // 2, screen_h - lz, ds, lz)
        elif self.direction == Direction.WEST:
            self.rect = pygame.Rect(0,cy - ds // 2, wt, ds)
            self.loading_zone = pygame.Rect(0,cy - ds // 2, lz, ds)
        elif self.direction == Direction.EAST:
            self.rect = pygame.Rect(screen_w - wt, cy - ds // 2, wt, ds)
            self.loading_zone = pygame.Rect(screen_w - lz, cy - ds // 2, lz, ds)


class Room:
    def __init__(
        self,
        room_id:   int,
        room_type: RoomType,
        grid_pos:  tuple[int, int],
        screen_w:  int = ROOM_W,
        screen_h:  int = ROOM_H,
        walls:     list[Wall]   = None,
        hazards:   list[Hazard] = None,
        enemies:   list[Enemy]  = None,
    ) -> None:
        self.id        = room_id
        self.type      = room_type
        self.grid_pos  = grid_pos
        self.screen_w  = screen_w
        self.screen_h  = screen_h

        self.walls   : list[Wall]   = walls   or []
        self.hazards : list[Hazard] = hazards or []
        self.enemies : list[Enemy]  = enemies or []

        self.doors: dict[Direction, Door] = {}
        self._surface: Optional[pygame.Surface] = None

        
    def add_door(self, direction: Direction, target_room_id: int) -> None:
        door = Door(direction=direction, target_room_id=target_room_id)
        door.build_rects(self.screen_w, self.screen_h)
        self.doors[direction] = door

    def check_transition(self, player_rect: pygame.Rect) -> Optional[tuple[Direction, int]]:
       
        #Returns (direction, target_room_id) if the player's rect overlaps any
        #loading zone, otherwise None
      
        for direction, door in self.doors.items():
            if player_rect.colliderect(door.loading_zone):
                return direction, door.target_room_id
        return None

    def update(self, dt: float, player) -> None:
        player_pos = pygame.Vector2(player.rect.center)
        for enemy in self.enemies:
            enemy.update(dt, player_pos)

        for hazard in self.hazards:
            if hazard.collides(player.rect):
                player.take_damage(hazard.damage)


    def _build_surface(self) -> pygame.Surface:
        surf = pygame.Surface((self.screen_w, self.screen_h))
        floor_col = {
            RoomType.NORMAL:    COL_FLOOR_NORMAL,
            RoomType.START:     COL_FLOOR_START,
            RoomType.BOSS:      COL_FLOOR_BOSS,
            RoomType.MINI_GAME: COL_FLOOR_MINI,
        }[self.type]
        surf.fill(floor_col)

        wt = WALL_THICKNESS
        wall_rects = [
            pygame.Rect(0,0,self.screen_w, wt),   # top
            pygame.Rect(0,self.screen_h - wt,self.screen_w, wt),   # bottom
            pygame.Rect(0,0,wt,self.screen_h),  # left
            pygame.Rect(self.screen_w - wt,0, wt,self.screen_h),  # right
        ]
        for r in wall_rects:
            pygame.draw.rect(surf, COL_WALL, r)

        for wall in self.walls:
                    wall.draw(surf)
      
        for door in self.doors.values():
            pygame.draw.rect(surf, floor_col,    door.rect)  # erase wall
            pygame.draw.rect(surf, COL_DOOR_FRAME, door.rect, 2)    # frame outline

        if pygame.font.get_init():
            font  = pygame.font.SysFont(None, 28)
            label = font.render(f"[{self.type.value.upper()}]  id:{self.id}", True, COL_LABEL)
            surf.blit(label, (wt + 8, wt + 8))

        return surf

    def draw(self, surface: pygame.Surface, debug: bool = False) -> None:
       
        if self._surface is None:
            self._surface = self._build_surface()
        surface.blit(self._surface, (0, 0))

        for hazard in self.hazards:
            hazard.draw(surface)
        for enemy in self.enemies:
            enemy.draw(surface)

        if debug:
            overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            for door in self.doors.values():
                pygame.draw.rect(overlay, (*COL_LOADING_ZONE[:3], 40), door.loading_zone)
                pygame.draw.rect(overlay, (*COL_LOADING_ZONE[:3], 120), door.loading_zone, 2)
            surface.blit(overlay, (0, 0))

    def invalidate_surface(self) -> None:
        self._surface = None
        
    #  Helpers                                                                 
    def __repr__(self) -> str:
        doors = [d.name for d in self.doors]
        return (f"Room(id={self.id}, type={self.type.value}, "
                f"grid={self.grid_pos}, doors={doors}, "
                f"walls={len(self.walls)}, hazards={len(self.hazards)}, "
                f"enemies={len(self.enemies)})")