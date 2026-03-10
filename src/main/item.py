from __future__ import annotations
import pygame
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Optional



# Effects
class EffectType(Enum):
    # Player stats
    MOVE_SPEED = auto()
    MAX_HEALTH  = auto()
    PLAYER_SIZE = auto()
    # Weapon / combat
    FIRE_RATE  = auto()
    BULLET_SPEED  = auto()
    BULLET_DAMAGE = auto()
    BULLET_SIZE = auto()
    MULTISHOT  = auto()
    PIERCING  = auto()
    # Enemy modifiers
    ENEMY_SLOW      = auto()
    ENEMY_WEAKNESS  = auto()
    # Utility / special
    HEAL_ON_KILL    = auto()
    SHIELD          = auto()
    MAGNET          = auto()


@dataclass
class ItemEffect:
    effect_type: EffectType
    value: float          
    is_multiplier: bool = False   # True : multiply stat by value
                                  # False : add value to stat



# Item


class Item:
    PLACEHOLDER_SIZE = (32, 32)

    def __init__(
        self,
        name:        str,
        tier:        int,
        description: str,
        effects:     list[ItemEffect],
        color:       pygame.Color | None = None,   # placeholder tint
        sprite:      pygame.Surface | None = None,
    ) -> None:
        assert len(description.split()) <= 10, \
            f"Item '{name}' description exceeds 10 words: '{description}'"

        self.name        = name
        self.tier        = tier          # 1 = common … 3 = rare
        self.description = description
        self.effects     = effects
        self._sprite     = sprite
        self._color      = color or pygame.Color("#aaaaaa")

    # --- Sprite ---

    @property
    def sprite(self) -> pygame.Surface:
        """Return the sprite, generating a placeholder if none is set."""
        if self._sprite is None:
            surf = pygame.Surface(self.PLACEHOLDER_SIZE, pygame.SRCALPHA)
            surf.fill(self._color)
            # draw a thin white border so items are distinguishable
            pygame.draw.rect(surf, pygame.Color("#ffffff"),
                             surf.get_rect(), 2)
            self._sprite = surf
        return self._sprite

    def set_sprite(self, surface: pygame.Surface) -> None:
        self._sprite = surface

    # --- Applying effects (convenience helpers) ---

    def get_effects_of(self, effect_type: EffectType) -> list[ItemEffect]:
        return [e for e in self.effects if e.effect_type == effect_type]

    def __repr__(self) -> str:
        return f"Item({self.name!r}, tier={self.tier})"



# Items

# Tier guide:
#   1 – common, small bonus
#   2 – uncommon, meaningful bonus
#   3 – rare, strong / build-defining


