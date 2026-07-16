# game/sprites/enemy.py
import pygame
import random
from game.settings import *
from game.graphics.pixel_art import create_enemy_surface


class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type="basic", eid=0, *groups):
        super().__init__(*groups)
        self.eid = eid  # 全局唯一敌机 ID（用于合作模式同步）
        self.enemy_type = enemy_type
        config = ENEMY_TYPES[enemy_type]
        self.image = create_enemy_surface(enemy_type, scale=3)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = -self.rect.height  # spawn from above
        self.speed = config["speed"]
        self.hp = config["hp"]
        self.score_value = config["score"]
        # Slight lateral wobble
        self.wobble = random.uniform(-1, 1)
        self.wobble_speed = random.uniform(0.02, 0.05)
        # Shooting ability
        self.can_shoot = enemy_type in ("fast", "tank")  # basic enemies don't shoot
        self.shoot_timer = random.randint(0, ENEMY_SHOOT_INTERVAL)

    def update(self, *args, **kwargs):
        self.rect.y += self.speed
        # Lateral wobble
        self.wobble += self.wobble_speed
        self.rect.x += self.wobble * 0.5
        # Boundary clamp
        self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
        # Destroy if off-screen
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def take_damage(self, amount=1):
        self.hp -= amount
        # Hit flash
        self.image.set_alpha(100)
        return self.hp <= 0

    def should_shoot(self, frame_count):
        """Check if this enemy should fire a bullet this frame."""
        if not self.can_shoot:
            return False
        # Only shoot when roughly in the upper 2/3 of screen
        if self.rect.top > SCREEN_HEIGHT * 0.66:
            return False
        # Timer-based shooting with random variation
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot_timer = max(ENEMY_SHOOT_MIN_INTERVAL,
                                   ENEMY_SHOOT_INTERVAL - random.randint(0, 30))
            return True
        return False