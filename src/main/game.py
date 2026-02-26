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
    title_background: pygame.Color = field(default_factory=lambda: pygame.Color("#808080"))

PALETTE = Palette()


class Game:

    def __init__(self):
        self.fps    = 60
        self.w      = 960
        self.h      = 540
        self.screen = pygame.display.set_mode((self.w, self.h))
        self.font   = pygame.font.SysFont(None, 24)

        self.Player = Player((self.w // 2, self.h // 2))

        self.state: str = "title"   # title | playing | gameover | paused
        self.seed  = random.randrange(0, 2**32)
        self.rng   = random.Random(self.seed)

        self.debug = False   # toggle with F1 to see loading zones

        self.events: list[pygame.event.Event] = []
        self._reset_run()

    # -------------------------------- reset  -------------------------------------- #

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

    # ------------------------------ Events ---------------------------------------- #

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
 # ------------------------------ Update ---------------------------------------- #

    def update(self, dt: float) -> None:
       
        if self.state == "playing":
            keys = pygame.key.get_pressed()
            self.Player.update(dt, keys, self.events)
            self.dungeon.update(self.Player)

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


    def _draw_playing(self) -> None:
        # Draw the active room first, then the player on top for layering
        self.dungeon.draw(self.screen, debug=self.debug)
        self.Player.draw(self.screen)
        self._draw_dungeon_debug()

    def _draw_title(self) -> None:
        self.screen.fill(PALETTE.title_background)
        self._draw_text("super cool game title", (self.w // 2, self.h // 6), pygame.Color("white"))
        mx, my = pygame.mouse.get_pos()

        start_game_button = pygame.Rect(50, 100, 200, 50)
        settings_button = pygame.Rect(50, 200, 200, 50)
        quit_button = pygame.Rect(50, 300, 200, 50)

        click = False 
        for event in self.events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    click = True
            else:
             click = False

        if start_game_button.collidepoint((mx, my)):
            if click:
                self.state = "playing"
                
        if settings_button.collidepoint((mx, my)):
             if click:
                click = False 
                
        if quit_button.collidepoint((mx, my)):
            if click:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

        pygame.draw.rect(self.screen, (255, 0, 0), start_game_button)
        pygame.draw.rect(self.screen, (255, 0, 0), settings_button)
        pygame.draw.rect(self.screen, (255, 0, 0), quit_button)

        self._draw_button_text("Start", start_game_button, pygame.Color("white"))
        self._draw_button_text("Settings", settings_button, pygame.Color("white"))
        self._draw_button_text("Quit", quit_button, pygame.Color("white"))


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
    
    def _draw_text(self, text: str, pos: tuple[int, int], color: pygame.Color) -> None:
        s = self.font.render(text, True, color)
        self.screen.blit(s, pos)

    def _draw_button_text(self, text: str, rect: pygame.Rect, color:pygame.Color) -> None:
        text_surface = self.font.render(text, True, color)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
