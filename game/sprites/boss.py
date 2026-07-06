# game/sprites/boss.py
import pygame
import random
import math
from game.settings import *
from game.graphics.pixel_art import create_boss_surface


class Boss(pygame.sprite.Sprite):
    """Large boss enemy with phase-based attack patterns."""

    def __init__(self, *groups):
        super().__init__(*groups)
        self.image = create_boss_surface(scale=3)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.y = -self.rect.height

        self.max_hp = BOSS_BASE_HP
        self.hp = self.max_hp
        self.score_value = BOSS_SCORE_VALUE
        self.speed = BOSS_SPEED

        # Movement: enter from top, then strafe horizontally
        self.phase = "entering"  # entering -> fighting -> defeated
        self.enter_y_target = 60
        self.move_direction = 1
        self.shoot_timer = 0
        self.current_pattern = "spread"

    def update(self, *args, **kwargs):
        # Phase: entering
        if self.phase == "entering":
            self.rect.y += self.speed
            if self.rect.y >= self.enter_y_target:
                self.rect.y = self.enter_y_target
                self.phase = "fighting"
            return

        # Phase: fighting — horizontal strafe
        self.rect.x += self.move_direction * self.speed * 2
        if self.rect.right >= SCREEN_WIDTH - 20:
            self.move_direction = -1
        elif self.rect.left <= 20:
            self.move_direction = 1

        # Update phase based on HP
        hp_ratio = self.hp / self.max_hp
        if hp_ratio <= 0.33:
            self.current_pattern = "aimed"
        elif hp_ratio <= 0.66:
            self.current_pattern = "circle"

    def should_shoot(self):
        """Timer-based shooting."""
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            interval = BOSS_SHOOT_INTERVAL
            for cfg in BOSS_BULLET_CONFIGS:
                if cfg["pattern"] == self.current_pattern:
                    interval = cfg["interval"]
                    break
            self.shoot_timer = interval
            return True
        return False

    def get_bullet_vectors(self, player_x, player_y):
        """Return a list of (vx, vy) tuples for the current pattern."""
        vectors = []
        pattern_config = None
        for cfg in BOSS_BULLET_CONFIGS:
            if cfg["pattern"] == self.current_pattern:
                pattern_config = cfg
                break
        if not pattern_config:
            pattern_config = BOSS_BULLET_CONFIGS[0]

        if self.current_pattern == "spread":
            count = pattern_config["count"]
            spread = pattern_config["angle_spread"]
            # Calculate angle to player
            dx = player_x - self.rect.centerx
            dy = player_y - self.rect.centery
            base_angle = math.degrees(math.atan2(dy, dx))
            for i in range(count):
                angle = math.radians(base_angle - spread / 2 + (spread / (count - 1)) * i)
                vx = math.cos(angle) * ENEMY_BULLET_SPEED
                vy = math.sin(angle) * ENEMY_BULLET_SPEED
                vectors.append((vx, vy))

        elif self.current_pattern == "aimed":
            dx = player_x - self.rect.centerx
            dy = player_y - self.rect.centery
            dist = max(1, (dx * dx + dy * dy) ** 0.5)
            vx = (dx / dist) * ENEMY_BULLET_SPEED * 1.2  # faster
            vy = (dy / dist) * ENEMY_BULLET_SPEED * 1.2
            vectors.append((vx, vy))

        elif self.current_pattern == "circle":
            count = pattern_config["count"]
            for i in range(count):
                angle = math.radians((360 / count) * i)
                vx = math.cos(angle) * ENEMY_BULLET_SPEED * 0.8
                vy = math.sin(angle) * ENEMY_BULLET_SPEED * 0.8
                vectors.append((vx, vy))

        return vectors

    def take_damage(self, amount=1):
        self.hp -= amount
        # Flash white briefly
        self.image.set_alpha(100)
        return self.hp <= 0

    def reset_alpha(self):
        """Restore full alpha after a brief flash."""
        self.image.set_alpha(255)

    def is_defeated(self):
        return self.hp <= 0

    def get_hp_ratio(self):
        return self.hp / self.max_hp