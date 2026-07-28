# game/sprites/enemy_bullet.py
import math

import pygame

from game.settings import *


class EnemyBullet(pygame.sprite.Sprite):
    """A bullet fired by an enemy toward the player."""

    def __init__(self, x, y, target_x, target_y, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface((ENEMY_BULLET_WIDTH, ENEMY_BULLET_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(self.image, ENEMY_BULLET_COLOR, (0, 0, ENEMY_BULLET_WIDTH, ENEMY_BULLET_HEIGHT))
        pygame.draw.rect(self.image, (255, 200, 200), (1, 1, ENEMY_BULLET_WIDTH - 2, 3))

        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y

        # Store precise float positions
        self.px = float(x)
        self.py = float(y)

        # Calculate velocity toward target (player)
        dx = target_x - x
        dy = target_y - y
        dist = max(1, (dx * dx + dy * dy) ** 0.5)
        self.vx = (dx / dist) * ENEMY_BULLET_SPEED
        self.vy = (dy / dist) * ENEMY_BULLET_SPEED

        # Reflection state
        self.reflected = False
        self.reflected_color = (255, 255, 100)  # gold color when reflected
        self.speed_multiplier = 1.0

    def reflect(self):
        """Reverse the bullet back toward enemies (used by reflect shield)."""
        self.vy = -abs(self.vy)  # always go upward
        self.reflected = True
        self.image = pygame.Surface((ENEMY_BULLET_WIDTH, ENEMY_BULLET_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(self.image, self.reflected_color, (0, 0, ENEMY_BULLET_WIDTH, ENEMY_BULLET_HEIGHT))
        pygame.draw.rect(self.image, (255, 255, 200), (1, 1, ENEMY_BULLET_WIDTH - 2, 3))

    def update(self, *args, **kwargs):
        self.px += self.vx * self.speed_multiplier
        self.py += self.vy * self.speed_multiplier
        self.rect.x = int(self.px)
        self.rect.y = int(self.py)
        if (self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0 or
                self.rect.left > SCREEN_WIDTH or self.rect.right < 0):
            self.kill()


class HomingMissile(pygame.sprite.Sprite):
    """Enemy homing missile that tracks the player."""

    def __init__(self, x, y, vx, vy, player_ref, damage=1, *groups):
        super().__init__(*groups)
        self._player_ref = player_ref  # weak ref via callable
        self.damage = damage
        self.lifetime = HOMING_MISSILE_CONFIG["lifetime"]
        self.homing_strength = HOMING_MISSILE_CONFIG["homing_strength"]
        self.base_speed = HOMING_MISSILE_CONFIG["speed"]

        # Missile sprite: slightly larger than normal bullet
        size = ENEMY_BULLET_WIDTH + 2
        self.image = pygame.Surface((size, size + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (255, 150, 50), (0, 2, size, size))
        pygame.draw.ellipse(self.image, (255, 220, 100), (1, 3, size - 2, size - 2))
        # Trail effect (drawn per frame in draw)
        self._trail_positions = []

        self.rect = self.image.get_rect()
        self.rect.centerx = int(x)
        self.rect.centery = int(y)
        self.px = float(x)
        self.py = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.speed_multiplier = 1.0
        self.reflected = False

    def update(self, *args, **kwargs):
        # Homing: adjust velocity toward player
        player = self._player_ref() if callable(self._player_ref) else None
        if player and player.alive():
            dx = player.rect.centerx - self.px
            dy = player.rect.centery - self.py
            dist = max(1, (dx * dx + dy * dy) ** 0.5)
            # Lerp velocity toward target direction
            target_vx = (dx / dist) * self.base_speed
            target_vy = (dy / dist) * self.base_speed
            self.vx += (target_vx - self.vx) * self.homing_strength
            self.vy += (target_vy - self.vy) * self.homing_strength
            # Normalize speed
            speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
            if speed > 0:
                self.vx = (self.vx / speed) * self.base_speed
                self.vy = (self.vy / speed) * self.base_speed

        self.px += self.vx * self.speed_multiplier
        self.py += self.vy * self.speed_multiplier
        self.rect.x = int(self.px)
        self.rect.y = int(self.py)

        # Store trail
        self._trail_positions.append((int(self.px), int(self.py)))
        if len(self._trail_positions) > 8:
            self._trail_positions.pop(0)

        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()
        if (self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0 or
                self.rect.left > SCREEN_WIDTH or self.rect.right < 0):
            self.kill()

    def get_trail(self):
        return self._trail_positions
