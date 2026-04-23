from __future__ import annotations
import pygame
import math
from src.entities import Bullet, MeleeHitbox


class WeaponType:
    MELEE  = "melee"
    RANGED = "ranged"
    AURA = "aura"


class Weapon:
    def __init__(
        self,
        name: str,
        wtype: str,
        damage: int,
        fire_rate: float,
        color: pygame.Color,
        # ranged
        bullet_speed: float = 500.0,
        bullet_range: float = 400.0,
        bullet_scale: float = 1.0,
        bullet_color: str   = "default",
        clip_size: int   = -1,
        reserve_clips: int   = -1,
        pierce: int   = 0,
        spread_shots: int   = 1,
        spread_angle: float = 0.0,
        # melee
        melee_radius:     float = 80.0,
        melee_half_angle: float = 55.0, 
        #aura
        aura_radius: float = 100.0,
        aura_tick_rate: float = 2.0,
        aura_color: pygame.Color = None,
        aura_pulse_speed: float = 2.0

    ) -> None:
        self.name = name
        self.wtype = wtype
        self.damage = damage
        self.fire_rate = fire_rate   # attacks / second
        self.color = color

        # ranged
        self.bullet_speed = bullet_speed
        self.bullet_range = bullet_range
        self.bullet_scale = bullet_scale
        self.bullet_color = bullet_color
        self.clip_size = clip_size
        self.reserve_clips = reserve_clips
        self.pierce = pierce
        self.spread_shots = spread_shots
        self.spread_angle = spread_angle

        # melee
        self.melee_radius = melee_radius
        self.melee_half_angle = melee_half_angle

        #aura
        self.aura_radius = aura_radius
        self.aura_tick_rate = aura_tick_rate
        self.aura_color = aura_color if aura_color is not None else color
        self.aura_pulse_speed = aura_pulse_speed

        
        # runtime state
        self.curr_ammo: int = clip_size  # -1 = unlimited
        self._cooldown: float = 0.0 # seconds until next attack
        self._reloading: float = 0.0  # reload timer
        self.RELOAD_TIME: float = 1.2  # seconds

        self._sprite: pygame.Surface | None = None

    @property
    def sprite(self) -> pygame.Surface:
        if self._sprite is None:
            surf = pygame.Surface((16,16), pygame.SRCALPHA)
            surf.fill(self.color)
            pygame.draw.rect(surf, pygame.Color("#ffffff"), surf.get_rect(), 1)
            self._sprite = surf
        return self._sprite
    
 # --- Ammo Helpers ---
    @property
    def unlimited_ammo(self) -> bool:
        return self.clip_size == -1
    
    @property
    def ammo_empty(self) -> bool:
        return (not self.unlimited_ammo) and self.curr_ammo <= 0
    
    def reload(self) -> None:
        if self.unlimited_ammo:
            return
        if self.reserve_clips == 0:
            return
        if self.curr_ammo == self.clip_size:
            return
        if self._reloading <= 0:
            self._reloading = self.RELOAD_TIME

# --- update ---
    def update(self, dt: float) -> None:

        if self._cooldown > 0:
            self._cooldown -= dt

        if self._reloading > 0:
            self._reloading -= dt
            if self._reloading <= 0:
                self._reloading = 0.0
                if self.reserve_clips > 0:
                    self.reserve_clips -= 1
                self.curr_ammo = self.clip_size

    def try_attack(self, origin: pygame.Vector2, aim_dir: pygame.Vector2, sound_manager=None) -> list[Bullet] | MeleeHitbox | None:
        if self.wtype == WeaponType.AURA:
            return None   # aura weapons are always going so they dont need to try

        if self._cooldown > 0:
            return None
        if self._reloading > 0:
            return None
        
        if self.wtype == WeaponType.RANGED:
            if not self.unlimited_ammo:
                if self.curr_ammo <= 0:
                    self.reload()
                    return None
                self.curr_ammo -= 1
            
            self._cooldown = 1.0 / self.fire_rate
            if sound_manager is not None:
                sound_manager.play_weapon(self.name)
            return self._spawn_bullets(origin, aim_dir)
        
        else: 
            self._cooldown = 1.0 / self.fire_rate
            if sound_manager is not None:
                sound_manager.play_weapon(self.name)
            return MeleeHitbox(origin = origin, direction = aim_dir, radius = self.melee_radius, half_angle = self.melee_half_angle, damage = self.damage, duration = self._cooldown * 0.6)
        
    def _spawn_bullets(self, origin: pygame.Vector2, aim_dir: pygame.Vector2) -> list[Bullet]:
        bullets = []
        if self.spread_shots <= 1:
            bullets.append(self._make_bullet(origin, aim_dir))
        else:
            half = self.spread_angle / 2.0
            step = self.spread_angle / (self.spread_shots - 1)
            base_angle = math.degrees(math.atan2(aim_dir.y, aim_dir.x))
            for i in range(self.spread_shots):
                angle = base_angle - half + step * i
                rad = math.radians(angle)
                direction = pygame.Vector2(math.cos(rad), math.sin(rad))
                bullets.append(self._make_bullet(origin, direction))
        return bullets
    
    def _make_bullet(self, origin: pygame.Vector2, direction: pygame.Vector2) -> Bullet:
        return Bullet(pos = origin, direction = direction, speed = self.bullet_speed, damage = self.damage, max_range = self.bullet_range, pierce = self.pierce, scale = self.bullet_scale, color_key = self.bullet_color)
    
    def __repr__(self) -> str:
        return f"Weapon({self.name!r}, {self.wtype})"
          


