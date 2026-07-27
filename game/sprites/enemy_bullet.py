# game/sprites/enemy_bullet.py
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
        # Time slow multiplier
        self.speed_multiplier = 1.0

    def reflect(self):
        """Reverse the bullet back toward enemies (used by reflect shield)."""
        self.vy = -abs(self.vy)  # always go upward
        self.reflected = True
        # Change color to indicate reflected state
        self.image = pygame.Surface((ENEMY_BULLET_WIDTH, ENEMY_BULLET_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(self.image, self.reflected_color, (0, 0, ENEMY_BULLET_WIDTH, ENEMY_BULLET_HEIGHT))
        pygame.draw.rect(self.image, (255, 255, 200), (1, 1, ENEMY_BULLET_WIDTH - 2, 3))

    def update(self, *args, **kwargs):
        self.px += self.vx * self.speed_multiplier
        self.py += self.vy * self.speed_multiplier
        self.rect.x = int(self.px)
        self.rect.y = int(self.py)
        # Remove if off-screen (with margin)
        if (self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0 or
                self.rect.left > SCREEN_WIDTH or self.rect.right < 0):
            self.kill()