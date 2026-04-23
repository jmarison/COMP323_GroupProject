import pygame
from pathlib import Path
from src.entities import Bullet, MeleeHitbox, AuraHitbox
from src.weapon import Weapon, WeaponType
from src.item import Item, EffectType
from src.keybindings import KeyBindings


class ControlScheme:
    def __init__(self, bindings: KeyBindings) -> None:
        self.bindings = bindings

    def read_move(self, keys) -> pygame.Vector2:
        move = self.bindings.move_keys()
        x, y = 0, 0
        if any(keys[k] for k in move["left"]):  x -= 1
        if any(keys[k] for k in move["right"]): x += 1
        if any(keys[k] for k in move["up"]):    y -= 1
        if any(keys[k] for k in move["down"]):  y += 1
        v = pygame.Vector2(x, y)
        return v.normalize() if v.length_squared() > 0 else v

    def read_aim(self, keys) -> pygame.Vector2:
        aim = self.bindings.aim_keys()
        x, y = 0, 0
        if any(keys[k] for k in aim["left"]):  x -= 1
        if any(keys[k] for k in aim["right"]): x += 1
        if any(keys[k] for k in aim["up"]):    y -= 1
        if any(keys[k] for k in aim["down"]):  y += 1
        v = pygame.Vector2(x, y)
        return v.normalize() if v.length_squared() > 0 else v

    def action_pressed(self, action: str, event: pygame.event.Event) -> bool:
        if event.type != pygame.KEYDOWN:
            return False
        return event.key in self.bindings.action_keys().get(action, set())

    def aim_held(self, keys) -> bool:
        # this is basically used for autofire
        aim = self.bindings.aim_keys()
        return any(any(keys[k] for k in aim[d]) for d in ("left", "right", "up", "down"))

