# main.py
import pygame
import random
import sys
from game.settings import *
from game.state import GameState
from game.sprites.player import Player
from game.sprites.bullet import Bullet
from game.sprites.explosion import Explosion
from game.systems.spawner import Spawner
from game.systems.collision import (
    check_bullet_enemy_collisions,
    check_player_enemy_collisions,
)
from game.graphics.hud import draw_hud, draw_menu_screen, draw_game_over_screen
from game.sounds.sound_manager import SoundManager


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.state = GameState()
        self.running = True
        self.menu_selection = 0  # 0 = START GAME, 1 = EXIT

        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.player_group = pygame.sprite.GroupSingle()
        self.bullets_group = pygame.sprite.Group()
        self.enemies_group = pygame.sprite.Group()
        self.explosions_group = pygame.sprite.Group()

        # Game systems
        self.player = Player()
        self.spawner = Spawner()
        self.sound_manager = SoundManager()

        # Starfield
        self.stars = []
        for _ in range(STAR_COUNT):
            self.stars.append({
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(0, SCREEN_HEIGHT),
                "speed": random.uniform(1, STAR_SPEED + 2),
                "size": random.randint(1, 3),
                "brightness": random.randint(100, 255),
            })

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state.is_menu():
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.menu_selection = (self.menu_selection - 1) % 2
                        self.sound_manager.play("shoot")
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.menu_selection = (self.menu_selection + 1) % 2
                        self.sound_manager.play("shoot")
                    elif event.key == pygame.K_RETURN:
                        if self.menu_selection == 0:
                            self._start_game()
                        else:
                            self.running = False
                elif self.state.is_game_over():
                    if event.key == pygame.K_RETURN:
                        self._start_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                elif self.state.is_playing():
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

    def _start_game(self):
        """Reset and start a new game."""
        self.state.set(GameState.PLAYING)
        self.bullets_group.empty()
        self.enemies_group.empty()
        self.explosions_group.empty()
        self.player.reset()
        self.spawner.reset()

    def update(self):
        if self.state.is_playing():
            self._update_stars()
            self._handle_shooting()
            self.player.update(pygame.key.get_pressed())
            self.bullets_group.update()
            self.enemies_group.update()
            self.explosions_group.update()
            self.spawner.update(self.enemies_group, self.player.score)

            # Collision detection
            score = check_bullet_enemy_collisions(
                self.bullets_group, self.enemies_group, self.explosions_group
            )
            if score > 0:
                self.player.score += score
                self.sound_manager.play("explosion")

            hit = check_player_enemy_collisions(
                self.player, self.enemies_group, self.explosions_group
            )
            if hit:
                self.sound_manager.play("hit")
                if self.player.lives <= 0:
                    self.state.set(GameState.GAME_OVER)
                    self.sound_manager.play("game_over")

    def _handle_shooting(self):
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_SPACE] or keys[pygame.K_z]) and self.player.can_shoot():
            bullet = Bullet(self.player.rect.centerx, self.player.rect.top)
            self.bullets_group.add(bullet)
            self.player.shoot()
            self.sound_manager.play("shoot")

    def _update_stars(self):
        for star in self.stars:
            star["y"] += star["speed"]
            if star["y"] > SCREEN_HEIGHT:
                star["y"] = 0
                star["x"] = random.randint(0, SCREEN_WIDTH)

    def _draw_stars(self, screen):
        for star in self.stars:
            c = star["brightness"]
            pygame.draw.circle(screen, (c, c, c), (int(star["x"]), int(star["y"])), star["size"])

    def draw(self):
        self.screen.fill(BLACK)

        if self.state.is_menu():
            draw_menu_screen(self.screen, self.menu_selection)
        elif self.state.is_playing():
            self._draw_stars(self.screen)
            self.enemies_group.draw(self.screen)
            self.bullets_group.draw(self.screen)
            self.player_group.add(self.player)
            self.player_group.draw(self.screen)
            # Explosions need custom draw
            for explosion in self.explosions_group:
                explosion.draw(self.screen)
            draw_hud(
                self.screen,
                self.player.score,
                self.player.lives,
                self.spawner.current_level,
            )
        elif self.state.is_game_over():
            self._draw_stars(self.screen)
            draw_game_over_screen(self.screen, self.player.score)


if __name__ == "__main__":
    Game().run()