# --- Weapon Catalogue  ---

WEAPON_CATALOGUE: list[Weapon] = [

    # --- Melee ---

    Weapon(
        name = "Dagger",
        wtype = WeaponType.MELEE,
        damage = 18,
        fire_rate = 3.5,          
        color= pygame.Color("#aaddff"),
        melee_radius= 90,
        melee_half_angle = 35,
    ),

    Weapon(
        name = "Broadsword",
        wtype = WeaponType.MELEE,
        damage = 40,
        fire_rate = 1.7,
        color = pygame.Color("#c0c0c0"),
        melee_radius= 120,
        melee_half_angle = 55,
    ),

    Weapon(
        name = "War Hammer",
        wtype = WeaponType.MELEE,
        damage = 70,
        fire_rate = 0.9,            
        color = pygame.Color("#886644"),
        melee_radius = 145,
        melee_half_angle = 45,
    ),

    Weapon(
        name = "Scythe",
        wtype = WeaponType.MELEE,
        damage = 30,
        fire_rate = 2.2,
        color = pygame.Color("#44ff88"),
        melee_radius = 110,            
        melee_half_angle = 28,
    ),

    # --- Ranged ---

    Weapon(
        name = "Pistol",
        wtype = WeaponType.RANGED,
        damage = 15,
        fire_rate = 3.0,
        color = pygame.Color("#ffdd44"),
        bullet_speed = 520,
        bullet_range = 450,
        bullet_scale = 1.0,
        bullet_color = "default",
        clip_size = 8,
        reserve_clips = 6,
    ),

    Weapon(
        name = "Shotgun",
        wtype = WeaponType.RANGED,
        damage = 12,               # per pellet
        fire_rate = 1.2,
        color = pygame.Color("#ffaa44"),
        bullet_speed = 440,
        bullet_range = 250,
        bullet_scale = 0.85,
        bullet_color = "shotgun",
        clip_size = 4,
        reserve_clips = 6,
        spread_shots = 5,
        spread_angle = 28.0,
    ),

    Weapon(
        name = "SMG",
        wtype = WeaponType.RANGED,
        damage = 8,
        fire_rate = 10.0,
        color = pygame.Color("#cc88ff"),
        bullet_speed = 480,
        bullet_range = 340,
        bullet_scale = 0.7,
        bullet_color = "smg",
        clip_size = 30,
        reserve_clips = 6,
    ),

    Weapon(
        name = "Sniper Rifle",
        wtype = WeaponType.RANGED,
        damage = 90,
        fire_rate = 0.7,
        color = pygame.Color("#44ffcc"),
        bullet_speed = 950,
        bullet_range = 960,              
        bullet_scale = 1.2,
        bullet_color = "sniper",
        clip_size = 3,
        reserve_clips = 7,
        pierce = 2,
    ),

    Weapon(
        name = "Grenade Launcher",
        wtype = WeaponType.RANGED,
        damage = 55,
        fire_rate = 0.9,
        color = pygame.Color("#ff6644"),
        bullet_speed = 300,
        bullet_range = 380,
        bullet_scale = 2.0,
        bullet_color = "heavy",
        clip_size = 2,
        reserve_clips = 6,
    ),

     Weapon(
        name = "Toxic Cloud",
        wtype = WeaponType.AURA,
        damage = 6,               
        fire_rate = 0.5,            
        color = pygame.Color("#44ff44"),
        aura_radius = 90.0,            
        aura_tick_rate = 4.0,           
        aura_color = pygame.Color("#66ff44"),
        aura_pulse_speed = 3.0,         
    ),
 

    Weapon(
        name = "Soul Furnace",
        wtype = WeaponType.AURA,
        damage = 18,              
        fire_rate = 0.5,
        color = pygame.Color("#ff8833"),
        aura_radius = 160.0,           
        aura_tick_rate = 1.5,           
        aura_color = pygame.Color("#ff5500"),
        aura_pulse_speed = 1.2,
    )
]