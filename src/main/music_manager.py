from __future__ import annotations
from pathlib import Path
import pygame

_MUSIC_DIR = Path(__file__).parent / "assets" / "music"

_TRACKS: dict[str, str] = {
    "title": str(_MUSIC_DIR / "title_music.mp3"),
    "background": str(_MUSIC_DIR / "background_music.mp3"),
}


class MusicManager:

    FADE_MS = 1500   # crossfade duration in milliseconds

    def __init__(self, volume: float = 0.5) -> None:
        self._current: str | None = None
        self.volume = volume
        pygame.mixer.music.set_volume(volume)

    def play(self, track_key: str, loop: bool = True) -> None:
        if track_key == self._current:
            return
        path = _TRACKS.get(track_key)
        if path is None:
            return
        pygame.mixer.music.fadeout(self.FADE_MS)
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(self.volume)
        pygame.mixer.music.play(-1 if loop else 0, fade_ms=self.FADE_MS)
        self._current = track_key

    def stop(self) -> None:
        pygame.mixer.music.fadeout(self.FADE_MS)
        self._current = None

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)