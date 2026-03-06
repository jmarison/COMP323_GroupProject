from __future__ import annotations
import pygame



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
        title_surf = title_font.render("super cool game title", True, pygame.Color("#e0e0e0"))
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

_HUD_COLS = 5         # max items per row before wrapping
_HUD_CELL = 36        # px per item cell (sprite is 32×32, 2 px padding each side)
_HUD_PAD  = 6         # padding inside the panel border
_HUD_MARGIN  = 8         # gap from screen edge
_HUD_MAX_ROWS = 3         # panel grows up to this many rows

COL_HUD_BG         = pygame.Color(10,  10,  20,  180)   # semi-transparent dark
COL_HUD_BORDER     = pygame.Color("#3a3a5c")
COL_HUD_CELL_BG    = pygame.Color(30,  30,  50,  200)
COL_HUD_CELL_HL    = pygame.Color(80,  80, 120,  200)    # most-recently-added cell


class ItemHUD:
    def __init__(self, screen_w: int, screen_h: int) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h
        self._font    = None         

    def draw(self, surface: pygame.Surface, items: list) -> None:
        if self._font is None:
            self._font = pygame.font.SysFont(None, 16)

        num_items  = len(items)
        num_cols   = _HUD_COLS
        num_rows   = max(1, min(_HUD_MAX_ROWS,
                                (num_items + num_cols - 1) // num_cols))

        panel_w = _HUD_PAD * 2 + num_cols * _HUD_CELL
        panel_h = _HUD_PAD * 2 + num_rows * _HUD_CELL + 14 
        panel_x = self.screen_w  - panel_w  - _HUD_MARGIN
        panel_y = _HUD_MARGIN

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill(COL_HUD_BG)
        pygame.draw.rect(panel_surf, COL_HUD_BORDER, panel_surf.get_rect(), 2, border_radius=4)
        surface.blit(panel_surf, (panel_x, panel_y))

        label      = self._font.render("ITEMS", True, pygame.Color("#888888"))
        surface.blit(label, (panel_x + _HUD_PAD, panel_y + 3))

        cell_top   = panel_y + _HUD_PAD + 14
        for idx, item in enumerate(items[:num_rows * num_cols]):
            col    = idx % num_cols
            row    = idx // num_cols
            cx     = panel_x + _HUD_PAD + col * _HUD_CELL
            cy     = cell_top + row * _HUD_CELL
            cell_r = pygame.Rect(cx, cy, _HUD_CELL - 2, _HUD_CELL - 2)

            is_newest = (idx == num_items - 1)
            cell_col  = COL_HUD_CELL_HL if is_newest else COL_HUD_CELL_BG

            cell_surf = pygame.Surface((cell_r.width, cell_r.height), pygame.SRCALPHA)
            cell_surf.fill(cell_col)
            pygame.draw.rect(cell_surf, COL_HUD_BORDER,
                             cell_surf.get_rect(), 1, border_radius=2)
            surface.blit(cell_surf, cell_r.topleft)

            sprite      = item.sprite
            inset       = 2
            target_size = (_HUD_CELL - 2 - inset * 2, _HUD_CELL - 2 - inset * 2)
            scaled      = pygame.transform.smoothscale(sprite, target_size)
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
