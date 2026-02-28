from __future__ import annotations
import pygame


# ---------------------------------------------------------------------------
# Wall
# ---------------------------------------------------------------------------

class Wall:

    COLOR = pygame.Color("#3a3a5c")

    def __init__(self, x: int, y: int, w: int, h: int) -> None:
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.COLOR, self.rect)

    def collides(self, rect: pygame.Rect) -> bool:
        return self.rect.colliderect(rect)


# ---------------------------------------------------------------------------
# Hazard
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Enemy
# ---------------------------------------------------------------------------

class EnemyType:
    BASIC  = "basic"
    FAST   = "fast"
    HEAVY  = "heavy"


_ENEMY_STATS = {
    EnemyType.BASIC: {"hp": 40,  "speed": 80,  "damage": 10, "color": "#e74c3c", "size": (24, 24)},
    EnemyType.FAST:  {"hp": 20,  "speed": 160, "damage": 5,  "color": "#e67e22", "size": (18, 18)},
    EnemyType.HEAVY: {"hp": 120, "speed": 40,  "damage": 25, "color": "#8e44ad", "size": (36, 36)},
}


class Enemy:

    def __init__(self, x: int, y: int, enemy_type: str = EnemyType.BASIC) -> None:
        stats      = _ENEMY_STATS[enemy_type]
        self.type  = enemy_type
        self.hp    = stats["hp"]
        self.speed = stats["speed"]
        self.damage = stats["damage"]
        self.color  = pygame.Color(stats["color"])
        w, h        = stats["size"]
        self.rect   = pygame.Rect(x - w // 2, y - h // 2, w, h)
        self.pos    = pygame.Vector2(x, y)
        self.alive  = True

    def update(self, dt: float, player_pos: pygame.Vector2) -> None:
        if not self.alive:
            return
        direction = player_pos - self.pos
        if direction.length_squared() > 0:
            direction = direction.normalize()
        self.pos  += direction * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

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