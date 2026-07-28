# game/sprites/item.py
import pygame

from game.graphics.pixel_art import create_item_surface
from game.settings import *


class Item(pygame.sprite.Sprite):
    """Item pickup sprite — falls down, collected into player inventory."""

    def __init__(self, x, y, item_type, *groups):
        super().__init__(*groups)
        self.item_type = item_type
        self.config = ITEM_TYPES[item_type]
        self.image = create_item_surface(item_type, self.config["color"])
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.y = y
        self.age = 0
        self.pulse = 0

    def update(self, *args, **kwargs):
        self.age += 1
        self.rect.y += ITEM_FALL_SPEED
        # Pulsating alpha effect
        self.pulse = (self.pulse + 1) % 60
        alpha = 200 + int(55 * abs((self.pulse / 60) * 2 - 1))
        self.image.set_alpha(min(255, alpha))
        # Destroy if off-screen
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()
