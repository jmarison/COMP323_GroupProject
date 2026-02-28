from __future__ import annotations
import pygame

TITLE_BUTTONS = ["Start", "Settings", "Quit"]

class TitleScreen:
    def __init__(self, w: int, h: int, font: pygame.font.Font):
        self.w = w
        self.h = h
        self.font = font

        self.selected = 0 #index

        self.button_rects = [
            pygame.Rect(50, 100, 200, 50),
            pygame.Rect(50, 200, 200, 50),
            pygame.Rect(50, 300, 200, 50),
        ]

    def draw(self, screen: pygame.Surface, events: list[pygame.event.Event]) -> str | None:
        screen.fill(pygame.Color("#808080"))
        self._draw_text(screen, "super cool game title", (self.w // 2, self.h // 6), pygame.Color("white"))

        action = None
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_s, pygame.K_DOWN):
                    self.selected = (self.selected + 1) % len(TITLE_BUTTONS)
                elif event.key in (pygame.K_w, pygame.K_UP):
                    self.selected = (self.selected - 1) % len(TITLE_BUTTONS)
                elif event.key == pygame.K_SPACE:
                    action = TITLE_BUTTONS[self.selected].lower()

        # Draw buttons
        for i, (label, rect) in enumerate(zip(TITLE_BUTTONS, self.button_rects)):
            color = (255, 200, 0) if i == self.selected else (255, 0, 0)
            pygame.draw.rect(screen, color, rect)
            if i == self.selected:
                pygame.draw.rect(screen, (255, 255, 255), rect, 3)
            self._draw_button_text(screen, label, rect)

        return action



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