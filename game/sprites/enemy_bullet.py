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

        # Calculate velocity toward target (player)
        dx = target_x - x
        dy = target_y - y
        dist = max(1, (dx * dx + dy * dy) ** 0.5)
        self.vx = (dx / dist) * ENEMY_BULLET_SPEED
        self.vy = (dy / dist) * ENEMY_BULLET_SPEED

    def update(self, *args, **kwargs):
        self.rect.x += self.vx
        self.rect.y += self.vy
        # Remove if off-screen (with margin)
        if (self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0 or
                self.rect.left > SCREEN_WIDTH or self.rect.right < 0):
            self.kill()