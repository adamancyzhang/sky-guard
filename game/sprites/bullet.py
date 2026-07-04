# game/sprites/bullet.py
import pygame
from game.settings import *
from game.graphics.pixel_art import create_bullet_surface


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(*groups)
        self.image = create_bullet_surface()
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y

    def update(self, *args, **kwargs):
        self.rect.y += BULLET_SPEED
        # Destroy if off-screen
        if self.rect.bottom < 0:
            self.kill()