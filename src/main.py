import pygame

from sprites_collisions.game import Game


def main() -> None:
    pygame.init()
    pygame.mixer.init()
    pygame.display.set_caption("Jacob and Gabe - Group Project")

    game = Game()
    clock = pygame.time.Clock()

    running = True
    while running:
        dt = clock.tick(game.fps) / 1000.0
        dt = min(dt, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(event)

        game.update(dt)
        game.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()