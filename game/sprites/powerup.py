# game/sprites/powerup.py
import pygame
from game.settings import *
from game.graphics.pixel_art import create_powerup_surface


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, power_type, *groups):
        super().__init__(*groups)
        self.power_type = power_type
        self.config = POWERUP_TYPES[power_type]
        self.image = create_powerup_surface(power_type, self.config["color"])
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.y = y
        self.age = 0
        self.pulse = 0

    def update(self, *args, **kwargs):
        self.age += 1
        self.rect.y += POWERUP_SPEED
        # Pulsating alpha effect
        self.pulse = (self.pulse + 1) % 60
        alpha = 200 + int(55 * abs((self.pulse / 60) * 2 - 1))
        self.image.set_alpha(min(255, alpha))
        # Destroy if off-screen
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()