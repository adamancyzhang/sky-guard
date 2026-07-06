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
    check_player_powerup_collisions,
)
from game.graphics.hud import draw_hud, draw_menu_screen, draw_game_over_screen, draw_help_screen
from game.sounds.sound_manager import SoundManager


class Game:
    def __init__(self):
        pygame.init()
        # Detect screen size for initial window size
        info = pygame.display.Info()
        max_w, max_h = int(info.current_w * 0.9), int(info.current_h * 0.9)
        scale_w = max_w // SCREEN_WIDTH
        scale_h = max_h // SCREEN_HEIGHT
        self.scale_factor = max(1, min(scale_w, scale_h))
        self.display_width = SCREEN_WIDTH * self.scale_factor
        self.display_height = SCREEN_HEIGHT * self.scale_factor

        self.screen = pygame.display.set_mode(
            (self.display_width, self.display_height),
            pygame.RESIZABLE,
        )
        pygame.display.set_caption(WINDOW_TITLE)
        self.virtual_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.state = GameState()
        self.running = True
        self.menu_selection = 0  # 0 = START GAME, 1 = EXIT (HELP added later)

        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.player_group = pygame.sprite.GroupSingle()
        self.bullets_group = pygame.sprite.Group()
        self.enemies_group = pygame.sprite.Group()
        self.explosions_group = pygame.sprite.Group()
        self.powerups_group = pygame.sprite.Group()

        # Game systems
        self.player = Player()
        self.spawner = Spawner()
        self.sound_manager = SoundManager()

        # Background
        from game.graphics.background import ScrollingBackground
        self.background = ScrollingBackground()

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
            elif event.type == pygame.VIDEORESIZE:
                self._handle_resize(event.w, event.h)
            elif event.type == pygame.KEYDOWN:
                if self.state.is_menu():
                    # 3 menu items: START, HELP, EXIT
                    menu_count = 3
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.menu_selection = (self.menu_selection - 1) % menu_count
                        self.sound_manager.play("shoot")
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.menu_selection = (self.menu_selection + 1) % menu_count
                        self.sound_manager.play("shoot")
                    elif event.key == pygame.K_l:
                        from game.l10n import L10n
                        L10n.toggle()
                        self.sound_manager.play("shoot")
                    elif event.key == pygame.K_RETURN:
                        if self.menu_selection == 0:
                            self._start_game()
                        elif self.menu_selection == 1:
                            self.state.set(GameState.HELP)
                        else:
                            self.running = False
                elif self.state.is_help():
                    if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                        self.state.set(GameState.MENU)
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
        self.powerups_group.empty()
        self.player.reset()
        self.spawner.reset()

    def update(self):
        if self.state.is_playing():
            self.background.update()
            self._handle_shooting()
            self.player.update(pygame.key.get_pressed())
            self.bullets_group.update()
            self.enemies_group.update()
            self.explosions_group.update()
            self.powerups_group.update()
            self.spawner.update(self.enemies_group, self.player.score)

            # Collision detection — pass powerups_group for drops
            score = check_bullet_enemy_collisions(
                self.bullets_group, self.enemies_group, self.explosions_group, self.powerups_group
            )
            if score > 0:
                self.player.score += score
                self.sound_manager.play("explosion")

            # Power-up collection
            collected_type = check_player_powerup_collisions(self.player, self.powerups_group)
            if collected_type:
                if collected_type == "bomb":
                    # Bomb clears all enemies
                    for enemy in self.enemies_group:
                        Explosion(enemy.rect.centerx, enemy.rect.centery, self.explosions_group)
                    self.enemies_group.empty()
                    self.sound_manager.play("explosion")
                else:
                    self.player.apply_powerup(collected_type)
                    self.sound_manager.play("level_up")

            hit = check_player_enemy_collisions(
                self.player, self.enemies_group, self.explosions_group
            )
            if hit:
                self.sound_manager.play("hit")
                if self.player.lives <= 0:
                    self.state.set(GameState.GAME_OVER)
                    self.sound_manager.play("game_over")

    def _handle_resize(self, new_w, new_h):
        """Maintain 2:3 aspect ratio on window resize."""
        # Calculate the largest integer scale that fits in the new window
        scale_w = new_w // SCREEN_WIDTH
        scale_h = new_h // SCREEN_HEIGHT
        self.scale_factor = max(1, min(scale_w, scale_h))
        self.display_width = SCREEN_WIDTH * self.scale_factor
        self.display_height = SCREEN_HEIGHT * self.scale_factor
        self.screen = pygame.display.set_mode(
            (self.display_width, self.display_height),
            pygame.RESIZABLE,
        )

    def _handle_shooting(self):
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_SPACE] or keys[pygame.K_z]) and self.player.can_shoot():
            # Determine cooldown — rapid fire halves it
            cooldown = PLAYER_SHOOT_COOLDOWN
            if self.player.has_powerup("rapid"):
                cooldown = max(3, PLAYER_SHOOT_COOLDOWN // 2)

            self.player.shoot()
            self.player.shoot_cooldown = cooldown  # override for rapid fire

            # Main bullet
            bullet = Bullet(self.player.rect.centerx, self.player.rect.top)
            self.bullets_group.add(bullet)

            # Triple shot — add 2 angled bullets
            if self.player.has_powerup("triple"):
                bullet_left = Bullet(self.player.rect.centerx - 12, self.player.rect.top)
                bullet_right = Bullet(self.player.rect.centerx + 12, self.player.rect.top)
                self.bullets_group.add(bullet_left, bullet_right)

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
        # Clear virtual surface
        self.virtual_surf.fill(BLACK)

        if self.state.is_menu():
            draw_menu_screen(self.virtual_surf, self.menu_selection)
        elif self.state.is_help():
            draw_help_screen(self.virtual_surf)
        elif self.state.is_playing():
            self.background.draw(self.virtual_surf)
            self.enemies_group.draw(self.virtual_surf)
            self.bullets_group.draw(self.virtual_surf)
            self.powerups_group.draw(self.virtual_surf)
            self.player_group.add(self.player)
            self.player_group.draw(self.virtual_surf)
            # Explosions need custom draw
            for explosion in self.explosions_group:
                explosion.draw(self.virtual_surf)
            draw_hud(
                self.virtual_surf,
                self.player.score,
                self.player.lives,
                self.spawner.current_level,
                self.player.active_powerups,
            )
        elif self.state.is_game_over():
            self.background.draw(self.virtual_surf)
            draw_game_over_screen(self.virtual_surf, self.player.score)

        # Scale virtual surface to display window
        scaled = pygame.transform.scale(self.virtual_surf, (self.display_width, self.display_height))
        self.screen.blit(scaled, (0, 0))


if __name__ == "__main__":
    Game().run()