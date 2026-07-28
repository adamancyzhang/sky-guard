# game/sprites/bullet.py
import math

import pygame

from game.graphics.pixel_art import create_weapon_bullet
from game.settings import *


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y,
                 weapon_type="normal",
                 weapon_level=1,
                 is_charged=False,
                 charge_tier=0,
                 vx=0,
                 vy=None,
                 custom_damage=None,
                 custom_speed=None,
                 piercing=False,
                 is_combo_bonus=False,
                 *groups):
        super().__init__(*groups)
        self.weapon_type = weapon_type
        self.weapon_level = weapon_level
        self.is_charged = is_charged
        self.charge_tier = charge_tier
        self.piercing = piercing
        self.is_combo_bonus = is_combo_bonus

        # Calculate damage
        config = WEAPON_LEVEL_CONFIGS.get(weapon_type, WEAPON_LEVEL_CONFIGS["normal"]).get(weapon_level, {})
        base_damage = config.get("damage", 1)
        if custom_damage is not None:
            self.damage = int(custom_damage)
        else:
            self.damage = base_damage
            if is_combo_bonus:
                self.damage = max(1, self.damage * 2)

        # Create surface
        self.image = create_weapon_bullet(weapon_type, weapon_level, is_charged, charge_tier)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y

        # Velocity
        self.vx = vx
        if custom_speed is not None:
            self.speed = custom_speed
        else:
            speed_mult = config.get("speed_mult", 1.0)
            self.speed = BULLET_SPEED * speed_mult
        self.vy = vy if vy is not None else self.speed
        self._frame = 0

        # For homing
        self.enemies_group = None

    def set_enemies_ref(self, enemies_group):
        """Set reference to enemies group for homing."""
        self.enemies_group = enemies_group

    def update(self, *args, **kwargs):
        self._frame += 1
        self.rect.x += self.vx
        self.rect.y += self.vy

        # Homing behavior
        if self.weapon_type == "homing" and self.enemies_group is not None:
            nearest = None
            nearest_dist = float("inf")
            if len(self.enemies_group) > 0:
                for enemy in self.enemies_group:
                    dx = enemy.rect.centerx - self.rect.centerx
                    dy = enemy.rect.centery - self.rect.centery
                    dist = dx * dx + dy * dy
                    if dist < nearest_dist:
                        nearest_dist = dist
                        nearest = enemy
                if nearest:
                    dx = nearest.rect.centerx - self.rect.centerx
                    dy = nearest.rect.centery - self.rect.centery
                    dist = max(1, math.sqrt(dx * dx + dy * dy))
                    self.vx += (dx / dist) * 0.03
                    self.vy += (dy / dist) * 0.03

        # Destroy if off-screen
        if self.rect.bottom < 0 or self.rect.left > SCREEN_WIDTH or self.rect.right < 0:
            self.kill()
