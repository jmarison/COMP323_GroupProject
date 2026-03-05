from __future__ import annotations
import pygame
import heapq
import math
from typing import Optional



# --- Wall ---


class Wall:

    COLOR = pygame.Color("#3a3a5c")

    def __init__(self, x: int, y: int, w: int, h: int) -> None:
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.COLOR, self.rect)

    def collides(self, rect: pygame.Rect) -> bool:
        return self.rect.colliderect(rect)


# --- Hazard ---


class HazardType:
    SPIKE = "spike"
    LAVA  = "lava"


class Hazard:
    #A floor hazard that damages the player on contact

    COLORS = {
        HazardType.SPIKE: pygame.Color("#b0b0b0"),
        HazardType.LAVA:  pygame.Color("#ff4500"),
    }

    def __init__(self, x: int, y: int, w: int, h: int,
                 hazard_type: str = HazardType.SPIKE,
                 damage: int = 10) -> None:
        self.rect        = pygame.Rect(x, y, w, h)
        self.hazard_type = hazard_type
        self.damage      = damage

    def draw(self, surface: pygame.Surface) -> None:
        color = self.COLORS.get(self.hazard_type, pygame.Color("#ff0000"))
        pygame.draw.rect(surface, color, self.rect)
        # simple cross pattern to make spikes obvious
        if self.hazard_type == HazardType.SPIKE:
            cx, cy = self.rect.center
            pygame.draw.line(surface, pygame.Color("#ffffff"),
                             (self.rect.left, self.rect.top),
                             (self.rect.right, self.rect.bottom), 1)
            pygame.draw.line(surface, pygame.Color("#ffffff"),
                             (self.rect.right, self.rect.top),
                             (self.rect.left, self.rect.bottom), 1)

    def collides(self, rect: pygame.Rect) -> bool:
        return self.rect.colliderect(rect)
# --- Nav Grid / Pathfinding ---

# must match WALL_THICKNESS
# dont change
CELL_SIZE = 16

def _build_nav_grid(screen_w: int, screen_h: int, walls: list[Wall], agent_w: int, agent_h: int) -> list[list[bool]]:
    # returns true if impassable
    cols = math.ceil(screen_w / CELL_SIZE)
    rows = math.ceil(screen_h / CELL_SIZE)
    blocked = [[False] * cols for _ in range(rows)]

    half_w = agent_w //2
    half_h = agent_h // 2

    for row in range(rows):
        for col in range(cols):
            cx = col * CELL_SIZE + CELL_SIZE // 2
            cy = row * CELL_SIZE + CELL_SIZE // 2
            agent_rect = pygame.Rect(cx - half_w, cy - half_h, agent_w, agent_h)
            for wall in walls:
                if wall.rect.colliderect(agent_rect):
                    blocked[row][col] = True
                    break
    return blocked

