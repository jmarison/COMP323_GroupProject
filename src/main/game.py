from __future__ import annotations
from dataclasses import dataclass, field
import random
import pygame
import copy
from main.player import Player
from main.dungeon_generator import DungeonGenerator
from main.ui import TitleScreen, SettingsMenu, ItemHUD, PlayerHUD, PauseMenu
from main.keybindings import KeyBindings
from main.weapon import WEAPON_CATALOGUE
from main.music_manager import MusicManager
from main.sound_manager import SoundManager
from main.entities import Coin
from main.ui import RoomTransition



@dataclass(frozen=True)
class Palette:
    background: pygame.Color = field(default_factory=lambda: pygame.Color("#060606"))
    title_background: pygame.Color = field(default_factory=lambda: pygame.Color("#808080"))

PALETTE = Palette()

transition_duration = 0.3

class Game:

    def __init__(self):
        self.fps = 60
        self.w = 960
        self.h = 540
        self.screen = pygame.display.set_mode((self.w, self.h))
        self.font = pygame.font.SysFont(None, 24)

        self.music = MusicManager(volume=0.1)
        self.music.play("title")
        self.sounds = SoundManager(volume=0.15)

        self.bindings = KeyBindings.load()
        self.Player = Player((self.w // 2, self.h // 2), self.bindings,  sound_manager=self.sounds)

        self.state: str = "title"   # title | settings | playing | gameover | paused
        self.seed = random.randrange(0, 2**32)
        self.rng = random.Random(self.seed)
        self.current_floor = 1

        self.debug = False   # toggle with F1 to see loading zones

      

        self.title_screen = TitleScreen(self.w, self.h, self. font)
        self.settings_menu = SettingsMenu(self.w, self.h, self. font, self.bindings)
        self.pause_menu = PauseMenu(self.w, self.h, self.music, self.sounds)
        self.item_hud = ItemHUD(self.w, self.h)
        self.player_hud = PlayerHUD(self.w, self.h)

        self.room_transition = RoomTransition(self.w, self.h, transition_duration)
        self.events: list[pygame.event.Event] = []
        self._reset_run()

    # -------------------------------- reset  -------------------------------------- #

    def _reset_run(self) -> None:
        self.seed = random.randrange(0, 2**32)
        self.current_floor = 1
        self.Player._reset()
        #player starting weapons
        self.Player.add_weapon(copy.copy(WEAPON_CATALOGUE[4]))
        self.Player.add_weapon(copy.copy(WEAPON_CATALOGUE[10]))

        # --- Generate a fresh dungeon ---
        gen = DungeonGenerator(
            seed = self.seed,
            num_normal_rooms = 6,
            screen_size = (self.w, self.h),
            floor_number = self.current_floor
        )
        self.dungeon = gen.generate()

        self.room_coins: list[Coin] = []

        # Place player at the center of the start room
        self.Player.pos = pygame.Vector2(self.w // 2, self.h // 2)
        self.Player.rect.center = (self.w // 2, self.h // 2)
        self.Player.hitbox.center = self.Player.rect.center
        self.Player.start_room_protection()

# --- next level --- (player keeps items/weapons/coins/etc)
    def _advance_to_next_dungeon(self) -> None:
        self.seed = random.randrange(0, 2**32)
        self.current_floor += 1

        gen = DungeonGenerator(
            seed=self.seed,
            num_normal_rooms=6,
            screen_size=(self.w, self.h),
            floor_number=self.current_floor
        )
        self.dungeon = gen.generate()
        self.room_coins = []

        self.Player.pos = pygame.Vector2(self.w // 2, self.h // 2)
        self.Player.rect.center = (self.w // 2, self.h // 2)
        self.Player.hitbox.center = self.Player.rect.center
        self.Player.start_room_protection()
        #player heals to full between floors
        self.Player.currHealth = self.Player.maxHealth

    # ------------------------------ Events ---------------------------------------- #

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and self.state == "playing":
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                return
            if event.key == pygame.K_F1:
                self.debug = not self.debug
            if event.key == pygame.K_y:
                self.seed = random.randrange(0, 2**32)
                self._reset_run()
            if event.key == pygame.K_p and self.state in ("playing", "paused"):
                self.state = "paused" if self.state == "playing" else "playing"
            if event.key == pygame.K_SPACE and self.state == "gameover":
                self._reset_run()
                self.state = "playing"
                self.music.play("background")

        self.events.append(event)
        return 
    
 # ------------------------------ Update ---------------------------------------- #

    def update(self, dt: float) -> None:
        self.room_transition.update(dt)
       
        if self.state == "playing":
            #prevents anything from moving during transitions
            if self.room_transition.is_active():
                return
            
            keys = pygame.key.get_pressed()
            self.Player.update(dt, keys, self.events)
            self.Player.wall_collisions(self.dungeon.current_room.all_walls)

            result = self.dungeon.current_room.check_transition(self.Player.hitbox)
            if result is not None:
                direction, target_id = result

                def change_room():
                    self.dungeon.current_id = target_id
                    self.Player.pos = self.dungeon._entry_position(direction.opposite())
                    self.Player.rect.center = (round(self.Player.pos.x), round(self.Player.pos.y))
                    self.Player.hitbox.center = self.Player.rect.center
                    self.dungeon.current_room.on_player_enter()
                    self._on_room_enter()
                
                        # Start the transition
                self.room_transition.start(on_peak_callback=change_room)
                return
            self.dungeon.current_room.update(dt, self.Player)

            walls = self.dungeon.current_room.all_walls
            enemies = self.dungeon.current_room.enemies
            flawless_drop_chance = 1.0 if self.Player.room_flawless else 0.33

            for enemy in enemies:
                if enemy.alive and enemy.hitbox.colliderect(self.Player.hitbox):
                    self.Player.take_damage(enemy.damage)

            for bullet in self.Player.bullets:
                bullet.update(dt, walls)
                for enemy in enemies:
                    if enemy.alive:
                        hit = bullet.try_hit(enemy)
                        if hit:
                            self.Player.on_enemy_hit(enemy)
                        if hit and not enemy.alive:
                            self.Player.on_enemy_killed()
                            coin = enemy.try_drop_coin(flawless_drop_chance)
                            if coin:
                                self.room_coins.append(coin)
            
            for mh in self.Player.melee_hitboxes:
                mh.update(dt)
                for enemy in enemies:
                    if enemy.alive:
                        hit = mh.try_hit(enemy)
                        if hit:
                            self.Player.on_enemy_hit(enemy)
                        if hit and not enemy.alive:
                            self.Player.on_enemy_killed()
                            coin = enemy.try_drop_coin(flawless_drop_chance)
                            if coin:
                                self.room_coins.append(coin)

            self.Player.bullets = [b for b in self.Player.bullets if b.alive]
            self.Player.melee_hitboxes = [mh for mh in self.Player.melee_hitboxes if mh.alive]

            # Persistent aura damage (always-on while aura weapon is equipped)
            aura = self.Player._active_aura
            if aura is not None and aura.alive:
                for enemy in enemies:
                    if enemy.alive:
                        hit = aura.try_hit(enemy)
                        if hit:
                            self.Player.on_enemy_hit(enemy)
                        if hit and not enemy.alive:
                            self.Player.on_enemy_killed()
                            coin = enemy.try_drop_coin(flawless_drop_chance)
                            if coin:
                                self.room_coins.append(coin)

            self.dungeon.current_room.refresh_clear_state()

            magnet_radius = self.Player.coin_magnet_radius
            for coin in self.room_coins:
                collected = coin.update(dt, self.Player.rect, magnet_radius=magnet_radius)
                if collected:
                    self.Player.coins += 1
            self.room_coins = [c for c in self.room_coins if c.alive]

            if self.Player.is_dead:
                self.state = "gameover"

            if self.dungeon.current_room.boss_goal_reached(self.Player.hitbox):
                self._advance_to_next_dungeon()
                return

    def _on_room_enter(self) -> None:
        self.room_coins = []
        self.Player.bullets.clear()
        self.Player.melee_hitboxes.clear()
        self.Player.aura_hitboxes.clear()
        # Reset the persistent aura so it re-initialises in the new room
        self.Player._active_aura = None
        self.Player.start_room_protection()

# ------------------------------ Draw ---------------------------------------- #
    def draw(self) -> None:
        self.screen.fill(PALETTE.background)
        if self.state == "title":
            self._draw_title()
        elif self.state == "playing":
            self._draw_playing()
        elif self.state == "paused":
            self._draw_paused()
        elif self.state == "settings":
            self._draw_settings()
        else:
            self._draw_gameover()

        self.events.clear()

# --- Draw states --- 
    def _draw_playing(self) -> None:
        # Draw the active room first, then the player on top for layering
        self.dungeon.draw(self.screen, debug=self.debug)
        for coin in self.room_coins:
            coin.draw(self.screen)
        self.Player.draw(self.screen, debug = self.debug)
        self.item_hud.draw(self.screen, self.Player.items)
        self.player_hud.draw(self.screen, self.Player)
        self._draw_dungeon_debug()
        self.room_transition.draw(self.screen)

    def _draw_title(self) -> None:
        action = self.title_screen.draw(self.screen, self.events)
        if action == "start":
            self.state = "playing"
            self.music.play("background")
        if action == "settings":
            self.state = "settings"
        elif action == "quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _draw_settings(self) -> None:
        action = self.settings_menu.draw(self.screen, self.events)
        if action == "back":
            self.state = "title"

    def _draw_paused(self) -> None:
        self._draw_playing()   # still shows game underneath
        action = self.pause_menu.draw(self.screen, self.events)
        if action == "quit":
            self.state = "title"
            self.music.play("title")

    def _draw_gameover(self) -> None:
        self._draw_playing()
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        go_font = pygame.font.SysFont(None, 72)
        text = go_font.render("GAME OVER", True, pygame.Color("#ff4444"))
        self.screen.blit(text, (self.w // 2 - text.get_width() // 2, self.h // 2 - text.get_height() // 2))
        hint_font = pygame.font.SysFont(None, 28)
        hint = hint_font.render("SPACE / Y  —  New Run", True, pygame.Color("#aaaaaa"))
        self.screen.blit(hint, (self.w // 2 - hint.get_width() // 2, self.h // 2 + 50))

    def _draw_dungeon_debug(self) -> None:
        if self.debug:
            room = self.dungeon.current_room
            info = self.font.render(
                f"Room {room.id} | {room.type.value.upper()} | F1=debug  Y=regenerate dungeon",
                True, pygame.Color("#ffffff"),
            )
            self.screen.blit(info, (8, self.h - 28))

    # ------ Draw Helpers -------
    def _draw_text(self, text: str, pos: tuple[int, int], color: pygame.Color) -> None:
        s = self.font.render(text, True, color)
        self.screen.blit(s, pos)

    def _draw_button_text(self, text: str, rect: pygame.Rect, color:pygame.Color) -> None:
        text_surface = self.font.render(text, True, color)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)