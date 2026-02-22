from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import random
import json

import pygame
from main.player import Player


@dataclass (frozen = True)
class Palette:
    background: pygame.Color  = field(default_factory=lambda: pygame.Color("#060606"))
    
PALETTE = Palette()

class Game:
    
    def __init__(self):
        self.fps = 60
        self.w = 960
        self.h = 540
        self.screen = pygame.display.set_mode((self.w, self.h))
        self.font = pygame.font.SysFont(None, 24)

        self.Player = Player((self.w // 2, self.h //2 ))


        self.state : str = "playing" # title | playing | gameover | paused 
        self.seed = random.randrange(0, 2**32)
        self.rng = random.Random(self.seed)

        self._reset_run()
        

    def _reset_run(self) -> None:
        self.Player._reset()

    def handle_event(self, event: pygame.event.Event) -> bool:
        self.events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
            self.events.append(event)
        return True

    def update(self, dt: float) -> None:
        if self.state != "playing":
            return
        keys = pygame.key.get_pressed()
        self.Player.update(dt, keys, self.events)

    def draw(self) -> None:
        self.screen.fill(PALETTE.background)
        if self.state == "title":
            self._draw_title()
        elif self.state == "playing":
            self._draw_playing()
        elif self.state == "paused":
            self._draw_paused()
        else:
            self._draw_gameover()

    def _draw_title(self) -> None:
        pass

    def _draw_playing(self) -> None:
        self.Player.draw(self.screen)

    def _draw_paused(self) -> None:
        pass

    def _draw_gameover(self) -> None:
        pass
