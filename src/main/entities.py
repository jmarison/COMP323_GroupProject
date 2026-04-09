from __future__ import annotations
import pygame
import heapq
import math
import random
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


# --- Coin ---

COIN_RADIUS = 6
COIN_COLLECT_R = 28  #pickup radius
COL_COIN_OUTER = pygame.Color("#ffd700")
COL_COIN_INNER = pygame.Color("#fffacd")
COL_COIN_SHINE = pygame.Color("#ffffff")
 
class Coin:
    def __init__(self, x: float, y: float) -> None:
        self.pos   = pygame.Vector2(x, y)
        self.alive = True
        self._bob_t: float = 0.0
 
    def update(self, dt: float, player_rect: pygame.Rect, magnet_radius: float = 0.0, magnet_strength: float = 520.0) -> bool:
        if not self.alive:
            return False
        self._bob_t += dt
        player_pos = pygame.Vector2(player_rect.center)
        to_player = player_pos - self.pos
        dist = to_player.length()
        if magnet_radius > 0 and 0 < dist <= magnet_radius:
            self.pos += to_player.normalize() * magnet_strength * dt
            dist = self.pos.distance_to(player_pos)
        if dist <= COIN_COLLECT_R:
            self.alive = False
            return True
        return False
 
    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return
        bob = int(3 * pygame.math.Vector2(1, 0).rotate(self._bob_t * 150).y)
        cx  = int(self.pos.x)
        cy  = int(self.pos.y) + bob
        pygame.draw.circle(surface, COL_COIN_OUTER, (cx, cy), COIN_RADIUS)
        pygame.draw.circle(surface, COL_COIN_INNER, (cx, cy), COIN_RADIUS - 2)
        # tiny shine
        pygame.draw.circle(surface, COL_COIN_SHINE, (cx - 1, cy - 2), 1)



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

    def __init__(self, 
                 x: int, 
                 y: int, 
                 w: int, 
                 h: int,
                 hazard_type: str = HazardType.SPIKE,
                 damage: int = 10
                 ) -> None:
        self.rect  = pygame.Rect(x, y, w, h)
        self.hazard_type = hazard_type
        self.damage= damage

    def draw(self, surface: pygame.Surface) -> None:
        color = self.COLORS.get(self.hazard_type, pygame.Color("#ff0000"))
        pygame.draw.rect(surface, color, self.rect)
        # simple cross pattern to make spikes obvious
        if self.hazard_type == HazardType.SPIKE:
            cx, cy = self.rect.center
            pygame.draw.line(surface, pygame.Color("#ffffff"), (self.rect.left, self.rect.top), (self.rect.right, self.rect.bottom), 1)
            pygame.draw.line(surface, pygame.Color("#ffffff"), (self.rect.right, self.rect.top), (self.rect.left, self.rect.bottom), 1)

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
        (0, -1, 1.0), ( 0, 1, 1.0), (-1, 0, 1.0), ( 1, 0, 1.0),
        (-1, -1, 1.414), ( 1, -1, 1.414), (-1, 1, 1.414), ( 1, 1, 1.414),
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
    EnemyType.BASIC: {"hp": 70,  "speed": 100,  "damage": 15, "color": "#e74c3c", "size": (24, 24), "hitbox": (18, 18)},
    EnemyType.FAST:  {"hp": 40,  "speed": 125, "damage": 10,  "color": "#e67e22", "size": (18, 18), "hitbox": (16, 16)},
    EnemyType.HEAVY: {"hp": 120, "speed": 80,  "damage": 25, "color": "#8e44ad", "size": (36, 36), "hitbox": (26, 26)},
}

