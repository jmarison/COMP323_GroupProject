from __future__ import annotations
import pygame
import math



# ------------------ TITLE ---------------------------
TITLE_BUTTONS = ["Start", "Settings", "Quit"]

class TitleScreen:
    def __init__(self, w: int, h: int, font: pygame.font.Font):
        self.w = w
        self.h = h
        self.font = font
        self.selected = 0

        btn_w, btn_h = 260, 44
        btn_x = w // 2 - btn_w // 2
        spacing = 58
        start_y = h // 2 - spacing  # vertically center the button group

        self.button_rects = [
            pygame.Rect(btn_x, start_y + i * spacing, btn_w, btn_h)
            for i in range(len(TITLE_BUTTONS))
        ]

    def draw(self, screen: pygame.Surface, events: list[pygame.event.Event]) -> str | None:
        screen.fill(pygame.Color("#1a1a2e"))

        # Title
        title_font = pygame.font.SysFont(None, 64)
        title_surf = title_font.render("Consumed with Greed", True, pygame.Color("#e0e0e0"))
        screen.blit(title_surf, (self.w // 2 - title_surf.get_width() // 2, self.h // 6))

        # Subtitle / hint
        hint_font = pygame.font.SysFont(None, 20)
        hint = hint_font.render("SPACE Select", True, pygame.Color("#555555"))
        screen.blit(hint, (self.w // 2 - hint.get_width() // 2, self.h - 28))

        action = None
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_s, pygame.K_DOWN):
                    self.selected = (self.selected + 1) % len(TITLE_BUTTONS)
                elif event.key in (pygame.K_w, pygame.K_UP):
                    self.selected = (self.selected - 1) % len(TITLE_BUTTONS)
                elif event.key == pygame.K_SPACE:
                    action = TITLE_BUTTONS[self.selected].lower()

        # buttons
        for i, (label, rect) in enumerate(zip(TITLE_BUTTONS, self.button_rects)):
            is_selected = (i == self.selected)

            bg_color = pygame.Color("#2a2a4a") if is_selected else pygame.Color("#111122")
            pygame.draw.rect(screen, bg_color, rect)

            # bright if selected, dim if not
            border_color = pygame.Color("#4fc3f7") if is_selected else pygame.Color("#333355")
            pygame.draw.rect(screen, border_color, rect, 2)

            label_color = pygame.Color("#ffffff") if is_selected else pygame.Color("#aaaaaa")
            self._draw_button_text(screen, label, rect, label_color)

        return action
    
    def _draw_text(self, screen: pygame.Surface, text: str, pos: tuple[int, int], color: pygame.Color = None) -> None:
        if color is None:
             color = pygame.Color("white")
        s = self.font.render(text, True, color)
        screen.blit(s, pos)

    def _draw_button_text(self, screen: pygame.Surface, text: str, rect: pygame.Rect, color:pygame.Color = None) -> None:
        if color is None:
             color = pygame.Color("white")
        text_surface = self.font.render(text, True, color)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)

# -------------- SETTINGS --------------------------

_BIND_ROWS: list[tuple[str, str, str]] = [
    # (group,     action,         display label)
    ("move",    "up",           "Move Up"),
    ("move",    "down",         "Move Down"),
    ("move",    "left",         "Move Left"),
    ("move",    "right",        "Move Right"),
    ("aim",     "up",           "Aim Up"),
    ("aim",     "down",         "Aim Down"),
    ("aim",     "left",         "Aim Left"),
    ("aim",     "right",        "Aim Right"),
    ("actions", "weapon_next",  "Next Weapon"),
    ("actions", "weapon_prev",  "Prev Weapon"),
    ("actions", "weapon_slot1", "Weapon Slot 1"),
    ("actions", "weapon_slot2", "Weapon Slot 2"),
]

_COL_LABEL = 80    # x: action name
_COL_KEY  = 300   # x: current key
_ROW_START  = 80    # y: first row
_ROW_H   = 34    # row height
_CONFLICT_SHOW_FRAMES = 120   # how long to show the conflict warning


class SettingsMenu:

    def __init__(self, w: int, h: int, font: pygame.font.Font, bindings) -> None:
        self.w = w
        self.h = h
        self.font = font
        self.bindings = bindings        

        self.selected: int = 0            
        self.listening: bool = False     
        self.conflict_timer: int = 0    
        self.conflict_msg: str = ""

    # ------------------------------------------------------------------ #

    def draw(self, screen: pygame.Surface, events: list[pygame.event.Event]) -> str | None:
        screen.fill(pygame.Color("#1a1a2e"))

        # Title
        self._draw_centered(screen, "SETTINGS  —  KEY BINDINGS", self.h // 14,
                            pygame.Color("#e0e0e0"), big=True)

        # Column headers
        hdr_y = _ROW_START - 24
        self._draw_text(screen, "Action", (_COL_LABEL, hdr_y), pygame.Color("#888888"))
        self._draw_text(screen, "Key", (_COL_KEY,   hdr_y), pygame.Color("#888888"))

        # Rows
        for i, (group, action, label) in enumerate(_BIND_ROWS):
            y = _ROW_START + i * _ROW_H
            is_selected = (i == self.selected)

            # highlight selected
            if is_selected:
                pygame.draw.rect(screen, pygame.Color("#2a2a4a"),
                pygame.Rect(60, y - 4, self.w - 120, _ROW_H - 2))

            key_int   = self.bindings.get(group, action)
            key_label = pygame.key.name(key_int).upper()

            label_color = pygame.Color("#ffffff") if is_selected else pygame.Color("#aaaaaa")
            self._draw_text(screen, label,     (_COL_LABEL, y), label_color)

            # Key box
            if is_selected and self.listening:
                key_color  = pygame.Color("#ffcc00")
                key_label  = "PRESS A KEY…"
            elif is_selected:
                key_color  = pygame.Color("#4fc3f7")
            else:
                key_color  = pygame.Color("#888888")

            key_rect = pygame.Rect(_COL_KEY - 4, y - 3, 180, _ROW_H - 4)
            pygame.draw.rect(screen, pygame.Color("#111122"), key_rect)
            pygame.draw.rect(screen, key_color, key_rect, 2)
            self._draw_text(screen, key_label, (_COL_KEY + 4, y), key_color)

        # Conflict warning
        if self.conflict_timer > 0:
            self.conflict_timer -= 1
            self._draw_centered(screen, self.conflict_msg, self.h - 60, pygame.Color("#ff4444"))

        # Footer
        hints = "ENTER Rebind    BACKSPACE Reset Row    ESC Back"
        self._draw_centered(screen, hints, self.h - 28, pygame.Color("#555555"))

        # ---- Handle input ----
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            result = self._handle_key(event.key)
            if result == "back":
                return "back"

        return None

    
    # --- Input ---                                                              
    

    def _handle_key(self, key: int) -> str | None:
        if self.listening:
            return self._finish_rebind(key)

        if key == pygame.K_ESCAPE:
            self.bindings.save()
            return "back"

        if key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % len(_BIND_ROWS)
        elif key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % len(_BIND_ROWS)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            self.listening = True
        elif key == pygame.K_BACKSPACE:
            self._reset_row()

        return None

    def _finish_rebind(self, key: int) -> None:
        self.listening = False

        # esc not allowed as keybinding since it closes game
        if key in (pygame.K_ESCAPE,):
            return None

        group, action, _ = _BIND_ROWS[self.selected]
        conflict = self.bindings.is_key_used(key, exclude_group=group,
                                                   exclude_action=action)
        if conflict:
            c_group, c_action = conflict
            c_label = next((lbl for g, a, lbl in _BIND_ROWS
                            if g == c_group and a == c_action), f"{c_group}/{c_action}")
            self.conflict_msg   = f"'{pygame.key.name(key).upper()}' is already used by  {c_label}"
            self.conflict_timer = _CONFLICT_SHOW_FRAMES
            return None

        self.bindings.set(group, action, key)
        return None

    def _reset_row(self) -> None:
        from main.keybindings import _DEFAULTS
        group, action, _ = _BIND_ROWS[self.selected]
        default_key = _DEFAULTS[group][action]
        # Only reset if the default isn't already taken by something else
        conflict = self.bindings.is_key_used(default_key, exclude_group=group, exclude_action=action)
        if conflict:
            c_group, c_action = conflict
            c_label = next((lbl for g, a, lbl in _BIND_ROWS
                            if g == c_group and a == c_action), f"{c_group}/{c_action}")
            self.conflict_msg   = f"Default key is already used by  {c_label}  — reset manually"
            self.conflict_timer = _CONFLICT_SHOW_FRAMES
        else:
            self.bindings.set(group, action, default_key)

   
# --- Helpers --- 
    
    def _draw_text(self, screen: pygame.Surface, text: str, pos: tuple[int, int], color: pygame.Color = None) -> None:
        if color is None:
            color = pygame.Color("white")
        s = self.font.render(text, True, color)
        screen.blit(s, pos)

    def _draw_button_text(self, screen: pygame.Surface, text: str, rect: pygame.Rect, color:pygame.Color = None) -> None:
        if color is None:
             color = pygame.Color("white")
        text_surface = self.font.render(text, True, color)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)

    def _draw_centered(self, screen, text, y, color, big=False):
        font = pygame.font.SysFont(None, 32 if big else 20)
        s = font.render(text, True, color)
        screen.blit(s, (self.w // 2 - s.get_width() // 2, y))


# --- Items ---

_HUD_COLS = 8         # max items per row before wrapping
_HUD_CELL = 36        # px per item cell (sprite is 32×32, 2 px padding each side)
_HUD_PAD  = 6         # padding inside the panel border
_HUD_MARGIN  = 8         # gap from screen edge
_HUD_MAX_ROWS = 3         # panel grows up to this many rows

COL_HUD_BG = pygame.Color(10,  10,  20,  180)   # semi-transparent dark
COL_HUD_BORDER = pygame.Color("#3a3a5c")
COL_HUD_CELL_BG = pygame.Color(30,  30,  50,  200)
COL_HUD_CELL_HL = pygame.Color(80,  80, 120,  200)    # most-recently-added cell


class ItemHUD:
    def __init__(self, screen_w: int, screen_h: int) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h
        self._font = None         

    def draw(self, surface: pygame.Surface, items: list) -> None:
        if self._font is None:
            self._font = pygame.font.SysFont(None, 16)

        num_items= len(items)
        num_cols = _HUD_COLS
        num_rows = max(1, min(_HUD_MAX_ROWS,
                                (num_items + num_cols - 1) // num_cols))

        panel_w = _HUD_PAD * 2 + num_cols * _HUD_CELL
        panel_h = _HUD_PAD * 2 + num_rows * _HUD_CELL + 14 
        panel_x = self.screen_w - panel_w - _HUD_MARGIN - 9
        panel_y = _HUD_MARGIN + 9

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill(COL_HUD_BG)
        pygame.draw.rect(panel_surf, COL_HUD_BORDER, panel_surf.get_rect(), 2, border_radius=4)
        surface.blit(panel_surf, (panel_x, panel_y))

        label = self._font.render("ITEMS", True, pygame.Color("#888888"))
        surface.blit(label, (panel_x + _HUD_PAD, panel_y + 3))

        cell_top   = panel_y + _HUD_PAD + 14
        for idx, item in enumerate(items[:num_rows * num_cols]):
            col = idx % num_cols
            row = idx // num_cols
            cx = panel_x + _HUD_PAD + col * _HUD_CELL
            cy = cell_top + row * _HUD_CELL
            cell_r = pygame.Rect(cx, cy, _HUD_CELL - 2, _HUD_CELL - 2)

            is_newest = (idx == num_items - 1)
            cell_col  = COL_HUD_CELL_HL if is_newest else COL_HUD_CELL_BG

            cell_surf = pygame.Surface((cell_r.width, cell_r.height), pygame.SRCALPHA)
            cell_surf.fill(cell_col)
            pygame.draw.rect(cell_surf, COL_HUD_BORDER, cell_surf.get_rect(), 1, border_radius=2)
            surface.blit(cell_surf, cell_r.topleft)

            sprite = item.sprite
            inset = 2
            target_size = (_HUD_CELL - 2 - inset * 2, _HUD_CELL - 2 - inset * 2)
            scaled = pygame.transform.smoothscale(sprite, target_size)
            surface.blit(scaled, (cx + inset, cy + inset))

        total_slots = num_rows * num_cols
        for idx in range(num_items, total_slots):
            col = idx % num_cols
            row = idx // num_cols
            cx = panel_x + _HUD_PAD + col * _HUD_CELL
            cy = cell_top + row * _HUD_CELL
            cell_r = pygame.Rect(cx, cy, _HUD_CELL - 2, _HUD_CELL - 2)
            slot_surf = pygame.Surface((cell_r.width, cell_r.height), pygame.SRCALPHA)
            slot_surf.fill((20, 20, 35, 160))
            pygame.draw.rect(slot_surf, pygame.Color(50, 50, 70, 200),
                             slot_surf.get_rect(), 1, border_radius=2)
            surface.blit(slot_surf, cell_r.topleft)


# --- PlayerHUD - health bar, active weapon, and ammo thing---
_HP_BAR_W = 200
_HP_BAR_H = 16
_HP_BAR_X = 17
_HP_BAR_Y = 17
_WPN_PANEL_W = 200
_WPN_PANEL_H = 52
_WPN_PAD = 8

COL_HP_BG = pygame.Color(40,  10,  10,  210)
COL_HP_FILL = pygame.Color("#e84040")
COL_HP_FULL = pygame.Color("#44ee44")
COL_HP_BORDER = pygame.Color("#664444")
COL_WPN_BG = pygame.Color(10,  10,  30,  200)
COL_WPN_BORDER = pygame.Color("#3a3a5c")
COL_AMMO_FULL = pygame.Color("#ffe066")
COL_AMMO_EMPTY = pygame.Color("#444422")
COL_RELOAD = pygame.Color("#ff9900")

class PlayerHUD:
    def __init__(self, screen_w: int, screen_h: int) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h
        self._font_sm: pygame.font.Font | None = None
        self._font_md: pygame.font.Font | None = None

        import os
        BASE_DIR = os.path.dirname(__file__)  

        self.coin_empty = pygame.image.load(os.path.join(BASE_DIR, "assets", "sprites", "coin_health.png")).convert_alpha()

        self.coin_full = pygame.image.load(os.path.join(BASE_DIR, "assets", "sprites", "coin_health_active.png")).convert_alpha()

        self.coin_size = 35
        self.coin_empty = pygame.transform.smoothscale(self.coin_empty, (self.coin_size, self.coin_size))
        self.coin_full  = pygame.transform.smoothscale(self.coin_full, (self.coin_size, self.coin_size))
    
    def draw(self, surface: pygame.Surface, player) -> None:
        if self._font_sm is None:
            self._font_sm = pygame.font.SysFont(None, 18)
            self._font_md = pygame.font.SysFont(None, 22)
        
        self._draw_health(surface, player)
        self._draw_weapon(surface, player)
        self._draw_coins(surface, player)
        self._draw_divine_protection(surface, player)

    def _draw_divine_protection(self, surface: pygame.Surface, player) -> None:
        x = self.screen_w - 185
        y = self.screen_h - _HP_BAR_Y - _WPN_PANEL_H - 20

        panel_w, panel_h = 168, _WPN_PANEL_H + _HP_BAR_H + 6
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((12, 12, 34, 200))
        border = pygame.Color("#6f66ff") if player.divine_protection_active else pygame.Color("#444466")
        pygame.draw.rect(panel, border, panel.get_rect(), 2, border_radius=4)
        surface.blit(panel, (x, y))

        title = self._font_sm.render("Divine Protection", True, pygame.Color("#c7c2ff"))
        surface.blit(title, (x + 8, y + 6))

        status = "READY" if player.divine_protection_active else "BROKEN"
        status_col = pygame.Color("#8df0ff") if player.divine_protection_active else pygame.Color("#888888")
        status_surf = self._font_md.render(status, True, status_col)
        surface.blit(status_surf, (x + 8, y + 22))

        reward = "100% COINS" if player.room_flawless else "33% COINS"
        reward_col = pygame.Color("#ffd700") if player.room_flawless else pygame.Color("#999999")
        reward_surf = self._font_sm.render(reward, True, reward_col)
        surface.blit(reward_surf, (x + 8, y + panel_h - reward_surf.get_height() - 8))

    # --- Coins --- 
    def _draw_coins(self, surface: pygame.Surface, player) -> None:
        coins = getattr(player, "coins", 0)
        mult  = getattr(player, "damage_multiplier", 1.0)
 
        x = _HP_BAR_X + _HP_BAR_W + 14
        y = self.screen_h - _HP_BAR_Y - _WPN_PANEL_H - 20
 
        panel_w, panel_h = 130, _WPN_PANEL_H + _HP_BAR_H + 6
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((10, 10, 30, 200))
        pygame.draw.rect(panel, pygame.Color("#4a3a00"), panel.get_rect(), 2, border_radius=4)
        surface.blit(panel, (x, y))
 
        # coin icon (small gold circle)
        pygame.draw.circle(surface, pygame.Color("#ffd700"), (x + 14, y + 14), 7)
        pygame.draw.circle(surface, pygame.Color("#fffacd"), (x + 14, y + 14), 5)
 
        coin_txt = self._font_md.render(str(coins), True, pygame.Color("#ffd700"))
        surface.blit(coin_txt, (x + 26, y + 6))
 
        # damage multiplier below
        col = pygame.Color("#ff6644") if mult >= 5.0 else (pygame.Color("#ffcc00") if mult >= 2.0 else pygame.Color("#aaaaaa"))
        mult_txt = self._font_sm.render(f"DMG  ×{mult:.1f}", True, col)
        surface.blit(mult_txt, (x + 8, y + panel_h - mult_txt.get_height() - 8))


    # --- health ---
    def _draw_health(self, surface: pygame.Surface, player) -> None:
        num_coins = 10

        # position (adjust to fit your UI)
        start_x = _HP_BAR_X
        y = self.screen_h - _HP_BAR_Y - _WPN_PANEL_H - self.coin_size - 6
        spacing = self.coin_size - 20

        ratio = player.currHealth / player.maxHealth
        filled_coins = int(ratio * num_coins)

        for i in range(num_coins):
            x = start_x + i * spacing

            if i < filled_coins:
                surface.blit(self.coin_full, (x, y))
            else:
                surface.blit(self.coin_empty, (x, y))

        # optional text (you already had this)
        label = self._font_sm.render(
            f"{player.currHealth} / {player.maxHealth}", True, pygame.Color("#ffffff")
        )
        surface.blit(label, (start_x, y - 18))


    def _draw_weapon(self, surface: pygame.Surface, player) -> None:
        x = _HP_BAR_X
        y = self.screen_h - _HP_BAR_Y - _WPN_PANEL_H

        panel = pygame.Surface((_WPN_PANEL_W, _WPN_PANEL_H), pygame.SRCALPHA)
        panel.fill(COL_WPN_BG)
        pygame.draw.rect(panel, COL_WPN_BORDER, panel.get_rect(), 2, border_radius=4)
        surface.blit(panel, (x, y))

        weapon = player.current_weapon
        if weapon is None:
            no_wpn = self._font_sm.render("No weapon", True, pygame.Color("#666666"))
            surface.blit(no_wpn, (x + _WPN_PAD, y + _WPN_PANEL_H // 2 - no_wpn.get_height() // 2))
            return

        # weapon name
        name_surf = self._font_md.render(weapon.name, True, pygame.Color("#ffffff"))
        surface.blit(name_surf, (x + _WPN_PAD, y + 6))

        # weapon type 
        if weapon.wtype == "melee":
            badge_text, badge_col = "MELEE", pygame.Color("#ff8888")
        elif weapon.wtype == "aura":
            badge_text, badge_col = "AURA", pygame.Color("#8ac45b")
        else:
            badge_text, badge_col = "RANGED", pygame.Color("#88aaff")
        badge_surf = self._font_sm.render(badge_text, True, badge_col)
        surface.blit(badge_surf, (x + _WPN_PAD, y + 6 + name_surf.get_height() + 2))

        # ammo display
        if weapon.wtype == "ranged":
            self._draw_ammo(surface, weapon, x, y)

        # reload indicator
        if weapon._reloading > 0:
            progress = 1.0 - (weapon._reloading / weapon.RELOAD_TIME)
            rel_w = int((_WPN_PANEL_W - _WPN_PAD * 2) * progress)
            bar_y = y + _WPN_PANEL_H - 6
            pygame.draw.rect(surface, pygame.Color("#333333"), (x + _WPN_PAD, bar_y, _WPN_PANEL_W - _WPN_PAD * 2, 4))
            pygame.draw.rect(surface, COL_RELOAD, (x + _WPN_PAD, bar_y, rel_w, 4))

    def _draw_ammo(self, surface: pygame.Surface, weapon, panel_x, panel_y) -> None:
        if weapon.unlimited_ammo:
            inf_surf = self._font_sm.render("∞", True, COL_AMMO_FULL)
            surface.blit(inf_surf, (panel_x + _WPN_PANEL_W - inf_surf.get_width() - _WPN_PAD,
                                    panel_y + 8))
            return

        # draw bullet in clip
        pip_size = 7
        pip_gap = 3
        max_pips = weapon.clip_size
        per_row = min(max_pips, 15)
        start_x = panel_x + _WPN_PANEL_W - _WPN_PAD - (per_row * (pip_size + pip_gap))
        pip_y = panel_y + 10

        for i in range(max_pips):
            col = i % per_row
            row = i // per_row
            px = start_x + col * (pip_size + pip_gap)
            py = pip_y + row * (pip_size + pip_gap + 1)
            filled = i < weapon.curr_ammo
            pygame.draw.rect(surface, COL_AMMO_FULL if filled else COL_AMMO_EMPTY, (px, py, pip_size, pip_size), 0 if filled else 1,)

        reserve_text = f"x{weapon.reserve_clips}" if weapon.reserve_clips >= 0 else "∞"
        rsv = self._font_sm.render(reserve_text, True, pygame.Color("#aaaaaa"))
        surface.blit(rsv, (panel_x + _WPN_PANEL_W - rsv.get_width() - _WPN_PAD,
                           panel_y + _WPN_PANEL_H - rsv.get_height() - 4))
        


class PauseMenu:
    def __init__(self, screen_w: int, screen_h: int, music_manager, sound_manager) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.music_manager = music_manager
        self.sound_manager = sound_manager
        
        self._font_title = pygame.font.SysFont(None, 72)
        self._font_label = pygame.font.SysFont(None, 28)
        self._font_hint = pygame.font.SysFont(None, 20)

        self.slider_width = 300
        self.slider_height = 12
        self.handle_radius = 10

        center_x = screen_w // 2
        start_y = screen_h // 2 - 60
        spacing = 70

        #different volume sliders
        self.sliders = [
            {
                "label": "Master Volume",
                "y": start_y,
                "get": lambda: self._get_master_volume(),
                "set": lambda v: self._set_master_volume(v),
            },
            {
                "label": "Music Volume",
                "y": start_y + spacing,
                "get": lambda: self.music_manager.volume,
                "set": lambda v: self.music_manager.set_volume(v),
            },
            {
                "label": "SFX Volume",
                "y": start_y + spacing * 2,
                "get": lambda: self.sound_manager.volume,
                "set": lambda v: self.sound_manager.set_volume(v),
            },
        ]

        btn_w, btn_h = 200, 50
        self.quit_button = pygame.Rect(
            center_x - btn_w // 2,
            start_y + spacing * 3 + 30,
            btn_w,
            btn_h
        )

        self.dragging_slider = None
        self.quit_hovered = False

        #some getters/setters

    def _get_master_volume(self) -> float:
        return (self.music_manager.volume + self.sound_manager.volume) / 2.0
        
    def _set_master_volume(self, value: float) -> None:
        self.music_manager.set_volume(value)
        self.sound_manager.set_volume(value)
    
    def _get_slider_rect(self, y: int) -> pygame.Rect:
        return pygame.Rect(self.screen_w // 2 - self.slider_width // 2, y, self.slider_width, self.slider_height)
    
    #handlers
    def _get_handle_pos(self, slider_rect: pygame.Rect, value: float) -> tuple[int, int]:
        x = slider_rect.x + int(slider_rect.width * value)
        y = slider_rect.centery
        return (x, y)
    
    def _handle_mouse_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Check if clicking on quit button
            if self.quit_button.collidepoint(mouse_pos):
                return "quit"
            
            # Check if clicking on any slider handle
            for i, slider in enumerate(self.sliders):
                slider_rect = self._get_slider_rect(slider["y"])
                value = slider["get"]()
                handle_x, handle_y = self._get_handle_pos(slider_rect, value)

                dist = math.hypot(mouse_pos[0] - handle_x, mouse_pos[1] - handle_y)
                if dist <= self.handle_radius:
                    self.dragging_slider = i
                    return None
                
                # Check if clicking on slider bar (jump to position)
                if slider_rect.collidepoint(mouse_pos):
                    self.dragging_slider = i
                    new_value = (mouse_pos[0] - slider_rect.x) / slider_rect.width
                    new_value = max(0.0, min(1.0, new_value))
                    slider["set"](new_value)
                    return None
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_slider = None
        
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            
            self.quit_hovered = self.quit_button.collidepoint(mouse_pos)
            
            if self.dragging_slider is not None:
                slider = self.sliders[self.dragging_slider]
                slider_rect = self._get_slider_rect(slider["y"])
                
                new_value = (mouse_pos[0] - slider_rect.x) / slider_rect.width
                new_value = max(0.0, min(1.0, new_value))
                slider["set"](new_value)
        
        return None

    def draw(self, surface: pygame.Surface, events: list[pygame.event.Event]) -> str | None:
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))
        
        title = self._font_title.render("PAUSED", True, pygame.Color("#ffffff"))
        surface.blit(title, (self.screen_w // 2 - title.get_width() // 2, 80))
        
        action = None
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    return "resume"
                elif event.key == pygame.K_ESCAPE:
                    return "quit"
            
            mouse_action = self._handle_mouse_event(event)
            if mouse_action:
                action = mouse_action
        
        # Draw sliders
        for slider in self.sliders:
            y = slider["y"]
            value = slider["get"]()
            
            label = self._font_label.render(slider["label"], True, pygame.Color("#e0e0e0"))
            surface.blit(label, (self.screen_w // 2 - label.get_width() // 2, y - 30))
            
            slider_rect = self._get_slider_rect(y)
            pygame.draw.rect(surface, pygame.Color("#333344"), slider_rect, border_radius=6)
            
            # Filled portion
            filled_width = int(slider_rect.width * value)
            if filled_width > 0:
                filled_rect = pygame.Rect(slider_rect.x, slider_rect.y, filled_width, slider_rect.height)
                pygame.draw.rect(surface, pygame.Color("#4fc3f7"), filled_rect, border_radius=6)
            
            handle_x, handle_y = self._get_handle_pos(slider_rect, value)
            pygame.draw.circle(surface, pygame.Color("#ffffff"), (handle_x, handle_y), self.handle_radius)
            pygame.draw.circle(surface, pygame.Color("#4fc3f7"), (handle_x, handle_y), self.handle_radius - 2)
            
            percent_text = f"{int(value * 100)}%"
            percent_surf = self._font_label.render(percent_text, True, pygame.Color("#aaaaaa"))
            surface.blit(percent_surf, (slider_rect.right + 20, y - percent_surf.get_height() // 2 + 6))
        
        #Quit button
        btn_color = pygame.Color("#663333") if self.quit_hovered else pygame.Color("#442222")
        pygame.draw.rect(surface, btn_color, self.quit_button, border_radius=8)
        
        border_color = pygame.Color("#ff4444") if self.quit_hovered else pygame.Color("#884444")
        pygame.draw.rect(surface, border_color, self.quit_button, 2, border_radius=8)
        
        quit_text = self._font_label.render("Quit to Menu", True, pygame.Color("#ffffff"))
        quit_text_rect = quit_text.get_rect(center=self.quit_button.center)
        surface.blit(quit_text, quit_text_rect)
        
        return action
    