ITEM_CATALOGUE: list[Item] = [

    # ── Player-stat items 

    Item(
        name        = "Worn Boots",
        tier        = 1,
        description = "Slightly increases your movement speed.",
        effects     = [ItemEffect(EffectType.MOVE_SPEED, 60)],
        color       = pygame.Color("#8B6914"),
    ),
    Item(
        name        = "Rocket Shoes",
        tier        = 3,
        description = "Greatly boosts movement speed.",
        effects     = [ItemEffect(EffectType.MOVE_SPEED, 180)],
        color       = pygame.Color("#ff6600"),
    ),
    Item(
        name        = "Iron Heart",
        tier        = 2,
        description = "Permanently increases your maximum health pool.",
        effects     = [ItemEffect(EffectType.MAX_HEALTH, 50)],
        color       = pygame.Color("#cc2222"),
    ),
    Item(
        name        = "Elixir of Giants",
        tier        = 3,
        description = "Doubles your size and maximum health.",
        effects     = [
            ItemEffect(EffectType.PLAYER_SIZE,  2.0, is_multiplier=True),
            ItemEffect(EffectType.MAX_HEALTH,  100),
        ],
        color       = pygame.Color("#44cc44"),
    ),
    Item(
        name        = "Pocket Mirror",
        tier        = 2,
        description = "Shrinks you, making you harder to hit.",
        effects     = [ItemEffect(EffectType.PLAYER_SIZE, 0.65, is_multiplier=True)],
        color       = pygame.Color("#aaddff"),
    ),

    # ── Weapon / combat items 

    Item(
        name        = "Hair Trigger",
        tier        = 1,
        description = "Reduces delay between shots slightly.",
        effects     = [ItemEffect(EffectType.FIRE_RATE, -0.05)],
        color       = pygame.Color("#ffdd44"),
    ),
    Item(
        name        = "Overclock",
        tier        = 3,
        description = "Massively increases fire rate.",
        effects     = [ItemEffect(EffectType.FIRE_RATE, 0.5, is_multiplier=True)],
        color       = pygame.Color("#ff4488"),
    ),
    Item(
        name        = "Lead Rounds",
        tier        = 1,
        description = "Bullets deal more damage.",
        effects     = [ItemEffect(EffectType.BULLET_DAMAGE, 5)],
        color       = pygame.Color("#888888"),
    ),
    Item(
        name        = "Explosive Tips",
        tier        = 3,
        description = "Bullets deal greatly increased damage.",
        effects     = [ItemEffect(EffectType.BULLET_DAMAGE, 20)],
        color       = pygame.Color("#ff8800"),
    ),
    Item(
        name        = "Tailwind",
        tier        = 1,
        description = "Bullets travel faster.",
        effects     = [ItemEffect(EffectType.BULLET_SPEED, 100)],
        color       = pygame.Color("#88ddff"),
    ),
    Item(
        name        = "Cannonball",
        tier        = 2,
        description = "Larger bullets that deal extra damage.",
        effects     = [
            ItemEffect(EffectType.BULLET_SIZE,   1.5, is_multiplier=True),
            ItemEffect(EffectType.BULLET_DAMAGE, 8),
        ],
        color       = pygame.Color("#664422"),
    ),
    Item(
        name        = "Double Tap",
        tier        = 2,
        description = "Fires an additional bullet per shot.",
        effects     = [ItemEffect(EffectType.MULTISHOT, 1)],
        color       = pygame.Color("#cc88ff"),
    ),
    Item(
        name        = "Drill Bit",
        tier        = 3,
        description = "Bullets pierce through one extra enemy.",
        effects     = [ItemEffect(EffectType.PIERCING, 1)],
        color       = pygame.Color("#44ffcc"),
    ),

    # ── Enemy-modifier items 

    Item(
        name        = "Cryo Flask",
        tier        = 2,
        description = "Bullets slow enemies on hit.",
        effects     = [ItemEffect(EffectType.ENEMY_SLOW, 0.4)],   # multiplier on enemy speed
        color       = pygame.Color("#aaeeff"),
    ),
    Item(
        name        = "Cursed Tome",
        tier        = 3,
        description = "Enemies take increased damage from all sources.",
        effects     = [ItemEffect(EffectType.ENEMY_WEAKNESS, 1.25, is_multiplier=True)],
        color       = pygame.Color("#550055"),
    ),

    # ── Utility / special items 

    Item(
        name        = "Vampire Fang",
        tier        = 2,
        description = "Killing an enemy restores a little health.",
        effects     = [ItemEffect(EffectType.HEAL_ON_KILL, 8)],
        color       = pygame.Color("#880022"),
    ),
    Item(
        name        = "Force Field",
        tier        = 3,
        description = "Grants a one-hit shield that regenerates slowly.",
        effects     = [ItemEffect(EffectType.SHIELD, 1)],
        color       = pygame.Color("#4488ff"),
    ),
    Item(
        name        = "Horseshoe Magnet",
        tier        = 1,
        description = "Pulls nearby pickups towards you automatically.",
        effects     = [ItemEffect(EffectType.MAGNET, 200)],   # attract radius px
        color       = pygame.Color("#ff2222"),
    ),
]