_REPATH_INTERVAL = 0.2 # how often enemy recalcs its path
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
        hw, hh = stats["hitbox"] # hw is hitbox width / hh is hitbox height
        self.hitbox = pygame.Rect(0, 0, hw, hh)
        self.hitbox.center = self.rect.center
        self.pos = pygame.Vector2(x, y)
        self.alive = True

        # --- pathfinding ---
        self._nav_grid: Optional[list[list[bool]]] = None
        self._path: list[tuple[int, int]]      = []
        self._repath_timer: float = 0.0

        self._spawn_delay: float = 0.2  # when player enters room there is a delay before enemies start moving to give time to react
        self._hit_flash: float= 0.0
        self._slow_mult: float = 1.0
        self._slow_timer: float = 0.0


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
        if self._hit_flash > 0:
            self._hit_flash -= dt
        if self._slow_timer > 0:
            self._slow_timer -= dt
            if self._slow_timer <= 0:
                self._slow_timer = 0.0
                self._slow_mult = 1.0

        direction = self._get_move_direction(dt, player_pos)
        if direction.length_squared() > 0:
            direction = direction.normalize()

        self.pos += direction * (self.speed * self._slow_mult) * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.hitbox.center = self.rect.center

        # if player miraculously gets in the wall = pushout 
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
        self.hitbox.center = self.rect.center



    def take_damage(self, amount: int) -> None:
        self.hp -= amount
        self._hit_flash = 0.12
        if self.hp <= 0:
            self.alive = False

    def apply_slow(self, multiplier: float, duration: float) -> None:
        self._slow_mult = max(0.1, min(self._slow_mult, multiplier))
        self._slow_timer = max(self._slow_timer, duration)
        
    def try_drop_coin(self, drop_chance: float = 0.33) -> "Coin | None":
        if random.random() < max(0.0, min(1.0, drop_chance)):
            return Coin(self.pos.x, self.pos.y)
        return None

    def draw(self, surface: pygame.Surface, debug: bool = False) -> None:
        if not self.alive:
            return
        pygame.draw.rect(surface, self.color, self.rect)
        # small HP bar
        bar_w = self.rect.width
        bar_h = 4
        bar_x = self.rect.left
        bar_y = self.rect.top - 6
        pygame.draw.rect(surface, pygame.Color("#333333"), (bar_x, bar_y, bar_w, bar_h))
        fill = int(bar_w * max(self.hp, 0) / _ENEMY_STATS[self.type]["hp"])
        pygame.draw.rect(surface, pygame.Color("#00cc44"), (bar_x, bar_y, fill, bar_h))
        if debug:
            pygame.draw.rect(surface, pygame.Color("#ff4400"), self.hitbox, 1)


# --- Bullet ---
_BULLET_COLORS  = {
    "default": pygame.Color("#ffe066"),
    "fast": pygame.Color("#88ddff"),
    "heavy": pygame.Color("#ff6644"),
    "shotgun": pygame.Color("#ffaa44"),
    "sniper": pygame.Color("#44ffcc"),
    "smg": pygame.Color("#cc88ff"),
}
class Bullet:
    def __init__(
            self,
            pos: pygame.Vector2,
            direction: pygame.Vector2,
            speed: float,
            damage: int,
            max_range: float,
            pierce: int = 0,
            scale: float = 1.0,
            color_key: str = "default"
    ) -> None:
        self.pos = pygame.Vector2(pos)
        self.direction = pygame.Vector2(direction)
        self.direction = direction.normalize() if direction.length_squared() > 0 else pygame.Vector2(1,0)
        self.speed = speed
        self.damage = damage
        self.max_range = max_range
        self.pierce = pierce
        self.alive = True
        self._traveled = 0.0
        self.radius = max(3, int(5 * scale))
        self.color = _BULLET_COLORS.get(color_key, _BULLET_COLORS["default"])
        self._hit_ids: set[int] = set()

    # --- update---
    def update(self, dt: float, walls: list) -> None:
        if not self.alive:
            return
        move = self.direction * self.speed * dt
        self.pos += move
        self._traveled += move.length()
        if self._traveled >= self.max_range:
            self.alive = False
            return
        bx, by = int(self.pos.x), int(self.pos.y)
        for wall in walls:
            if wall.rect.collidepoint(bx, by):
                self.alive = False
                return
    
    def try_hit(self, enemy: Enemy) -> bool:
        if not self.alive:
            return False
        eid = id(enemy)
        if eid in self._hit_ids:
            return False
        if not enemy.hitbox.collidepoint(int(self.pos.x), int(self.pos.y)):
            return False
        enemy.take_damage(self.damage)
        self._hit_ids.add(eid)
        if self.pierce > 0:
            self.pierce -= 1
        else:
            self.alive = False

        return True
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)



