from __future__ import annotations
from pathlib import Path
import pygame

_SFX_DIR = Path(__file__).parent / "assets" / "sfx"


_WEAPON_SOUNDS: dict[str, str] = {
    # --- melee (all melees get the same sfx for now) ---
    "dagger": "swing.mp3",
    "broadsword": "swing.mp3",
    "war hammer": "swing.mp3",
    "scythe": "swing.mp3",
    # --- ranged ---
    "pistol": "pistol.mp3",
    "shotgun" :"pistol.mp3",  # placeholder
    "smg": "pistol.mp3",   # placeholder
    "sniper rifle": "pistol.mp3",  # placeholder
    "grenade launcher": "pistol.mp3", # placeholder
}

_MAX_CHANNELS = 8


class SoundManager:
    def __init__(self, volume: float = 0.4) -> None:
        self.volume = volume
        self._cache: dict[str, pygame.mixer.Sound | None] = {}

        pygame.mixer.set_num_channels(max(pygame.mixer.get_num_channels(), _MAX_CHANNELS + 4))

    # -------------------------------- play----------------------------------
    def play_weapon(self, weapon_name: str) -> None:
        key = weapon_name.lower()
        filename = _WEAPON_SOUNDS.get(key)
        if filename is None:
            return  # unknown weapon 

        sound = self._load(filename)
        if sound is None:
            return

        sound.play()

    # --------------------------- load ---------------------------------------
    def _load(self, filename: str) -> pygame.mixer.Sound | None:
        
        if filename in self._cache:
            return self._cache[filename]

        path = _SFX_DIR / filename
        if not path.exists():
            print(f"[SoundManager] Missing SFX file: {path}")
            self._cache[filename] = None
            return None

        try:
            sound = pygame.mixer.Sound(str(path))
            sound.set_volume(self.volume)
            self._cache[filename] = sound
            return sound
        except pygame.error as e:
            print(f"[SoundManager] Could not load {path}: {e}")
            self._cache[filename] = None
            return None

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))
        for sound in self._cache.values():
            if sound is not None:
                sound.set_volume(self.volume)