# Item Pedestal


PEDESTAL_W, PEDESTAL_H = 64, 80          # total pedestal visual size
PEDESTAL_BASE_H        = 20              # height of the plinth portion
ITEM_DISPLAY_Y_OFFSET  = -8             # how far above the plinth the item floats
PICKUP_RADIUS          = 48             # how close the player must be to pick up

COL_PEDESTAL_BASE      = pygame.Color("#4a3728")
COL_PEDESTAL_TOP       = pygame.Color("#6b5240")
COL_PEDESTAL_GLOW      = pygame.Color("#ffe066")
COL_LABEL_BG           = pygame.Color(0, 0, 0, 160)


class ItemPedestal:
    def __init__(self, pos: tuple[int, int], item: Item) -> None:
        self.pos    = pygame.Vector2(pos)          # centre of the base
        self.item   = item
        self.taken  = False
        self._font  = None                          # lazy-initialised
        self._bob_t = 0.0                           # time accumulator for bobbing

    # --- Update ---

    def update(self, dt: float, player) -> Item | None:
        """
        Call every frame.  Returns the item if the player picks it up,
        otherwise returns None.
        """
        if self.taken:
            return None

        self._bob_t += dt

        dist = self.pos.distance_to(pygame.Vector2(player.rect.center))
        if dist <= PICKUP_RADIUS:
            self.taken = True
            return self.item
        return None

    # --- Draw ---

    def draw(self, surface: pygame.Surface, debug: bool = False) -> None:
        if self.taken:
            return

        if self._font is None:
            self._font = pygame.font.SysFont(None, 18)

        cx = int(self.pos.x)
        cy = int(self.pos.y)

        # Plinth
        base_rect = pygame.Rect(
            cx - PEDESTAL_W // 2,
            cy - PEDESTAL_BASE_H,
            PEDESTAL_W,
            PEDESTAL_BASE_H,
        )
        top_rect = pygame.Rect(
            cx - PEDESTAL_W // 2 + 4,
            cy - PEDESTAL_BASE_H - 10,
            PEDESTAL_W - 8,
            10,
        )
        pygame.draw.rect(surface, COL_PEDESTAL_BASE, base_rect, border_radius=4)
        pygame.draw.rect(surface, COL_PEDESTAL_TOP,  top_rect,  border_radius=3)

        # Glow halo behind item
        glow_surf = pygame.Surface((44, 44), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*COL_PEDESTAL_GLOW[:3], 60), (22, 22), 22)
        bob = int(4 * pygame.math.Vector2(1, 0).rotate(self._bob_t * 120).y)  # ±4 px sine bob
        item_y = cy - PEDESTAL_BASE_H - 10 - 32 + ITEM_DISPLAY_Y_OFFSET + bob
        surface.blit(glow_surf, (cx - 22, item_y - 6))

        # Item sprite
        sprite = self.item.sprite
        sprite_rect = sprite.get_rect(centerx=cx, top=item_y)
        surface.blit(sprite, sprite_rect)

        # Item name label
        name_surf = self._font.render(self.item.name, True, pygame.Color("#ffffff"))
        name_x    = cx - name_surf.get_width() // 2
        name_y    = cy + 6

        bg = pygame.Surface((name_surf.get_width() + 6, name_surf.get_height() + 4), pygame.SRCALPHA)
        bg.fill(COL_LABEL_BG)
        surface.blit(bg,       (name_x - 3, name_y - 2))
        surface.blit(name_surf,(name_x,     name_y))

        # Description on hover / debug
        if debug:
            desc_surf = self._font.render(self.item.description, True, pygame.Color("#dddddd"))
            surface.blit(desc_surf, (cx - desc_surf.get_width() // 2, name_y + 18))

        # Pickup indicator ring
        if debug:
            pygame.draw.circle(surface, pygame.Color("#ffffff"), (cx, cy), PICKUP_RADIUS, 1)