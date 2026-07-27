"""Tests for sub-weapon system."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.set_mode((1, 1))
pygame.font.init()

from game.settings import SUB_WEAPONS, SUB_WEAPON_MAX_ENERGY
from game.sprites.player import Player
from game.sprites.sub_weapon_projectile import SubWeaponProjectile
from game.sprites.enemy import Enemy
from game.systems.collision import check_sub_weapon_collisions
from game.sprites.explosion import Explosion


def test_sub_weapon_default_type():
    p = Player()
    assert p.sub_weapon_type == "missile"


def test_sub_weapon_starts_with_full_energy():
    p = Player()
    assert p.sub_weapon_energy == SUB_WEAPON_MAX_ENERGY


def test_can_fire_when_energy_high():
    p = Player()
    assert p.can_fire_sub_weapon()


def test_fire_consumes_energy():
    p = Player()
    sub_type, config = p.fire_sub_weapon()
    assert sub_type == "missile"
    assert p.sub_weapon_energy < SUB_WEAPON_MAX_ENERGY


def test_cooldown_after_fire():
    p = Player()
    p.fire_sub_weapon()
    assert not p.can_fire_sub_weapon()


def test_cooldown_recovers():
    p = Player()
    p.fire_sub_weapon()
    original_cd = p.sub_weapon_cooldown
    for _ in range(original_cd + 1):
        p.update_sub_weapon()
    assert p.can_fire_sub_weapon()


def test_energy_regen():
    p = Player()
    p.sub_weapon_energy = 50
    for _ in range(10):
        p.update_sub_weapon()
    assert p.sub_weapon_energy > 50


def test_energy_does_not_exceed_max():
    p = Player()
    p.sub_weapon_energy = SUB_WEAPON_MAX_ENERGY
    for _ in range(50):
        p.update_sub_weapon()
    assert p.sub_weapon_energy <= SUB_WEAPON_MAX_ENERGY


def test_get_energy_ratio():
    p = Player()
    p.sub_weapon_energy = 50
    ratio = p.get_sub_weapon_energy_ratio()
    assert 0 < ratio < 1.0
    assert ratio == 50.0 / SUB_WEAPON_MAX_ENERGY


def test_get_energy_ratio_full():
    p = Player()
    assert p.get_sub_weapon_energy_ratio() == 1.0


def test_switch_sub_weapon_cycles():
    p = Player()
    p.unlocked_sub_weapons = ["missile", "bomb", "mine"]
    p.switch_sub_weapon()
    assert p.sub_weapon_type == "bomb"
    p.switch_sub_weapon()
    assert p.sub_weapon_type == "mine"
    p.switch_sub_weapon()
    assert p.sub_weapon_type == "missile"  # wraps


def test_switch_sub_weapon_single_no_op():
    p = Player()
    p.switch_sub_weapon()
    assert p.sub_weapon_type == "missile"


# ── Projectile behavior tests ──

def test_missile_moves_upward():
    proj = SubWeaponProjectile(100, 100, "missile", SUB_WEAPONS["missile"])
    assert proj.vy < 0
    proj.update()
    assert proj.rect.y < 100


def test_bomb_moves_upward():
    proj = SubWeaponProjectile(100, 100, "bomb", SUB_WEAPONS["bomb"])
    assert not proj.has_exploded
    proj.update()
    assert proj.rect.y < 100


def test_bomb_explosion_radius():
    proj = SubWeaponProjectile(100, 100, "bomb", SUB_WEAPONS["bomb"])
    assert proj.explosion_radius == 40
    assert proj.is_area_damage()


def test_mine_drops_down():
    proj = SubWeaponProjectile(100, 100, "mine", SUB_WEAPONS["mine"])
    assert proj.vy > 0  # drops


def test_mine_arms_after_timer():
    proj = SubWeaponProjectile(100, 100, "mine", SUB_WEAPONS["mine"])
    assert not proj.armed
    assert proj.arm_timer == 30
    for _ in range(31):
        proj.update()
    assert proj.armed


def test_mine_not_armed_immediately():
    proj = SubWeaponProjectile(100, 100, "mine", SUB_WEAPONS["mine"])
    proj.update()
    assert not proj.armed


def test_projectile_expires():
    proj = SubWeaponProjectile(100, 100, "missile", SUB_WEAPONS["missile"])
    assert proj.alive()
    for _ in range(200):
        proj.update()
    assert not proj.alive()


def test_missile_collision_kills_enemy():
    sub_group = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    explosions = pygame.sprite.Group()

    m = SubWeaponProjectile(100, 100, "missile", SUB_WEAPONS["missile"])
    sub_group.add(m)

    enemy = Enemy("basic", eid=1, x=100)
    enemy.rect.center = (100, 110)
    enemies.add(enemy)

    score = check_sub_weapon_collisions(sub_group, enemies, explosions)
    assert score == 10  # basic enemy = 10 points
    assert len(enemies) == 0


def test_bomb_explosion_hits_multiple():
    sub_group = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    explosions = pygame.sprite.Group()

    b = SubWeaponProjectile(100, 100, "bomb", SUB_WEAPONS["bomb"])
    sub_group.add(b)

    # Two enemies close together
    e1 = Enemy("basic", eid=1)
    e1.rect.center = (100, 110)
    e2 = Enemy("basic", eid=2)
    e2.rect.center = (105, 120)
    enemies.add(e1, e2)

    score = check_sub_weapon_collisions(sub_group, enemies, explosions)
    assert score == 20  # 2 basic enemies = 20 points
    assert len(enemies) == 0


def test_mine_does_not_hit_before_armed():
    sub_group = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    explosions = pygame.sprite.Group()

    m = SubWeaponProjectile(100, 100, "mine", SUB_WEAPONS["mine"])
    sub_group.add(m)

    # Enemy in range before mine is armed
    enemy = Enemy("basic", eid=1)
    enemy.rect.center = (100, 110)
    enemies.add(enemy)

    # No collision (mine not armed yet)
    score = check_sub_weapon_collisions(sub_group, enemies, explosions)
    assert score == 0
