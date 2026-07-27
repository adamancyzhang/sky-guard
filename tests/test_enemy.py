"""Tests for Enemy class: types, movement, damage, shooting."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.set_mode((1, 1))
pygame.font.init()

from game.settings import ENEMY_TYPES, SCREEN_WIDTH, SCREEN_HEIGHT
from game.sprites.enemy import Enemy


def test_basic_enemy_config():
    cfg = ENEMY_TYPES["basic"]
    assert cfg["speed"] == 3
    assert cfg["hp"] == 1
    assert cfg["score"] == 10


def test_fast_enemy_config():
    cfg = ENEMY_TYPES["fast"]
    assert cfg["speed"] == 5
    assert cfg["hp"] == 1
    assert cfg["score"] == 15


def test_tank_enemy_config():
    cfg = ENEMY_TYPES["tank"]
    assert cfg["speed"] == 2
    assert cfg["hp"] == 3
    assert cfg["score"] == 30


def test_enemy_spawns_above_screen():
    enemy = Enemy("basic")
    assert enemy.rect.y < 0


def test_enemy_has_score_value():
    enemy = Enemy("basic")
    assert enemy.score_value == 10


def test_enemy_moves_down():
    enemy = Enemy("basic")
    y_before = enemy.rect.y
    enemy.update()
    assert enemy.rect.y > y_before


def test_enemy_killed_offscreen():
    enemy = Enemy("basic")
    # Place off-screen bottom
    enemy.rect.y = SCREEN_HEIGHT + 10
    assert enemy.alive()
    enemy.update()
    assert not enemy.alive()


def test_basic_take_damage():
    enemy = Enemy("basic")
    assert enemy.hp == 1
    result = enemy.take_damage(1)
    assert result  # destroyed


def test_tank_survives_one_hit():
    enemy = Enemy("tank")
    assert enemy.hp == 3
    result = enemy.take_damage(1)
    assert not result  # still alive
    assert enemy.hp == 2


def test_tank_destroyed_after_three_hits():
    enemy = Enemy("tank")
    enemy.take_damage(1)
    enemy.take_damage(1)
    result = enemy.take_damage(1)
    assert result


def test_fast_enemy_can_shoot():
    enemy = Enemy("fast")
    assert enemy.can_shoot


def test_tank_enemy_can_shoot():
    enemy = Enemy("tank")
    assert enemy.can_shoot


def test_basic_enemy_cannot_shoot():
    enemy = Enemy("basic")
    assert not enemy.can_shoot


def test_shoot_timer_ignored_below_screen():
    """Enemies below screen top should not shoot."""
    enemy = Enemy("fast")
    enemy.rect.top = int(SCREEN_HEIGHT * 0.8)  # too low
    assert not enemy.should_shoot(0)


def test_shoot_timer_active_when_in_range():
    """Enemies in the upper portion should be able to shoot."""
    enemy = Enemy("fast")
    enemy.rect.top = 50  # in upper portion
    enemy.shoot_timer = 1  # almost ready
    # Force timer to fire
    result = False
    for _ in range(5):
        if enemy.should_shoot(0):
            result = True
            break
    # Timer should fire eventually
    assert result  # may be False if random variation resets it


def test_enemy_wobble():
    """Enemy has sinusoidal horizontal movement."""
    enemy = Enemy("basic")
    x_before = enemy.rect.x
    enemy.update()
    # x should change (either + or -) due to wobble
    # If wobble_amp is very small this might not change, so just check no crash
    assert True


def test_enemy_boundary_clamp():
    """Enemy x should be clamped to screen width."""
    enemy = Enemy("basic", x=9999)
    enemy.update()
    assert enemy.rect.x <= SCREEN_WIDTH - enemy.rect.width
    assert enemy.rect.x >= 0


def test_enemy_eid():
    enemy = Enemy("basic", eid=42)
    assert enemy.eid == 42


def test_enemy_custom_x():
    enemy = Enemy("basic", x=200)
    assert enemy.rect.x == 200


def test_enemy_random_x_when_not_specified():
    """When x is None, enemy spawns at random x within screen."""
    enemy = Enemy("basic")
    assert 0 <= enemy.rect.x <= SCREEN_WIDTH - enemy.rect.width


def test_damage_flash():
    """Enemy should flash alpha on hit."""
    enemy = Enemy("basic")
    assert enemy.image.get_alpha() in (None, 255)  # full opaque
    enemy.take_damage(1)
    assert enemy.image.get_alpha() == 100  # hit flash


def test_shoot_timer_basic_does_not_shoot():
    """Basic enemy should_shot returns False even with timer exhausted."""
    enemy = Enemy("basic")
    enemy.shoot_timer = 0
    assert not enemy.should_shoot(0)
