import pygame
from main.entities import Bullet, MeleeHitbox
from main.weapon import Weapon, WeaponType
from main.item import Item, EffectType
from main.keybindings import KeyBindings


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
    PLAYER_SIZE = (32, 48)
    HITBOX_SIZE = (22, 34)
    COLOR = pygame.Color("#4fc3f7")
    IFRAME_DURATION = 1.2

    def __init__(self, pos: tuple[int, int], bindings: KeyBindings, sound_manager = None) -> None:
        super().__init__()

        # --- player stats ---
        self.base_max_health: int = 50
        self.maxHealth: int = self.base_max_health
        self.currHealth: int  = self.maxHealth
        self.base_speed : int = 300
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

        # --- projectiles that are currently alive from player ---
        self.bullets: list[Bullet] = []
        self.melee_hitboxes: list[MeleeHitbox] = []

        # --- sprite + position ---
        self.image = pygame.Surface(self.PLAYER_SIZE, pygame.SRCALPHA)
        self.image.fill(self.COLOR)
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = pygame.Rect(0, 0, *self.HITBOX_SIZE)
        self.hitbox.center = self.rect.center
        self.pos = pygame.Vector2(pos)
        self.aim_dir = pygame.Vector2(1,0)

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

    # --- movement handler---
    def _handle_movement(self, dt:float, keys) -> None:
        direction = self.controls.read_move(keys)
        self.pos += direction * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.hitbox.center = self.rect.center
    # --- Collision --- 
    def wall_collisions(self, walls: list) -> None:
        for wall in walls:
            if not self.rect.colliderect(wall.rect):
                continue

            dx_left = self.rect.right  - wall.rect.left   
            dx_right = wall.rect.right  - self.rect.left   
            dy_up = self.rect.bottom - wall.rect.top    
            dy_down = wall.rect.bottom - self.rect.top     

            min_x = dx_left if dx_left < dx_right else -dx_right
            min_y = dy_up if dy_up < dy_down else -dy_down

            if abs(min_x) < abs(min_y):
                self.rect.x -= min_x
            else:
                self.rect.y -= min_y

            # Keep pos in sync with rect
            self.pos.x = self.rect.centerx
            self.pos.y = self.rect.centery
        self.hitbox.center = self.rect.center

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
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.image.fill(self.COLOR)
        self.rect = self.image.get_rect(center=center)
        hb_w = max(12, round(self.HITBOX_SIZE[0] * scale))
        hb_h = max(16, round(self.HITBOX_SIZE[1] * scale))
        self.hitbox = pygame.Rect(0, 0, hb_w, hb_h)
        self.hitbox.center = center
        self._last_scale = scale

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
            surface.blit(self.image, self.rect)
        self._draw_aim_line(surface)
        for b in self.bullets:
            b.draw(surface)
        for mh in self.melee_hitboxes:
            mh.draw(surface)
        if debug:
            pygame.draw.rect(surface, pygame.Color("#00ff00"), self.hitbox, 1)

    def _draw_aim_line(self, surface: pygame.Surface) -> None:
        start = pygame.Vector2(self.rect.center)
        end = start + self.aim_dir * 28
        pygame.draw.line(surface, pygame.Color("#ffffff"), start, end, 2)