# game/sprites/sub_weapon_projectile.py
import pygame
import math
import random
from game.settings import *
from game.graphics.pixel_art import create_sub_weapon_surface


class SubWeaponProjectile(pygame.sprite.Sprite):
    """A projectile fired from the sub-weapon system."""

    def __init__(self, x, y, sub_type, config, enemies_group=None, *groups):
        super().__init__(*groups)
        self.sub_type = sub_type
        self.config = config
        self.image = create_sub_weapon_surface(sub_type, scale=2)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.enemies_group = enemies_group
        self.damage = config.get("damage", 1)
        self.life = 180  # max frames alive

        if sub_type == "missile":
            self.speed = config.get("speed", 6)
            self.homing_strength = config.get("homing_strength", 0.05)
            self.vx = 0
            self.vy = -self.speed

        elif sub_type == "bomb":
            self.speed = config.get("speed", 4)
            self.vx = 0
            self.vy = -self.speed
            self.has_exploded = False
            self.explosion_radius = config.get("explosion_radius", 40)

        elif sub_type == "mine":
            self.speed = config.get("drop_speed", 2)
            self.vx = 0
            self.vy = self.speed  # drops down
            self.armed = False
            self.arm_timer = 30  # 0.5s until armed

    def update(self, *args, **kwargs):
        self.life -= 1
        if self.life <= 0:
            self.kill()
            return

        if self.sub_type == "missile":
            self._update_missile()
        elif self.sub_type == "bomb":
            if not self.has_exploded:
                self.rect.y += self.vy
            else:
                self.kill()
        elif self.sub_type == "mine":
            self._update_mine()

    def _update_missile(self):
        """Homing missile: track nearest enemy."""
        self.rect.y += self.vy

        # Find nearest enemy
        if self.enemies_group and len(self.enemies_group) > 0:
            nearest = None
            nearest_dist = float("inf")
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
                self.vx += (dx / dist) * self.homing_strength
                # Clamp speed
                current_speed = math.sqrt(self.vx * self.vx + self.vy * self.vy)
                max_speed = self.config.get("speed", 6) * 1.5
                if current_speed > max_speed:
                    self.vx = (self.vx / current_speed) * max_speed
                    self.vy = (self.vy / current_speed) * max_speed

        self.rect.x += self.vx

    def _update_mine(self):
        """Dropping mine that stays in place after arming."""
        if self.arm_timer > 0:
            self.arm_timer -= 1
            self.rect.y += self.speed
        else:
            self.armed = True
            # Slight pulse effect
            self.image.set_alpha(180 + int(75 * (0.5 + 0.5 * math.sin(self.life * 0.1))))

    def check_hit(self, enemy):
        """Check if this projectile hits an enemy. Returns True if projectile should be consumed."""
        if self.sub_type == "bomb" and not self.has_exploded:
            # Bomb explodes on any contact
            self.has_exploded = True
            return True
        elif self.sub_type == "mine":
            if self.armed and self.rect.colliderect(enemy.rect):
                return True
            return False
        else:
            # Missile: standard collision
            return self.rect.colliderect(enemy.rect)

    def get_damage(self):
        """Return damage value."""
        return self.damage

    def is_area_damage(self):
        """Check if this projectile does area damage (bomb)."""
        return self.sub_type == "bomb"

    def get_explosion_center(self):
        """Get center point for explosion effect."""
        return (self.rect.centerx, self.rect.centery)
