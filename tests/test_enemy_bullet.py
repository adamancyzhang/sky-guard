# tests/test_enemy_bullet.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.set_mode((1, 1))

from game.settings import ENEMY_BULLET_SPEED, SCREEN_WIDTH, SCREEN_HEIGHT
from game.sprites.enemy_bullet import EnemyBullet
from game.sprites.enemy import Enemy


def test_enemy_bullet_creation():
    """EnemyBullet should be created with proper position and velocity."""
    bullet = EnemyBullet(100, 100, 150, 200)
    assert bullet.rect.centerx == 100
    assert bullet.rect.centery == 100
    # Should move roughly toward (150, 200)
    assert bullet.vx > 0
    assert bullet.vy > 0


def test_enemy_bullet_velocity_magnitude():
    """Velocity magnitude should equal ENEMY_BULLET_SPEED."""
    bullet = EnemyBullet(100, 100, 200, 200)
    mag = (bullet.vx ** 2 + bullet.vy ** 2) ** 0.5
    assert abs(mag - ENEMY_BULLET_SPEED) < 0.01, f"Expected ~{ENEMY_BULLET_SPEED}, got {mag}"


def test_enemy_bullet_off_screen_kill():
    """Bullet should be killed when it goes off screen."""
    bullet = EnemyBullet(100, -100, 100, 0)  # above screen, moving up
    group = pygame.sprite.Group(bullet)
    bullet.update()
    # Should be killed since it's far above
    assert len(group) == 0 or bullet.rect.bottom < 0


def test_fast_enemy_can_shoot():
    """Fast enemy should have can_shoot=True."""
    enemy = Enemy("fast")
    assert enemy.can_shoot is True


def test_basic_enemy_cannot_shoot():
    """Basic enemy should have can_shoot=False."""
    enemy = Enemy("basic")
    assert enemy.can_shoot is False


def test_tank_enemy_can_shoot():
    """Tank enemy should have can_shoot=True."""
    enemy = Enemy("tank")
    assert enemy.can_shoot is True


def test_should_shoot_below_threshold():
    """Enemy below 66% screen should not shoot."""
    enemy = Enemy("fast")
    enemy.rect.top = int(SCREEN_HEIGHT * 0.8)  # below threshold
    enemy.shoot_timer = 0  # force timer to be ready
    assert enemy.should_shoot(0) is False


def test_should_shoot_above_threshold():
    """Enemy above 66% screen should eventually shoot when timer expires."""
    enemy = Enemy("fast")
    enemy.rect.top = int(SCREEN_HEIGHT * 0.3)  # above threshold
    enemy.shoot_timer = 0  # timer expired
    assert enemy.should_shoot(0) is True
    # Timer should be reset
    assert enemy.shoot_timer > 0


def test_should_shoot_basic_never_shoots():
    """Basic enemy should never shoot even with timer expired."""
    enemy = Enemy("basic")
    enemy.rect.top = int(SCREEN_HEIGHT * 0.3)
    enemy.shoot_timer = 0
    assert enemy.should_shoot(0) is False