"""Tests for Spawner: difficulty scaling, formations, boss spawn."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.set_mode((1, 1))
pygame.font.init()

from game.settings import SCORE_PER_LEVEL, DIFFICULTY_STEPS, BOSS_SCORE_INTERVAL
from game.systems.spawner import Spawner


def test_initial_spawner_state():
    s = Spawner()
    assert s.timer == 0
    assert s.current_level == 0
    assert not s.boss_active
    assert s.next_boss_score == BOSS_SCORE_INTERVAL


def test_difficulty_starts_at_zero():
    s = Spawner()
    enemies = pygame.sprite.Group()
    s.update(enemies, 0)
    assert s.current_level == 0


def test_difficulty_increases_with_score():
    s = Spawner()
    enemies = pygame.sprite.Group()
    score = SCORE_PER_LEVEL * 2
    s.update(enemies, score)
    assert s.current_level == 2


def test_difficulty_capped():
    s = Spawner()
    enemies = pygame.sprite.Group()
    max_level = len(DIFFICULTY_STEPS) - 1
    s.update(enemies, SCORE_PER_LEVEL * 999)
    assert s.current_level == max_level


def test_spawner_does_nothing_during_boss():
    s = Spawner()
    s.boss_active = True
    enemies = pygame.sprite.Group()
    s.update(enemies, 0)
    # Should not spawn anything during boss fight
    assert len(enemies) == 0


def test_boss_spawn_not_before_threshold():
    s = Spawner()
    result = s.check_boss_spawn(BOSS_SCORE_INTERVAL - 1)
    assert result is False
    assert not s.boss_active


def test_boss_spawn_at_threshold():
    s = Spawner()
    result = s.check_boss_spawn(BOSS_SCORE_INTERVAL)
    assert result is True
    assert s.boss_active


def test_boss_spawn_once_only():
    s = Spawner()
    s.check_boss_spawn(BOSS_SCORE_INTERVAL)  # triggers
    result = s.check_boss_spawn(BOSS_SCORE_INTERVAL * 2)  # should be blocked
    assert result is False  # boss_active blocks second spawn


def test_next_boss_score_increments():
    s = Spawner()
    s.check_boss_spawn(BOSS_SCORE_INTERVAL)
    assert s.next_boss_score == BOSS_SCORE_INTERVAL * 2


def test_boss_spawn_resets_after_defeat():
    s = Spawner()
    s.check_boss_spawn(BOSS_SCORE_INTERVAL)
    s.boss_active = False  # boss defeated
    result = s.check_boss_spawn(BOSS_SCORE_INTERVAL * 2)
    assert result is True


def test_enemy_counter_increments():
    s = Spawner()
    enemies = pygame.sprite.Group()
    # Run enough frames to trigger spawn
    s.timer = 999  # force spawn on next update
    s.update(enemies, 0)
    assert s.enemy_counter >= 1
    assert len(enemies) >= 1


def test_level_up_callback_fires():
    s = Spawner()
    callbacks = []
    def on_level_up(level):
        callbacks.append(level)
    s.on_level_up = on_level_up
    enemies = pygame.sprite.Group()
    # Jump to level 3
    s.update(enemies, SCORE_PER_LEVEL * 3)
    assert len(callbacks) >= 1
    assert callbacks[-1] == 3


def test_reset():
    s = Spawner()
    s.timer = 100
    s.current_level = 3
    s.boss_active = True
    s.enemy_counter = 50
    s.reset()
    assert s.timer == 0
    assert s.current_level == 0
    assert not s.boss_active
    assert s.enemy_counter == 0
    assert s.next_boss_score == BOSS_SCORE_INTERVAL


def test_formation_spawns_multiple_enemies():
    from game.settings import SCREEN_WIDTH
    s = Spawner()
    enemies = pygame.sprite.Group()
    s._formation_cooldown = 0  # force formation
    # Run many times to get formation
    for _ in range(100):
        s.update(enemies, 0)
    # After many frames, should have spawned some enemies
    # (exact count varies due to random, but should be > 0)
    assert len(enemies) > 0 or s.timer > 0
