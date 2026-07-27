# tests/test_collision.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame
from game.settings import *
from game.sprites.bullet import Bullet
from game.sprites.enemy import Enemy
from game.systems.collision import check_bullet_enemy_collisions

# Pygame needs a display to create Surfaces
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.display.set_mode((1, 1))


def test_bullet_hits_enemy():
    """Test that a bullet hitting an enemy awards points."""
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    explosions = pygame.sprite.Group()

    bullet = Bullet(100, 200)
    enemy = Enemy("basic")
    enemy.rect.center = (100, 200)
    bullets.add(bullet)
    enemies.add(enemy)

    score = check_bullet_enemy_collisions(bullets, enemies, explosions)
    assert score == 10, f"Expected 10, got {score}"
    assert len(bullets) == 0, "Bullet should be killed"
    assert len(enemies) == 0, "Enemy should be killed"
    print("PASS: test_bullet_hits_enemy")


def test_bullet_misses_enemy():
    """Test that a missing bullet awards no points."""
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    explosions = pygame.sprite.Group()

    bullet = Bullet(100, 200)
    enemy = Enemy("basic")
    enemy.rect.center = (300, 300)  # different position
    bullets.add(bullet)
    enemies.add(enemy)

    score = check_bullet_enemy_collisions(bullets, enemies, explosions)
    assert score == 0, f"Expected 0, got {score}"
    print("PASS: test_bullet_misses_enemy")


def test_tank_enemy_needs_multiple_hits():
    """Test that tank enemies require multiple hits to destroy."""
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    explosions = pygame.sprite.Group()

    enemy = Enemy("tank")
    enemy.rect.center = (100, 200)
    enemies.add(enemy)

    # First hit
    bullet1 = Bullet(100, 200)
    bullets.add(bullet1)
    score = check_bullet_enemy_collisions(bullets, enemies, explosions)
    assert score == 0, f"Tank should not die from 1 hit, got score {score}"
    assert len(enemies) == 1, "Tank should still be alive"
    print("PASS: test_tank_enemy_needs_multiple_hits (1st hit)")

    # Second hit
    bullet2 = Bullet(100, 200)
    bullets.add(bullet2)
    score = check_bullet_enemy_collisions(bullets, enemies, explosions)
    assert score == 0, f"Tank should not die from 2 hits, got score {score}"
    print("PASS: test_tank_enemy_needs_multiple_hits (2nd hit)")

    # Third hit -> destroyed
    bullet3 = Bullet(100, 200)
    bullets.add(bullet3)
    score = check_bullet_enemy_collisions(bullets, enemies, explosions)
    assert score == 30, f"Tank should die from 3rd hit, got score {score}"
    assert len(enemies) == 0, "Tank should be destroyed"
    print("PASS: test_tank_enemy_needs_multiple_hits (3rd hit - destroyed)")


# ── Item drop tests ──

def test_item_drop_with_items_group():
    """Enemies should be able to drop items when items_group is provided.
    This is a probabilistic test — verifies the items_group parameter doesn't crash
    and that the function signature accepts the new parameter."""
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    explosions = pygame.sprite.Group()
    items = pygame.sprite.Group()

    from game.sprites.bullet import Bullet
    bullet = Bullet(100, 200)
    bullet.damage = 10
    enemy = Enemy("basic")
    enemy.rect.center = (100, 200)
    bullets.add(bullet)
    enemies.add(enemy)

    score = check_bullet_enemy_collisions(bullets, enemies, explosions,
                                          items_group=items)
    assert score == 10
    assert len(enemies) == 0
    assert len(bullets) == 0
    print("PASS: test_item_drop_with_items_group (no crash)")


def test_item_drop_powerup_drop_independence():
    """Item drops should work alongside powerup drops without interference."""
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    explosions = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    items = pygame.sprite.Group()

    from game.sprites.bullet import Bullet
    bullet = Bullet(100, 200)
    bullet.damage = 10
    enemy = Enemy("basic")
    enemy.rect.center = (100, 200)
    bullets.add(bullet)
    enemies.add(enemy)

    score = check_bullet_enemy_collisions(bullets, enemies, explosions,
                                          powerups_group=powerups,
                                          items_group=items)
    assert score == 10
    print("PASS: test_item_drop_powerup_drop_independence (no interference)")


def test_item_drop_param_defaults():
    """Calling collision check without items_group should still work (backward compat)."""
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    explosions = pygame.sprite.Group()

    bullet = Bullet(100, 200)
    enemy = Enemy("basic")
    enemy.rect.center = (100, 200)
    bullets.add(bullet)
    enemies.add(enemy)

    # Original signature: no items_group parameter
    score = check_bullet_enemy_collisions(bullets, enemies, explosions)
    assert score == 10
    print("PASS: test_item_drop_param_defaults (backward compat)")


if __name__ == "__main__":
    test_bullet_hits_enemy()
    test_bullet_misses_enemy()
    test_tank_enemy_needs_multiple_hits()
    print("\nAll collision tests PASSED!")