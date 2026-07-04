# game/sprites/player.py
import pygame
from game.settings import *
from game.graphics.pixel_art import create_player_ship


class Player(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.image = create_player_ship(scale=3)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 30
        self.speed = PLAYER_SPEED
        self.lives = PLAYER_MAX_LIVES
        self.score = 0
        self.shoot_cooldown = 0
        self.invincible_timer = 0
        self.active_powerups = {}  # power_type -> remaining frames

    def update(self, keys_pressed, *args, **kwargs):
        self._handle_movement(keys_pressed)
        self._handle_shoot_cooldown()
        self._handle_invincibility()
        self._update_powerups()

    def _handle_movement(self, keys_pressed):
        speed = self.speed * 2 if self.has_powerup("speed") else self.speed
        if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.rect.x -= speed
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.rect.x += speed
        if keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            self.rect.y -= speed
        if keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            self.rect.y += speed
        # Boundary clamp
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

    def _handle_shoot_cooldown(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def _handle_invincibility(self):
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            # Blinking effect
            alpha = 128 if (self.invincible_timer // 6) % 2 == 0 else 255
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)

    def _update_powerups(self):
        """Tick down active power-up timers each frame."""
        expired = []
        for ptype, frames in self.active_powerups.items():
            self.active_powerups[ptype] = frames - 1
            if self.active_powerups[ptype] <= 0:
                expired.append(ptype)
        for ptype in expired:
            del self.active_powerups[ptype]

    def can_shoot(self):
        return self.shoot_cooldown == 0

    def shoot(self):
        self.shoot_cooldown = PLAYER_SHOOT_COOLDOWN

    def hit(self):
        if self.invincible_timer > 0:
            return False
        self.lives -= 1
        if self.lives > 0:
            self.invincible_timer = PLAYER_INVINCIBLE_FRAMES
        return True  # was hit

    def apply_powerup(self, power_type):
        """Apply a power-up effect to the player."""
        config = POWERUP_TYPES.get(power_type)
        if not config:
            return
        duration = config["duration"]
        if power_type == "bomb":
            # bomb handled externally (clear enemies)
            pass
        elif power_type == "life":
            self.lives = min(self.lives + 1, PLAYER_MAX_LIVES)
        else:
            self.active_powerups[power_type] = duration

    def has_powerup(self, power_type):
        """Check if a timed power-up is currently active."""
        return power_type in self.active_powerups

    def reset(self):
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 30
        self.lives = PLAYER_MAX_LIVES
        self.score = 0
        self.invincible_timer = PLAYER_INVINCIBLE_FRAMES  # respawn protection
        self.shoot_cooldown = 0
        self.active_powerups.clear()