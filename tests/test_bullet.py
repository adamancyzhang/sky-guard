"""Tests for Bullet class: damage, piercing, homing, combo bonus."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.set_mode((1, 1))
pygame.font.init()

from game.sprites.bullet import Bullet
from game.sprites.enemy import Enemy
from game.settings import BULLET_SPEED


def test_default_bullet_params():
    b = Bullet(100, 100)
    assert b.damage == 1
    assert not b.piercing
    assert not b.is_charged
    assert b.weapon_type == "normal"
    assert b.weapon_level == 1


def test_bullet_moves_upward():
    b = Bullet(100, 100)
    y_before = b.rect.y
    b.update()
    assert b.rect.y < y_before


def test_bullet_with_weapon_params():
    b = Bullet(100, 100, "laser", 4)
    assert b.weapon_type == "laser"
    assert b.weapon_level == 4
    assert b.damage == 3  # laser L4 damage = 3
    assert b.vy == BULLET_SPEED * 2.5  # laser speed_mult


def test_charged_bullet():
    b = Bullet(100, 100, "laser", 5,
               is_charged=True, charge_tier=3,
               custom_damage=40, custom_speed=-25, piercing=True)
    assert b.is_charged
    assert b.charge_tier == 3
    assert b.damage == 40
    assert b.piercing
    assert b.vy == -25


def test_combo_bonus_bullet():
    b = Bullet(100, 100, "normal", 3, is_combo_bonus=True)
    assert b.is_combo_bonus
    # normal L3 damage = 1, combo bonus doubles it
    assert b.damage == 2


def test_bullet_with_vx():
    b = Bullet(100, 100, "normal", 1, vx=2)
    assert b.vx == 2
    x_before = b.rect.x
    b.update()
    assert b.rect.x > x_before


def test_bullet_damage_kills_tank():
    enemy = Enemy("tank")
    assert enemy.hp == 3
    assert not enemy.take_damage(1)  # 3→2
    assert not enemy.take_damage(1)  # 2→1
    assert enemy.take_damage(1)      # 1→0 destroyed


def test_bullet_high_damage_one_hit():
    enemy = Enemy("tank")
    assert enemy.take_damage(3)  # 1 hit with damage=3


def test_piercing_bullet_survives_collision():
    """Piercing bullet should not be killed via spritecollide alone."""
    b = Bullet(100, 100, "laser", 5, piercing=True)
    bg = pygame.sprite.Group(b)

    e = Enemy("basic", eid=1)
    e.rect.center = (100, 110)

    hit = pygame.sprite.spritecollide(b, pygame.sprite.Group(e), False)
    assert len(hit) > 0
    assert b.alive()  # still in group


def test_homing_bullet_enemies_ref():
    """Homing must accept an enemies group ref without error."""
    b = Bullet(100, 100, "homing", 1)
    e = Enemy("basic", eid=1)
    e.rect.center = (105, 80)
    enemies = pygame.sprite.Group(e)
    b.set_enemies_ref(enemies)
    b.update()  # should not crash
    assert b.enemies_group is not None


def test_bullet_offscreen_kill():
    b = Bullet(100, -50)
    assert b.alive()
    b.update()
    assert not b.alive()


def test_bullet_offscreen_left():
    b = Bullet(-50, 100)
    b.update()
    assert not b.alive()