class Player(pygame.sprite.Sprite):
    MAX_WEAPONS = 2
    PLAYER_SIZE = (110, 110)
    HITBOX_SIZE = (24, 36)
    COLOR = pygame.Color("#4fc3f7")
    IFRAME_DURATION = 1.2

    def __init__(self, pos: tuple[int, int], bindings: KeyBindings, sound_manager = None) -> None:
        super().__init__()

        # --- player stats ---
        self.base_max_health: int = 50
        self.maxHealth: int = self.base_max_health
        self.currHealth: int = self.maxHealth
        self.base_speed : int = 265
        self.speed : int = self.base_speed

        self.controls = ControlScheme(bindings)
        self.sound_manager = sound_manager

        self._iframes: float = 0.0

        # --- room protection / flawless tracking ---
        self.divine_protection_active: bool = False
        self.room_flawless: bool = False

        # --- item-driven runtime state ---
        self.force_field_charges: int = 0
        self.force_field_regen_timer: float = 0.0
        self._last_scale: float = 1.0

        # --- weapons ---
        self.weaponInv: list[Weapon] = []
        self.currWeaponIndex: int = 0

        # --- items ---
        self.items: list[Item] = []

        # --- hitboxes that are currently active from player ---
        self.bullets: list[Bullet] = []
        self.melee_hitboxes: list[MeleeHitbox] = []
        self.aura_hitboxes: list[AuraHitbox] = []  # kept for compatibility
        self._active_aura: AuraHitbox | None = None  # persistent always-on aura

        # --- sprite + position ---
        self.image = pygame.Surface(self.PLAYER_SIZE, pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = pygame.Rect(0, 0, *self.HITBOX_SIZE)
        self.hitbox.center = self.rect.center
        self.pos = pygame.Vector2(pos)
        self.aim_dir = pygame.Vector2(1,0)

        ROOT_DIR = Path(__file__).parent.parent
        sprite_path = str(ROOT_DIR / "assets" / "sprites" / "prototype_character.png")

        # --- load animations ---
        anim_map = {
            "idle_down":  (0, 2),
            "idle_right": (1, 2),
            "idle_up":    (2, 2),
            "walk_down":  (3, 4),
            "walk_right": (4, 4),
            "walk_up":    (5, 4),
            "hit":        (6, 2),
            "death":      (10, 3)
        }
        

        self.animator = Animator(sprite_path, (32, 32), anim_map)
        self.image = self.animator.get_frame(0) # Initial 
        self.facing_dir = "down"

    # --- core update loop ----

    def update(self, dt: float, keys, events: list[pygame.event.Event]) -> None: 
        if self._iframes > 0:
            self._iframes -= dt
        if self.force_field_regen_timer > 0:
            self.force_field_regen_timer -= dt
            if self.force_field_regen_timer <= 0 and self.max_force_field_charges > self.force_field_charges:
                self.force_field_charges = self.max_force_field_charges
                self.force_field_regen_timer = 0.0
        self._recalculate_item_stats()
        self._handle_movement(dt, keys)
        self._handle_aim(keys)
        self._handle_weapon_switch(events)
        self._handle_attack(dt, keys, events)
        self._update_weapon_cooldowns(dt)
        self._update_aura(dt)

    # --- movement handler---
    def _handle_movement(self, dt:float, keys) -> None:
        direction = self.controls.read_move(keys)
        self.pos += direction * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.hitbox.center = self.rect.center

        # handle direction to determine which animation
        if self.is_dead:
            self.animator.set_anim("death")
        elif self._iframes > 0 and self.currHealth > 0:
            self.animator.set_anim("hit")
        elif direction.length_squared() > 0:
            # MOVING: Update the facing_dir and play walk animation
            if abs(direction.x) > abs(direction.y):
                self.facing_dir = "left" if direction.x < 0 else "right"
                self.animator.set_anim("walk_right", flip_x=(direction.x < 0))
            elif direction.y > 0:
                self.facing_dir = "down"
                self.animator.set_anim("walk_down")
            else:
                self.facing_dir = "up"
                self.animator.set_anim("walk_up")
        else:
            # IDLE: Use the last direction walked
            if self.facing_dir == "left":
                self.animator.set_anim("idle_right", flip_x=True)
            elif self.facing_dir == "right":
                self.animator.set_anim("idle_right", flip_x=False)
            elif self.facing_dir == "up":
                self.animator.set_anim("idle_up")
            else: # Default/Down
                self.animator.set_anim("idle_down")

        # Update current frame
        self.image = self.animator.get_frame(dt)

    # --- Collision --- 
    def wall_collisions(self, walls: list) -> None:
        for wall in walls:
            if not self.hitbox.colliderect(wall.rect):
                continue

            dx_left = self.hitbox.right - wall.rect.left
            dx_right = wall.rect.right - self.hitbox.left
            dy_up = self.hitbox.bottom - wall.rect.top
            dy_down = wall.rect.bottom - self.hitbox.top

            min_x = dx_left if dx_left < dx_right else -dx_right
            min_y = dy_up if dy_up < dy_down else -dy_down

            if abs(min_x) < abs(min_y):
                self.hitbox.x -= min_x
            else:
                self.hitbox.y -= min_y

            self.pos.x = self.hitbox.centerx
            self.pos.y = self.hitbox.centery
            self.rect.center = self.hitbox.center

    # -- aiming handler---
    def _handle_aim(self, keys) -> None:
        aim = self.controls.read_aim(keys)
        if aim.length_squared() > 0:
            self.aim_dir = aim

    # --- weapons system handler--- 
    def _handle_weapon_switch(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if self.controls.action_pressed("weapon_next", event):
                self._cycle_weapon(1)
            elif self.controls.action_pressed("weapon_prev", event):
                self._cycle_weapon(-1)
            elif self.controls.action_pressed("weapon_slot1", event):
                self._select_weapon(0)
            elif self.controls.action_pressed("weapon_slot2", event):
                self._select_weapon(1)
    
    def _cycle_weapon(self, step: int) -> None:
        if self.weaponInv:
            self.currWeaponIndex = (self.currWeaponIndex + step) % len(self.weaponInv)

    def _select_weapon(self, index: int) -> None:
        if 0 <= index < len(self.weaponInv):
            self.currWeaponIndex = index
    
    def add_weapon(self, weapon: Weapon) -> bool:
        if len(self.weaponInv) >= self.MAX_WEAPONS:
            return False
        self.weaponInv.append(weapon)
        return True
# planned to combine into add_weapon for a single call
    def acquire_weapon(self, weapon: Weapon) -> bool:
        if len(self.weaponInv) < self.MAX_WEAPONS:
            self.weaponInv.append(weapon)
            self.currWeaponIndex = len(self.weaponInv) - 1
            return True

        if not self.weaponInv:
            self.weaponInv.append(weapon)
            self.currWeaponIndex = 0
            return True

        self.weaponInv[self.currWeaponIndex] = weapon
        return True

# --- item mods --- 
    def _get_effect_value(self, effect_type: EffectType, *, multiplicative_default: float = 1.0) -> float:
        total = 0.0
        mult = multiplicative_default
        for item in self.items:
            for effect in item.effects:
                if effect.effect_type != effect_type:
                    continue
                if effect.is_multiplier:
                    mult *= effect.value
                else:
                    total += effect.value
        return total * mult if multiplicative_default == 0.0 else total, mult

    def _sum_effect(self, effect_type: EffectType) -> float:
        total = 0.0
        for item in self.items:
            for effect in item.effects:
                if effect.effect_type == effect_type and not effect.is_multiplier:
                    total += effect.value
        return total

    def _product_effect(self, effect_type: EffectType) -> float:
        mult = 1.0
        for item in self.items:
            for effect in item.effects:
                if effect.effect_type == effect_type and effect.is_multiplier:
                    mult *= effect.value
        return mult

    def _effect_count(self, effect_type: EffectType) -> int:
        count = 0
        for item in self.items:
            for effect in item.effects:
                if effect.effect_type == effect_type:
                    count += int(round(effect.value)) if not effect.is_multiplier else 1
        return count

    def _sync_size(self, scale: float) -> None:
        scale = max(0.45, scale)
        if abs(scale - self._last_scale) < 1e-6:
            return
        center = self.rect.center
        w = max(16, round(self.PLAYER_SIZE[0] * scale))
        h = max(20, round(self.PLAYER_SIZE[1] * scale))

        self.rect.size = (w, h)
        self._last_scale = scale

        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.image.fill(self.COLOR)
        self.rect = self.image.get_rect(center=center)
        hb_w = max(12, round(self.HITBOX_SIZE[0] * scale))
        hb_h = max(16, round(self.HITBOX_SIZE[1] * scale))
        self.hitbox = pygame.Rect(0, 0, hb_w, hb_h)
        self.hitbox.center = center

    def _apply_item_modifiers_to_weapons(self) -> None:
        fire_rate_add = self._sum_effect(EffectType.FIRE_RATE)
        fire_rate_mult_bonus = sum(
            effect.value for item in self.items for effect in item.effects
            if effect.effect_type == EffectType.FIRE_RATE and effect.is_multiplier
        )
        bullet_damage = self._sum_effect(EffectType.BULLET_DAMAGE)
        bullet_speed = self._sum_effect(EffectType.BULLET_SPEED)
        bullet_scale_mult = self._product_effect(EffectType.BULLET_SIZE)
        extra_multishot = int(round(self._sum_effect(EffectType.MULTISHOT)))
        extra_pierce = int(round(self._sum_effect(EffectType.PIERCING)))

        for weapon in self.weaponInv:
            if not hasattr(weapon, '_item_base_stats'):
                weapon._item_base_stats = {
                    'damage': weapon.damage,
                    'fire_rate': weapon.fire_rate,
                    'bullet_speed': weapon.bullet_speed,
                    'bullet_scale': weapon.bullet_scale,
                    'pierce': weapon.pierce,
                    'spread_shots': weapon.spread_shots,
                    'spread_angle': weapon.spread_angle,
                }
            base = weapon._item_base_stats
            weapon.damage = base['damage']
            # additive FIRE_RATE values are treated as cooldown reduction percent, so -0.05 = 5% faster
            weapon.fire_rate = max(0.1, base['fire_rate'] * max(0.1, 1.0 - fire_rate_add) * max(0.1, 1.0 + fire_rate_mult_bonus))
            weapon.bullet_speed = max(80.0, base['bullet_speed'] + bullet_speed)
            weapon.bullet_scale = max(0.35, base['bullet_scale'] * bullet_scale_mult)
            weapon.pierce = max(0, base['pierce'] + extra_pierce)
            if weapon.wtype == WeaponType.RANGED:
                weapon.damage = max(1, round(base['damage'] + bullet_damage))
                weapon.spread_shots = max(1, base['spread_shots'] + extra_multishot)
                if weapon.spread_shots > 1 and base['spread_angle'] <= 0:
                    weapon.spread_angle = max(12.0, 10.0 + 4.0 * (weapon.spread_shots - 1))
                else:
                    weapon.spread_angle = base['spread_angle']

    def _recalculate_item_stats(self) -> None:
        move_bonus = self._sum_effect(EffectType.MOVE_SPEED)
        max_health_bonus = self._sum_effect(EffectType.MAX_HEALTH)
        size_mult = self._product_effect(EffectType.PLAYER_SIZE)

        self.speed = max(80, round((self.base_speed + move_bonus)))
        old_max = self.maxHealth
        self.maxHealth = max(1, round(self.base_max_health + max_health_bonus))
        if self.currHealth > self.maxHealth:
            self.currHealth = self.maxHealth
        elif self.maxHealth > old_max:
            self.currHealth += self.maxHealth - old_max
        self._sync_size(size_mult)

        max_charges = self.max_force_field_charges
        if self.force_field_charges > max_charges:
            self.force_field_charges = max_charges
        if max_charges > 0 and self.force_field_charges <= 0 and self.force_field_regen_timer <= 0:
            self.force_field_regen_timer = self.force_field_regen_duration
        self._apply_item_modifiers_to_weapons()
    
    @property
    def damage_multiplier(self) -> float:
        # damage scales with # of coins collected. Capped at 10x damage
        if self.coins <= 0:
            return 1.0
        multiplier = 1.0 + (self.coins / 20.0)
        return min(multiplier, 10.0)

    @property
    def enemy_weakness_multiplier(self) -> float:
        mult = 1.0
        for item in self.items:
            for effect in item.effects:
                if effect.effect_type == EffectType.ENEMY_WEAKNESS:
                    mult *= effect.value if effect.is_multiplier else (1.0 + effect.value)
        return max(1.0, mult)

    @property
    def max_force_field_charges(self) -> int:
        return self._effect_count(EffectType.SHIELD)

    @property
    def force_field_regen_duration(self) -> float:
        return 8.0

    @property
    def coin_magnet_radius(self) -> float:
        return self._sum_effect(EffectType.MAGNET)
    
    @property
    def current_weapon(self) -> Weapon | None:
        return self.weaponInv[self.currWeaponIndex] if self.weaponInv else None
    

    # --- Attack handler ---
    def _handle_attack(self, dt:float, keys, events: list[pygame.event.Event]) -> None:
        weapon = self.current_weapon
        if weapon is None:
            return
        if weapon.wtype == WeaponType.AURA:
            return   # aura weapons are handled by _update_aura, not here
        if not self.controls.aim_held(keys):
            return
        result = weapon.try_attack(origin = pygame.Vector2(self.rect.center), aim_dir = self.aim_dir, sound_manager = self.sound_manager)
        if result is None:
            return
        mult = self.damage_multiplier * self.enemy_weakness_multiplier

        if isinstance(result, list):
            for b in result:
                b.damage = max(1, round(b.damage * mult))
            self.bullets.extend(result)
        elif isinstance(result, MeleeHitbox):
            result.damage = max(1, round(result.damage * mult))
            self.melee_hitboxes.append(result)

    # --- Aura update (always-on, like Vampire Survivors garlic) ---
    def _update_aura(self, dt: float) -> None:
        weapon = self.current_weapon
        is_aura = weapon is not None and weapon.wtype == WeaponType.AURA

        if not is_aura:
            # Switched away from aura weapon — kill it
            if self._active_aura is not None:
                self._active_aura.alive = False
                self._active_aura = None
            return

        center = pygame.Vector2(self.rect.center)
        radius = weapon.aura_radius * self._last_scale

        if self._active_aura is None or not self._active_aura.alive:
            # Create a fresh persistent aura
            mult = self.damage_multiplier * self.enemy_weakness_multiplier
            self._active_aura = AuraHitbox(
                center     = center,
                radius     = radius,
                damage     = max(1, round(weapon.damage * mult)),
                tick_rate  = weapon.aura_tick_rate,
                color      = weapon.aura_color,
                pulse_speed= weapon.aura_pulse_speed,
            )
        else:
            # Keep it anchored to the player and update radius (in case size items change)
            self._active_aura.follow(center)
            self._active_aura.radius = radius
            self._active_aura.update(dt)

    def _update_weapon_cooldowns(self, dt: float) -> None:
        for w in self.weaponInv:
            w.update(dt)


    # --- Health ---
    def start_room_protection(self) -> None:
        self.divine_protection_active = True
        self.room_flawless = True

    def lose_room_flawless(self) -> None:
        self.room_flawless = False

    def take_damage(self, amount: int) -> bool:
        if self._iframes > 0:
            return False

        if self.divine_protection_active:
            self.divine_protection_active = False
            self.room_flawless = False
            self._iframes = self.IFRAME_DURATION * 0.5
            return False

        if self.force_field_charges > 0:
            self.force_field_charges -= 1
            self.force_field_regen_timer = self.force_field_regen_duration
            self.room_flawless = False
            self._iframes = self.IFRAME_DURATION * 0.5
            return False

        self.currHealth = max(0, self.currHealth - amount)
        self.room_flawless = False
        self._iframes = self.IFRAME_DURATION
        return True

    def heal(self, amount: int) -> None:
        self.currHealth = min(self.maxHealth, self.currHealth + amount)

    def on_enemy_hit(self, enemy) -> None:
        slow_mult = 1.0
        for item in self.items:
            for effect in item.effects:
                if effect.effect_type == EffectType.ENEMY_SLOW:
                    slow_mult *= effect.value if effect.is_multiplier else effect.value
        if slow_mult != 1.0 and hasattr(enemy, 'apply_slow'):
            enemy.apply_slow(max(0.1, slow_mult), 1.5)

    def on_enemy_killed(self) -> None:
        heal_amount = int(round(self._sum_effect(EffectType.HEAL_ON_KILL)))
        if heal_amount > 0:
            self.heal(heal_amount)

    @property
    def is_dead(self) -> bool:
        return self.currHealth <= 0
    
    def _reset(self) -> None:
        self.items = []
        self.weaponInv = []
        self.currWeaponIndex = 0
        self.maxHealth = self.base_max_health
        self.currHealth = self.maxHealth
        self.speed = self.base_speed
        self.bullets = []
        self.melee_hitboxes = []
        self.aura_hitboxes = []
        self._active_aura = None
        self._iframes = 0.0
        self.coins = 0
        self.divine_protection_active = False
        self.room_flawless = False
        self.force_field_charges = 0
        self.force_field_regen_timer = 0.0
        self._sync_size(1.0)
    
    # --- Drawing --- 
    def draw(self, surface: pygame.Surface, debug: bool = False) -> None:
        if self._iframes <= 0 or int(self._iframes * 30) % 2 == 0:
            scaled_img = pygame.transform.scale(self.image, self.rect.size)
            surface.blit(scaled_img, self.rect)
        #self._draw_aim_line(surface)
        for b in self.bullets:
            b.draw(surface)
        for mh in self.melee_hitboxes:
            mh.draw(surface)
        if self._active_aura is not None and self._active_aura.alive:
            self._active_aura.draw(surface)
            
        if debug:
            pygame.draw.rect(surface, pygame.Color("#00ff00"), self.hitbox, 1)

    def _draw_aim_line(self, surface: pygame.Surface) -> None:
        start = pygame.Vector2(self.rect.center)
        end = start + self.aim_dir * 28
        pygame.draw.line(surface, pygame.Color("#ffffff"), start, end, 2)



# ========= ANIMATION STUFF ===============
class Animator:
    def __init__(self, sheet_path, frame_size, animations):
        self.sheet = pygame.image.load(sheet_path).convert_alpha()
        self.frame_size = frame_size
        self.animations = animations  
        self.current_anim = "idle_down"
        self.frame_index = 0
        self.timer = 0
        self.fps = 4
        self.flip_x = False

    def get_frame(self, dt):
        row, num_frames = self.animations.get(self.current_anim, (0, 1))
        self.timer += dt
        if self.timer >= 1 / self.fps:
            self.timer = 0
            self.frame_index = (self.frame_index + 1) % num_frames
        
        rect = pygame.Rect(self.frame_index * self.frame_size[0], 
                           row * self.frame_size[1], 
                           *self.frame_size)
        
        frame = self.sheet.subsurface(rect)
        if self.flip_x:
            return pygame.transform.flip(frame, True, False)
        return frame
    
    def set_anim(self, name, flip_x = False):
        if self.current_anim != name or self.flip_x != flip_x:
            self.current_anim = name
            self.flip_x = flip_x
            self.frame_index = 0