from __future__ import annotations
import json
from pathlib import Path
import pygame

_DEFAULTS: dict[str, dict[str, int]] = {
    "move": {
        "left":  pygame.K_a,
        "right": pygame.K_d,
        "up":    pygame.K_w,
        "down":  pygame.K_s,
    },
    "aim": {
        "left":  pygame.K_LEFT,
        "right": pygame.K_RIGHT,
        "up":    pygame.K_UP,
        "down":  pygame.K_DOWN,
    },
    "actions": {
        "weapon_next":  pygame.K_e,
        "weapon_prev":  pygame.K_q,
        "weapon_slot1": pygame.K_1,
        "weapon_slot2": pygame.K_2,
    },
}

SETTINGS_PATH = Path("settings.json")


class KeyBindings:
    def __init__(self, data: dict[str, dict[str, int]] | None = None) -> None:
        self._bindings: dict[str, dict[str, int]] = {
            group: dict(keys) for group, keys in _DEFAULTS.items()
        }
        if data:
            for group, keys in data.items():
                if group in self._bindings:
                    self._bindings[group].update(keys)

    @classmethod
    def load(cls) -> "KeyBindings":
        #loading from settings.json for controls
        if SETTINGS_PATH.exists():
            try:
                return cls(json.loads(SETTINGS_PATH.read_text()))
            except Exception:
                pass
        return cls()

    def save(self) -> None:
        SETTINGS_PATH.write_text(json.dumps(self._bindings, indent=2))

    def get(self, group: str, action: str) -> int:
        return self._bindings[group][action]

    def set(self, group: str, action: str, key: int) -> None:
        self._bindings[group][action] = key

    def is_key_used(self, key: int, exclude_group: str = "", exclude_action: str = "") -> tuple[str, str] | None:
        for group, actions in self._bindings.items():
            for action, bound_key in actions.items():
                if bound_key == key:
                    if group == exclude_group and action == exclude_action:
                        continue
                    return (group, action) #if conflict
        return None

    # --- helpers ---
    def move_keys(self)    -> dict[str, set[int]]:
        return {d: {k} for d, k in self._bindings["move"].items()}

    def aim_keys(self)     -> dict[str, set[int]]:
        return {d: {k} for d, k in self._bindings["aim"].items()}

    def action_keys(self)  -> dict[str, set[int]]:
        return {a: {k} for a, k in self._bindings["actions"].items()}