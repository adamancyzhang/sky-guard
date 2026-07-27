# game/sprites/option.py
import pygame
import math
from game.settings import *
from game.graphics.pixel_art import create_option_surface


class Option(pygame.sprite.Sprite):
    """A floating satellite that mirrors player shots."""

    def __init__(self, player, index=0, *groups):
        super().__init__(*groups)
        self.player = player
        self.index = index
        self.image = create_option_surface(scale=2)
        self.rect = self.image.get_rect()
        side = 1 if index % 2 == 0 else -1
        self.rect.centerx = player.rect.centerx + OPTION_OFFSET_X * side
        self.rect.centery = player.rect.centery + OPTION_OFFSET_Y * (index + 1)

        # Follow state
        self.target_x = self.rect.centerx
        self.target_y = self.rect.centery
        self.angle = 0

        # Shooting
        self.shoot_frame = 0
        self.should_fire = False
        self.shot_delay_frames = OPTION_SHOOT_DELAY * (index + 1)

    def update_position(self, player_cx, player_cy, player_bottom):
        """Smoothly follow the player."""
        side = 1 if self.index % 2 == 0 else -1
        offset_x = OPTION_OFFSET_X * side
        offset_y = OPTION_OFFSET_Y * (self.index + 1)

        self.target_x = player_cx + offset_x
        self.target_y = player_cy + offset_y

        self.rect.centerx += (self.target_x - self.rect.centerx) * OPTION_FOLLOW_SPEED
        self.rect.centery += (self.target_y - self.rect.centery) * OPTION_FOLLOW_SPEED

        # Gentle bob animation
        self.angle += 0.05
        self.rect.y += math.sin(self.angle) * 0.5

    def update_shoot_state(self, player_is_firing):
        """Receive the player's firing state with a delay."""
        self.shoot_frame += 1
        if self.shoot_frame >= self.shot_delay_frames:
            self.should_fire = player_is_firing
            self.shoot_frame = 0
        else:
            self.should_fire = False

    def get_shoot_position(self):
        """Return (x, y) for spawning a bullet from this option."""
        return (self.rect.centerx, self.rect.top)
