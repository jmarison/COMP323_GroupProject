from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

import pygame


@dataclass (frozen = True)
class Palette:
    background: pygame.Color  = field(default_factory=lambda: pygame.Color("#060606"))
    
def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))

class Wall(pygame.sprite.Sprite):
    def __init__(self, rect: pygame.Rect, color: pygame.Color) -> None:
        super().__init__()
        self.rect = rect.copy()
        self.color = color