def _world_to_cell(x: float, y: float) -> tuple[int, int]:
    return int(x // CELL_SIZE), int(y // CELL_SIZE)   


def _cell_to_world(col: int, row: int) -> pygame.Vector2:
    return pygame.Vector2(col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2)

def _astar(start_col:int, start_row:int, goal_col: int, goal_row: int, blocked: list[list[bool]],) -> list[tuple[int, int]]:

    rows = len(blocked)
    cols = len(blocked[0]) if rows else 0

    def h(c: int, r: int) -> float:
        return abs(c - goal_col) + abs(r - goal_row)

    open_heap: list[tuple[float, int, int]] = []
    heapq.heappush(open_heap, (h(start_col, start_row), start_col, start_row))

    came_from: dict[tuple[int, int], Optional[tuple[int, int]]] = {
        (start_col, start_row): None
    }
    g_cost: dict[tuple[int, int], float] = {(start_col, start_row): 0.0}

    DIRS = [
        ( 0, -1, 1.0), ( 0,  1, 1.0), (-1,  0, 1.0), ( 1,  0, 1.0),
        (-1, -1, 1.414), ( 1, -1, 1.414), (-1,  1, 1.414), ( 1,  1, 1.414),
    ]

    while open_heap:
        _, col, row = heapq.heappop(open_heap)

        if (col, row) == (goal_col, goal_row):
            path = []
            node: Optional[tuple[int, int]] = (col, row)
            while node is not None:
                path.append(node)
                node = came_from[node]
            path.reverse()
            return path[1:]  

        for dc, dr, cost in DIRS:
            nc, nr = col + dc, row + dr
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if blocked[nr][nc]:
                continue
            if dc != 0 and dr != 0:
                if blocked[row][nc] or blocked[nr][col]:
                    continue
            ng = g_cost[(col, row)] + cost
            if ng < g_cost.get((nc, nr), float("inf")):
                g_cost[(nc, nr)] = ng
                came_from[(nc, nr)] = (col, row)
                heapq.heappush(open_heap, (ng + h(nc, nr), nc, nr))

    return []   # no path found


# --- Enemy ---


class EnemyType:
    BASIC  = "basic"
    FAST   = "fast"
    HEAVY  = "heavy"


_ENEMY_STATS = {
    EnemyType.BASIC: {"hp": 40,  "speed": 135,  "damage": 10, "color": "#e74c3c", "size": (24, 24)},
    EnemyType.FAST:  {"hp": 20,  "speed": 200, "damage": 5,  "color": "#e67e22", "size": (18, 18)},
    EnemyType.HEAVY: {"hp": 120, "speed": 80,  "damage": 25, "color": "#8e44ad", "size": (36, 36)},
}
# this is how often the enemy recalcs its path
_REPATH_INTERVAL = 0.4
_DIRECT_CHASE_DIST = CELL_SIZE * 2

class Enemy:

    def __init__(self, x: int, y: int, enemy_type: str = EnemyType.BASIC) -> None:
        stats  = _ENEMY_STATS[enemy_type]
        self.type = enemy_type
        self.hp = stats["hp"]
        self.speed = stats["speed"]
        self.damage = stats["damage"]
        self.color = pygame.Color(stats["color"])
        w, h = stats["size"]
        self.rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
        self.pos = pygame.Vector2(x, y)
        self.alive = True

        # --- pathfinding ---
        self._nav_grid: Optional[list[list[bool]]] = None
        self._path: list[tuple[int, int]]      = []
        self._repath_timer: float = 0.0

        # when player enters room there is a delay before enemies start moving to give time to react
        self._spawn_delay: float = 0.2

    # called by Room AFTER the layout is built
    def set_nav_grid(self, grid: list[list[bool]]) -> None:
        self._nav_grid = grid
        self._path = []
        self._repath_timer = 0.0

    def update(self, dt: float, player_pos: pygame.Vector2, walls: Optional[list[Wall]] = None) -> None:
        if not self.alive:
            return
        
        if self._spawn_delay > 0:
            self._spawn_delay -= dt
            return
        
        direction = self._get_move_direction(dt, player_pos)

        if direction.length_squared() > 0:
            direction = direction.normalize()

        self.pos += direction * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        # wall pushout 
        if walls:
            self._resolve_wall_collisions(walls)

    def _get_move_direction(self, dt:float, player_pos: pygame.Vector2) -> pygame.Vector2:
        to_player = player_pos - self.pos
        dist = to_player.length()

        if self._nav_grid is None or dist <= _DIRECT_CHASE_DIST:
            return to_player.normalize() if dist > 0 else pygame.Vector2(0, 0)

        # if cant find anything after a while, start over
        self._repath_timer -= dt
        if self._repath_timer <= 0 or not self._path:
            self._repath_timer = _REPATH_INTERVAL
            sc, sr = _world_to_cell(self.pos.x, self.pos.y)
            gc, gr = _world_to_cell(player_pos.x, player_pos.y)
            self._path = _astar(sc, sr, gc, gr, self._nav_grid)

        # move along path
        if self._path:
            next_col, next_row = self._path[0]
            target = _cell_to_world(next_col, next_row)
            to_target = target - self.pos
            if to_target.length() < CELL_SIZE * 0.6:
                self._path.pop(0)
                if self._path:
                    next_col, next_row = self._path[0]
                    target = _cell_to_world(next_col, next_row)
                    to_target = target - self.pos
            return to_target
        return to_player
    
    def _resolve_wall_collisions(self, walls: list[Wall]) -> None:
        for wall in walls:
            if not self.rect.colliderect(wall.rect):
                continue
            dx_left = self.rect.right - wall.rect.left
            dx_right = wall.rect.right - self.rect.left
            dy_up = self.rect.bottom - wall.rect.top
            dy_down = wall.rect.bottom - self.rect.top
            min_x = dx_left if dx_left < dx_right else -dx_right
            min_y = dy_up  if dy_up  < dy_down  else -dy_down
            if abs(min_x) < abs(min_y):
                self.rect.x -= min_x
            else:
                self.rect.y -= min_y
            self.pos.x = self.rect.centerx
            self.pos.y = self.rect.centery




    def take_damage(self, amount: int) -> None:
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return
        pygame.draw.rect(surface, self.color, self.rect)
        # small HP bar
        bar_w = self.rect.width
        bar_h = 4
        bar_x = self.rect.left
        bar_y = self.rect.top - 6
        pygame.draw.rect(surface, pygame.Color("#333333"),
                         (bar_x, bar_y, bar_w, bar_h))
        fill = int(bar_w * max(self.hp, 0) / _ENEMY_STATS[self.type]["hp"])
        pygame.draw.rect(surface, pygame.Color("#00cc44"),
                         (bar_x, bar_y, fill, bar_h))

