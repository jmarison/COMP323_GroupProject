import pygame
from main.weapon import Weapon
from main.item import Item

class ControlScheme:
    SCHEMES = {
         "WASD_ARROWS": {
            "move": {
                "left":  {pygame.K_a},
                "right": {pygame.K_d},
                "up":    {pygame.K_w},
                "down":  {pygame.K_s},
            },
            "aim": {
                "left":  {pygame.K_LEFT},
                "right": {pygame.K_RIGHT},
                "up":    {pygame.K_UP},
                "down":  {pygame.K_DOWN},
            },
        },
        "WASD_IJKL": {
            "move": {
                "left":  {pygame.K_a},
                "right": {pygame.K_d},
                "up":    {pygame.K_w},
                "down":  {pygame.K_s},
            },
            "aim": {
                "left":  {pygame.K_j},
                "right": {pygame.K_l},
                "up":    {pygame.K_i},
                "down":  {pygame.K_k},
            },
        },
    }
    ACTIONS = {
        "weapon_next":  {pygame.K_e},
        "weapon_prev":  {pygame.K_q},
        "weapon_slot1": {pygame.K_1},
        "weapon_slot2": {pygame.K_2},
    }

    def __init__(self, scheme_name: str = "WASD_ARROWS") -> None:
        self.set_scheme(scheme_name)

    def set_scheme(self, scheme_name: str) -> None:
        if scheme_name not in self.SCHEMES:
            raise ValueError(f"Unknown scheme '{scheme_name}'. Valid: {list(self.SCHEMES)}")
        self.name = scheme_name
        self._move = self.SCHEMES[scheme_name]["move"]
        self._aim  = self.SCHEMES[scheme_name]["aim"]

    def read_move(self, keys) -> pygame.Vector2:
        x = 0
        y = 0
        if any(keys[k] for k in self._move["left"]):  x -= 1
        if any(keys[k] for k in self._move["right"]): x += 1
        if any(keys[k] for k in self._move["up"]):    y -= 1
        if any(keys[k] for k in self._move["down"]):  y += 1
        v = pygame.Vector2(x, y)
        return v.normalize() if v.length_squared() > 0 else v 
    
    def read_aim(self, keys) -> pygame.Vector2:
        x = 0
        y = 0
        if any(keys[k] for k in self._aim["left"]):  x -= 1
        if any(keys[k] for k in self._aim["right"]): x += 1
        if any(keys[k] for k in self._aim["up"]):    y -= 1
        if any(keys[k] for k in self._aim["down"]):  y += 1
        v = pygame.Vector2(x, y)
        return v.normalize() if v.length_squared() > 0 else v
    
    def action_pressed(self, action: str, event: pygame.event.Event) -> bool:
        if event.type != pygame.KEYDOWN:
            return False
        return event.key in self.ACTIONS.get(action, set())
    


class Player(pygame.sprite.Sprite):
    MAX_WEAPONS = 2
    PLAYER_SIZE = (32, 48)
    COLOR = pygame.Color("#4fc3f7")


    def __init__(self, pos: tuple[int, int], scheme_name: str = "WASD_IJKL") -> None:
        super().__init__()

        # --- player stats ---
        self.maxHealth: int = 200
        self.currentHealth: int  = self.maxHealth
        self.speed : int = 200

        self.controls = ControlScheme(scheme_name)

        # --- weapons ---
        self.weaponInv: list[Weapon] = []
        self.currentWeaponIndex: int = 0

        # --- items ---
        self.items: list[Item] = []

        # --- sprite + position ---
        self.image = pygame.Surface(self.PLAYER_SIZE, pygame.SRCALPHA)
        self.image.fill(self.COLOR)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.aim_dir = pygame.Vector2(1,0)

    # --- core update loop ----

    def update(self, dt: float, keys, events: list[pygame.event.Event]) -> None: 
        self._handle_movement(dt, keys)
        self._handle_aim(keys)
        self._handle_weapon_switch(events)

    # --- movement ---
    def _handle_movement(self, dt:float, keys) -> None:
        direction = self.controls.read_move(keys)
        self.pos += direction * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
    
    # -- aiming ---
    def _handle_aim(self, keys) -> None:
        aim = self.controls.read_aim(keys)
        if aim.length_squared() > 0:
            self.aim_dir = aim

    # --- weapons system --- 
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
            self.currentWeaponIndex = (self.currentWeaponIndex + step) % len(self.weaponInv)

    def _select_weapon(self, index: int) -> None:
        if 0 <= index < len(self.weaponInv):
            self.currentWeaponIndex = index
    
    def add_weapon(self, weapon: Weapon) -> bool:
        if len(self.weaponInv) >= self.MAX_WEAPONS:
            return False
        self.weaponInv.append(weapon)
        return True
    
    @property
    def current_weapon(self) -> Weapon | None:
        return self.weaponInv[self.currentWeaponIndex] if self.weaponInv else None
    
    # --- Health ---
    def take_damage(self, amount: int) -> None:
        self.currentHealth = max(0, self.currentHealth - amount)

    def heal(self, amount: int) -> None:
        self.currentHealth = min(self.maxHealth, self.currentHealth + amount)

    @property
    def is_dead(self) -> bool:
        return self.currentHealth <= 0
    
    def _reset(self) -> None:
        pass
    
    # --- Drawing --- 
    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, self.rect)
        self._draw_aim_line(surface)

    def _draw_aim_line(self, surface: pygame.Surface) -> None:
        start = pygame.Vector2(self.rect.center)
        end = start + self.aim_dir * 28
        pygame.draw.line(surface, pygame.Color("#ffffff"), start, end, 2)