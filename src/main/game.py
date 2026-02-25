from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import random
import json

import pygame
from main.player import Player
from main.dungeon_generator import DungeonGenerator


@dataclass(frozen=True)
class Palette:
    background: pygame.Color = field(default_factory=lambda: pygame.Color("#060606"))

PALETTE = Palette()


class Game:

    def __init__(self):
        self.fps    = 60
        self.w      = 960
        self.h      = 540
        self.screen = pygame.display.set_mode((self.w, self.h))
        self.font   = pygame.font.SysFont(None, 24)

        self.Player = Player((self.w // 2, self.h // 2))

        self.state: str = "playing"   # title | playing | gameover | paused
        self.seed  = random.randrange(0, 2**32)
        self.rng   = random.Random(self.seed)

        self.debug = False   # toggle with F1 to see loading zones

        self.events: list[pygame.event.Event] = []
        self._reset_run()

    # ---------------------------------------------------------------------- #

    def _reset_run(self) -> None:
        self.Player._reset()

        # --- Generate a fresh dungeon ---
        gen = DungeonGenerator(
            seed             = self.seed,
            num_normal_rooms = 6,
            screen_size      = (self.w, self.h),
        )
        self.dungeon = gen.generate()

        # Place player at the centre of the start room
        self.Player.pos = pygame.Vector2(self.w // 2, self.h // 2)
        self.Player.rect.center = (self.w // 2, self.h // 2)

    # ---------------------------------------------------------------------- #

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                return
            if event.key == pygame.K_F1:
                self.debug = not self.debug
            if event.key == pygame.K_r:
                self.seed = random.randrange(0, 2**32)
                self._reset_run()
        self.events.append(event)
        return 

    def update(self, dt: float) -> None:
        if self.state != "playing":
            return
        keys = pygame.key.get_pressed()
        self.Player.update(dt, keys, self.events)
        # Check room transitions
        self.dungeon.update(self.Player)
        self.events = []

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
        # Draw the active room first, then the player on top
        self.dungeon.draw(self.screen, debug=self.debug)
        self.Player.draw(self.screen)
        self._draw_dungeon_debug()


    def _draw_paused(self) -> None:
        pass

    def _draw_gameover(self) -> None:
        pass

    def _draw_dungeon_debug(self) -> None:
        if self.debug:
            room = self.dungeon.current_room
            info = self.font.render(
                f"Room {room.id} | {room.type.value.upper()} | F1=debug  R=regenerate dungeon",
                True, pygame.Color("#ffffff"),
            )
            self.screen.blit(info, (8, self.h - 28))