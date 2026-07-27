"""Tests for the item (道具) system."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.set_mode((1, 1))
pygame.font.init()

from game.settings import (
    ITEM_TYPES, ITEM_DROP_CHANCE, ITEM_MAX_INVENTORY, ITEM_FALL_SPEED,
    SCREEN_HEIGHT, PLAYER_MAX_LIVES,
)
from game.sprites.player import Player
from game.sprites.item import Item
from game.sprites.enemy import Enemy
from game.sprites.enemy_bullet import EnemyBullet
from game.systems.collision import (
    check_player_item_collisions,
    apply_gravity_bomb,
    check_enemy_bullet_player_collisions,
    check_player_enemy_collisions,
)
from game.sprites.explosion import Explosion
from game.settings import ENEMY_BULLET_SPEED


# ============================================================
# 配置测试
# ============================================================

def test_item_types_defined():
    """All 6 item types should be defined in settings."""
    assert "full_bomb" in ITEM_TYPES
    assert "time_slow" in ITEM_TYPES
    assert "reflect_shield" in ITEM_TYPES
    assert "repair" in ITEM_TYPES
    assert "score_boost" in ITEM_TYPES
    assert "gravity_bomb" in ITEM_TYPES


def test_item_configs():
    """Each item type should have color, description_key, and icon."""
    for itype, config in ITEM_TYPES.items():
        assert "color" in config, f"{itype} missing color"
        assert "description_key" in config, f"{itype} missing description_key"
        assert "icon" in config, f"{itype} missing icon"
        assert config["description_key"].startswith("item_"), f"{itype} bad description_key"


def test_item_drop_chance():
    """Item drop chance should be between 0 and 1."""
    assert 0 < ITEM_DROP_CHANCE < 1


def test_item_max_inventory():
    """Max inventory should be positive."""
    assert ITEM_MAX_INVENTORY > 0
    assert ITEM_MAX_INVENTORY == 3


def test_item_fall_speed():
    """Item fall speed should be positive."""
    assert ITEM_FALL_SPEED > 0


# ============================================================
# 道具精灵测试
# ============================================================

def test_item_sprite_creation():
    """Item sprite should initialize with correct type and position."""
    it = Item(150, 200, "full_bomb")
    assert it.item_type == "full_bomb"
    assert it.rect.centerx == 150
    assert it.rect.y == 200
    assert it.image is not None
    assert it.image.get_width() > 0


def test_item_sprite_falls_down():
    """Item sprite should move downward each frame."""
    it = Item(100, 50, "time_slow")
    y_before = it.rect.y
    it.update()
    assert it.rect.y == y_before + ITEM_FALL_SPEED


def test_item_sprite_offscreen_kill():
    """Item sprite should be killed when falling off the bottom."""
    group = pygame.sprite.Group()
    it = Item(100, 50, "reflect_shield", group)
    assert it.alive()
    # Move far off-screen then update
    it.rect.y = SCREEN_HEIGHT + 50
    it.update()
    assert not it.alive()


def test_item_sprite_pulse():
    """Item sprite should have pulsing alpha effect."""
    it = Item(100, 100, "repair")
    # alpha is controlled in update() — check via set_alpha
    alpha_before = it.image.get_alpha()
    it.update()
    # Alpha should change (not always the same)
    alphas = set()
    for _ in range(60):
        alphas.add(it.image.get_alpha())
        it.update()
    # At least 2 different alpha values indicates pulsing
    assert len(alphas) > 1


def test_all_item_types_have_sprites():
    """Every item type should create a valid sprite surface."""
    for itype in ITEM_TYPES:
        it = Item(100, 100, itype)
        assert it.image.get_width() > 0
        assert it.image.get_height() > 0


# ============================================================
# 玩家背包/库存测试
# ============================================================

def test_inventory_starts_empty():
    """Player should start with an empty inventory."""
    p = Player()
    assert not p.has_item()
    assert p.can_collect_item()
    assert len(p.inventory) == 0


def test_collect_item():
    """Collecting an item should add it to inventory."""
    p = Player()
    result = p.collect_item("full_bomb")
    assert result is True
    assert p.has_item()
    assert len(p.inventory) == 1
    assert p.inventory[0] == "full_bomb"


def test_collect_multiple_items():
    """Player can collect up to ITEM_MAX_INVENTORY items."""
    p = Player()
    p.collect_item("full_bomb")
    p.collect_item("time_slow")
    p.collect_item("repair")
    assert len(p.inventory) == ITEM_MAX_INVENTORY
    assert not p.can_collect_item()


def test_inventory_full_rejects():
    """Collecting more than max should be rejected."""
    p = Player()
    for _ in range(ITEM_MAX_INVENTORY):
        p.collect_item("full_bomb")
    result = p.collect_item("score_boost")
    assert result is False
    assert len(p.inventory) == ITEM_MAX_INVENTORY


def test_use_item_returns_first():
    """Using an item should return and remove the leftmost (first) item."""
    p = Player()
    p.collect_item("full_bomb")
    p.collect_item("time_slow")
    p.collect_item("repair")
    result = p.use_item()
    assert result is not None
    item_type, config = result
    assert item_type == "full_bomb"
    assert "color" in config
    assert len(p.inventory) == 2
    assert p.inventory[0] == "time_slow"  # shifted


def test_use_item_empty_inventory():
    """Using an item with empty inventory should return None."""
    p = Player()
    result = p.use_item()
    assert result is None


def test_use_item_cooldown():
    """Using an item should set a cooldown that blocks immediate reuse."""
    p = Player()
    p.collect_item("full_bomb")
    p.collect_item("repair")
    result1 = p.use_item()
    assert result1 is not None
    assert p.inventory_cooldown > 0
    # Should be blocked by cooldown
    result2 = p.use_item()
    assert result2 is None
    assert len(p.inventory) == 1  # second item not consumed


def test_cooldown_decays():
    """Cooldown should decrease each frame via _update_item_timers."""
    p = Player()
    p.collect_item("full_bomb")
    p.collect_item("repair")
    p.use_item()  # cooldown = 10
    cd_before = p.inventory_cooldown
    for _ in range(3):
        p._update_item_timers()
    assert p.inventory_cooldown == cd_before - 3


def test_cooldown_expires():
    """Cooldown should eventually allow next use."""
    p = Player()
    p.collect_item("full_bomb")
    p.collect_item("repair")
    p.use_item()
    for _ in range(20):
        p._update_item_timers()
    assert p.inventory_cooldown == 0
    result = p.use_item()
    assert result is not None
    assert result[0] == "repair"


# ============================================================
# 道具效果测试
# ============================================================

def test_activate_full_bomb():
    """Full bomb should set clear_enemies and clear_bullets flags."""
    p = Player()
    effect = p.activate_item_effect("full_bomb")
    assert effect["type"] == "full_bomb"
    assert effect.get("clear_enemies") is True
    assert effect.get("clear_bullets") is True


def test_activate_time_slow():
    """Time slow should set the timer and report active."""
    p = Player()
    effect = p.activate_item_effect("time_slow")
    assert effect["type"] == "time_slow"
    assert p.has_time_slow()
    assert p.time_slow_timer > 0


def test_time_slow_decays():
    """Time slow timer should decrease each frame."""
    p = Player()
    p.activate_item_effect("time_slow")
    timer_before = p.time_slow_timer
    p._update_item_timers()
    assert p.time_slow_timer == timer_before - 1


def test_time_slow_expires():
    """Time slow should eventually expire and report inactive."""
    p = Player()
    p.activate_item_effect("time_slow")
    for _ in range(p.time_slow_timer + 10):
        p._update_item_timers()
    assert not p.has_time_slow()
    assert p.time_slow_timer == 0


def test_activate_reflect_shield():
    """Reflect shield should set the timer."""
    p = Player()
    effect = p.activate_item_effect("reflect_shield")
    assert effect["type"] == "reflect_shield"
    assert p.has_reflect_shield()
    assert p.reflect_shield_timer > 0


def test_reflect_shield_blocks_hit():
    """Reflect shield should prevent player from taking damage."""
    p = Player()
    lives_before = p.lives
    p.reflect_shield_timer = 60
    result = p.hit()
    assert result is False
    assert p.lives == lives_before  # no damage taken


def test_reflect_shield_blocks_enemy_bullets():
    """Reflect shield should return False from enemy bullet collision."""
    p = Player()
    p.reflect_shield_timer = 60

    bullets = pygame.sprite.Group()
    eb = EnemyBullet(100, 100, p.rect.centerx, p.rect.centery)
    bullets.add(eb)
    explosions = pygame.sprite.Group()

    result = check_enemy_bullet_player_collisions(p, bullets, explosions)
    assert result is False  # blocked


def test_reflect_shield_blocks_enemy_body_collision():
    """Reflect shield should prevent damage from enemy body collision."""
    p = Player()
    p.reflect_shield_timer = 60

    enemies = pygame.sprite.Group()
    enemy = Enemy("basic")
    enemy.rect.center = p.rect.center
    enemies.add(enemy)
    explosions = pygame.sprite.Group()

    result = check_player_enemy_collisions(p, enemies, explosions)
    assert result is False  # blocked
    assert len(enemies) == 0  # enemy destroyed


def test_reflect_shield_expires():
    """Reflect shield should expire after timer runs out."""
    p = Player()
    p.reflect_shield_timer = 10
    for _ in range(20):
        p._update_item_timers()
    assert not p.has_reflect_shield()


def test_activate_repair_gains_life():
    """Repair should restore 1 life when not at max."""
    p = Player()
    p.lives = 1
    effect = p.activate_item_effect("repair")
    assert effect["type"] == "repair"
    assert effect.get("healed") is True
    assert p.lives == 2


def test_repair_at_max_no_effect():
    """Repair should not heal when already at max lives."""
    p = Player()
    lives_before = p.lives
    effect = p.activate_item_effect("repair")
    assert effect.get("healed") is False
    assert p.lives == lives_before


def test_activate_score_boost():
    """Score boost should activate and report active."""
    p = Player()
    effect = p.activate_item_effect("score_boost")
    assert effect["type"] == "score_boost"
    assert p.has_score_boost()
    assert p.score_boost_timer > 0


def test_score_boost_multiplier():
    """Score boost should double the score multiplier."""
    p = Player()
    p.combo_multiplier = 1.0
    assert p.get_score_multiplier() == 1.0
    p.activate_item_effect("score_boost")
    assert p.get_score_multiplier() == 2.0


def test_score_boost_stacks_with_combo():
    """Score boost should multiply with combo multiplier."""
    p = Player()
    p.combo_multiplier = 2.0
    p.activate_item_effect("score_boost")
    assert p.get_score_multiplier() == 4.0


def test_activate_gravity_bomb():
    """Gravity bomb should set pull_enemies and gravity_damage flags."""
    p = Player()
    effect = p.activate_item_effect("gravity_bomb")
    assert effect["type"] == "gravity_bomb"
    assert effect.get("pull_enemies") is True
    assert effect.get("gravity_damage") is True


def test_gravity_bomb_damages_enemies():
    """Gravity bomb should damage all enemies and return score."""
    enemies = pygame.sprite.Group()
    explosions = pygame.sprite.Group()

    e1 = Enemy("basic", eid=1)
    e1.rect.center = (100, 100)
    e2 = Enemy("basic", eid=2)
    e2.rect.center = (200, 150)
    enemies.add(e1, e2)

    score = apply_gravity_bomb(enemies, explosions)
    # Each basic enemy = 10, gravity bomb does 3 dmg (kills basic with 1 HP)
    assert score >= 20


def test_gravity_bomb_does_not_affect_game_over():
    """Gravity bomb on empty group should return 0 score."""
    enemies = pygame.sprite.Group()
    explosions = pygame.sprite.Group()
    score = apply_gravity_bomb(enemies, explosions)
    assert score == 0


# ============================================================
# 玩家-道具拾取碰撞测试
# ============================================================

def test_player_picks_up_item():
    """Player should collect item when touching it."""
    p = Player()
    items = pygame.sprite.Group()

    it = Item(p.rect.centerx, p.rect.centery, "full_bomb")
    items.add(it)

    collected = check_player_item_collisions(p, items)
    assert collected == "full_bomb"
    assert p.has_item()
    assert p.inventory[0] == "full_bomb"
    assert len(items) == 0  # item consumed


def test_player_picks_up_different_items():
    """Player should collect different item types."""
    p = Player()
    items = pygame.sprite.Group()

    Item(p.rect.centerx, p.rect.centery, "time_slow", items)
    collected = check_player_item_collisions(p, items)
    assert collected == "time_slow"
    assert p.inventory[0] == "time_slow"


def test_full_inventory_rejects_pickup():
    """Item should not be collected when inventory is full."""
    p = Player()
    p.collect_item("full_bomb")
    p.collect_item("time_slow")
    p.collect_item("repair")

    items = pygame.sprite.Group()
    it = Item(p.rect.centerx, p.rect.centery, "score_boost", items)

    collected = check_player_item_collisions(p, items)
    assert collected is None  # not collected
    assert it in items  # item still exists in the group
    assert len(p.inventory) == ITEM_MAX_INVENTORY


def test_pickup_no_items_noop():
    """Collision check with empty items group should not crash."""
    p = Player()
    items = pygame.sprite.Group()
    result = check_player_item_collisions(p, items)
    assert result is None


# ============================================================
# 敌人/子弹速度倍率测试（时间减速）
# ============================================================

def test_enemy_speed_multiplier_default():
    """Enemy should default to speed_multiplier = 1.0."""
    enemy = Enemy("basic")
    assert enemy.speed_multiplier == 1.0


def test_enemy_speed_multiplier_affects_movement():
    """Enemy should move slower with reduced speed_multiplier."""
    e1 = Enemy("basic")
    e2 = Enemy("basic")
    e1.rect.y = e2.rect.y = 100
    e1.speed_multiplier = 0.5
    e2.speed_multiplier = 1.0
    e1.update()
    e2.update()
    assert e1.rect.y < e2.rect.y


def test_enemy_bullet_speed_multiplier_default():
    """EnemyBullet should default to speed_multiplier = 1.0."""
    eb = EnemyBullet(100, 100, 200, 200)
    assert eb.speed_multiplier == 1.0


def test_enemy_bullet_speed_multiplier_affects_movement():
    """EnemyBullet should move slower with reduced speed_multiplier."""
    eb1 = EnemyBullet(100, 100, 100, 200)  # straight down
    eb2 = EnemyBullet(100, 100, 100, 200)
    eb1.speed_multiplier = 0.5
    eb2.speed_multiplier = 1.0
    eb1.update()
    eb2.update()
    # eb2 should have moved further (downward = positive y)
    assert eb1.rect.y < eb2.rect.y


# ============================================================
# 重置测试
# ============================================================

def test_reset_clears_inventory():
    """Player.reset() should empty the inventory."""
    p = Player()
    p.collect_item("full_bomb")
    p.collect_item("time_slow")
    p.activate_item_effect("time_slow")
    p.reset()
    assert len(p.inventory) == 0
    assert p.inventory_cooldown == 0
    assert not p.has_time_slow()
    assert not p.has_reflect_shield()
    assert p.score_boost_timer == 0


def test_item_cooldown_persists_across_game():
    """Item cooldown should start fresh when using items."""
    p = Player()
    p.collect_item("full_bomb")
    p.use_item()
    assert p.inventory_cooldown >= 0  # no crash on reset
    p.reset()
    assert p.inventory_cooldown == 0


# ============================================================
# 反射子弹行为测试
# ============================================================

def test_enemy_bullet_reflect_goes_upward():
    """Reflected bullet should change direction upward."""
    eb = EnemyBullet(100, 100, 200, 200)
    assert eb.vy > 0  # moving downward toward player
    assert not eb.reflected
    eb.reflect()
    assert eb.reflected
    assert eb.vy < 0  # now moving upward
    assert eb.px == 100
    assert eb.py == 100


def test_reflected_bullet_has_different_color():
    """Reflected bullet should have a gold-tinted surface."""
    eb = EnemyBullet(100, 100, 200, 200)
    eb.reflect()
    # Check that the surface was recreated
    pixel = eb.image.get_at((eb.image.get_width() // 2, eb.image.get_height() // 2))
    r, g, b = pixel[0], pixel[1], pixel[2]
    # Should be yellowish/gold
    assert r > 200
    assert g > 150


# ============================================================
# 完整生命周期测试
# ============================================================

def test_full_item_lifecycle():
    """Full lifecycle: collect → use → effect → expire."""
    p = Player()
    # Collect
    p.collect_item("time_slow")
    assert p.has_item()
    # Use
    result = p.use_item()
    assert result is not None
    assert result[0] == "time_slow"
    # Activate
    p.activate_item_effect("time_slow")
    assert p.has_time_slow()
    # Timer decays
    for _ in range(p.time_slow_timer + 5):
        p._update_item_timers()
    # Expires
    assert not p.has_time_slow()
    assert not p.has_item()


def test_inventory_fifo_order():
    """Items should be used in FIFO (first-in-first-out) order."""
    p = Player()
    p.collect_item("full_bomb")
    p.collect_item("repair")
    p.collect_item("score_boost")
    p.inventory_cooldown = 0
    r1 = p.use_item()
    assert r1[0] == "full_bomb"
    p.inventory_cooldown = 0
    r2 = p.use_item()
    assert r2[0] == "repair"
    p.inventory_cooldown = 0
    r3 = p.use_item()
    assert r3[0] == "score_boost"
    assert not p.has_item()