# --- Melee Hitbox ---
class MeleeHitbox:
    def __init__(
            self,
            origin: pygame.Vector2,
            direction: pygame.Vector2,
            radius: float,
            half_angle: float,
            damage: int,
            duration: float = 0.15
    ) -> None:
        self.origin = pygame.Vector2(origin)
        self.direction = direction.normalize() if direction.length_squared() > 0 else pygame.Vector2(1,0)
        self.radius = radius
        self.half_angle = half_angle
        self.damage = damage
        self.duration = duration
        self.alive = True
        self._timer = duration
        self._hit_ids: set[int] = set()
    
    def update(self, dt: float) -> None:
        if not self.alive:
            return
        self._timer -= dt
        if self._timer <= 0:
            self.alive = False

    def try_hit(self, enemy: Enemy) -> bool:
        if not self.alive: 
            return False
        eid = id(enemy)
        if eid in self._hit_ids:
            return False

        to_enemy = pygame.Vector2(enemy.hitbox.center) - self.origin
        dist = to_enemy.length()
        if dist > self.radius: 
            return False

        angle = math.degrees(
            math.acos(max(-1.0, min(1.0, self.direction.dot(to_enemy) / dist))) if dist > 0 else 0.0
        )
        if angle > self.half_angle: 
            return False

        enemy.take_damage(self.damage)
        self._hit_ids.add(eid)
        return True
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return
        alpha = int(180 * (self._timer / self.duration))
        r = int(self.radius)
        arc_surf = pygame.Surface((r*2 + 2, r*2 + 2), pygame.SRCALPHA)
        base_angle = math.degrees(math.atan2(-self.direction.y, self.direction.x))
        pygame.draw.arc(arc_surf, (255, 220, 100, alpha), pygame.Rect(1, 1, r*2, r*2),
                        math.radians(base_angle - self.half_angle),
                        math.radians(base_angle + self.half_angle),
                        max(1, int(r * 0.45)),
        )
        surface.blit(arc_surf, (int(self.origin.x) - r - 1, int(self.origin.y) - r - 1))

# --- Aura hitbox ---
class AuraHitbox:
    def __init__(
        self,
        center: pygame.Vector2,
        radius: float,
        damage: int,
        tick_rate: float,  # hits per second
        color: pygame.Color,
        pulse_speed: float = 2.0,   # how fast the ring pulses visually
    ) -> None:
        self.center = pygame.Vector2(center)
        self.radius = radius
        self.damage = damage
        self.tick_interval: float = 1.0 / max(tick_rate, 0.01)
        self.color = color
        self.pulse_speed = pulse_speed
        self.alive = True
 
        # per enemy cooldown maps id(enemy) and seconds until next hit
        self._enemy_timers: dict[int, float] = {}
        # visual pulse
        self._pulse_t: float = 0.0
 
    # --- called every frame by the player update ---
    def follow(self, new_center: pygame.Vector2) -> None:
        self.center = pygame.Vector2(new_center)
 
    def update(self, dt: float) -> None:
        if not self.alive:
            return
        self._pulse_t += dt * self.pulse_speed
 
        # tick down per enemy cooldowns
        to_delete = []
        for eid, timer in self._enemy_timers.items():
            new_timer = timer - dt
            if new_timer <= 0:
                to_delete.append(eid)
            else:
                self._enemy_timers[eid] = new_timer
        for eid in to_delete:
            del self._enemy_timers[eid]
 
    def try_hit(self, enemy: "Enemy") -> bool:
        if not self.alive:
            return False
        eid = id(enemy)
        if eid in self._enemy_timers:
            return False
 
        to_enemy = pygame.Vector2(enemy.hitbox.center) - self.center
        if to_enemy.length() > self.radius:
            return False
 
        enemy.take_damage(self.damage)
        self._enemy_timers[eid] = self.tick_interval
        return True
 
    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return
        r = int(self.radius)
        cx, cy = int(self.center.x), int(self.center.y)
 
        glow_size = r * 2 + 4
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        base_alpha = 28
        pygame.draw.circle(
            glow_surf,
            (*self.color[:3], base_alpha),
            (r + 2, r + 2),
            r,
        )
        surface.blit(glow_surf, (cx - r - 2, cy - r - 2))
 
        # pulsing ring
        pulse_offset = int(6 * math.sin(self._pulse_t * math.pi))
        pulse_r = max(4, r + pulse_offset)
        ring_alpha = int(120 + 80 * math.sin(self._pulse_t * math.pi))
        ring_surf = pygame.Surface((pulse_r * 2 + 4, pulse_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(
            ring_surf,
            (*self.color[:3], ring_alpha),
            (pulse_r + 2, pulse_r + 2),
            pulse_r,
            2,
        )
        surface.blit(ring_surf, (cx - pulse_r - 2, cy - pulse_r - 2))
        inner_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(
            inner_surf,
            (*self.color[:3], 180),
            (r + 2, r + 2),
            r,
            1,
        )
        surface.blit(inner_surf, (cx - r - 2, cy - r - 2))




