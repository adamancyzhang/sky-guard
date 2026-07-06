# tests/test_boss.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.set_mode((1, 1))

from game.sprites.boss import Boss
from game.settings import BOSS_BASE_HP, BOSS_SCORE_VALUE, SCREEN_WIDTH, ENEMY_BULLET_SPEED


def test_boss_creation():
    """Boss should have correct initial stats."""
    boss = Boss()
    assert boss.hp == BOSS_BASE_HP
    assert boss.score_value == BOSS_SCORE_VALUE
    assert boss.phase == "entering"


def test_boss_entering_phase():
    """Boss should move down during entering phase."""
    boss = Boss()
    initial_y = boss.rect.y
    boss.update()
    assert boss.rect.y > initial_y


def test_boss_fighting_phase():
    """Boss should strafe horizontally after entering."""
    boss = Boss()
    boss.rect.y = 60  # at target y
    boss.phase = "fighting"
    initial_x = boss.rect.x
    boss.update()
    # Should have moved
    assert boss.rect.x != initial_x


def test_boss_take_damage():
    """Boss should lose HP when taking damage."""
    boss = Boss()
    boss.take_damage()
    assert boss.hp == BOSS_BASE_HP - 1


def test_boss_defeated():
    """Boss should be defeated after all HP depleted."""
    boss = Boss()
    for _ in range(BOSS_BASE_HP):
        boss.take_damage()
    assert boss.is_defeated()


def test_boss_get_bullet_vectors():
    """Boss should return bullet vectors for spread pattern."""
    from game.settings import BOSS_BULLET_CONFIGS
    boss = Boss()
    boss.rect.center = (SCREEN_WIDTH // 2, 100)
    vectors = boss.get_bullet_vectors(SCREEN_WIDTH // 2, 600)
    assert len(vectors) > 0
    for vx, vy in vectors:
        # Should be valid velocities
        assert abs(vx) <= ENEMY_BULLET_SPEED * 1.5
        assert abs(vy) <= ENEMY_BULLET_SPEED * 1.5


def test_boss_hp_ratio():
    """Boss HP ratio should decrease correctly."""
    boss = Boss()
    assert boss.get_hp_ratio() == 1.0
    boss.hp = boss.max_hp // 2
    assert abs(boss.get_hp_ratio() - 0.5) < 0.01


def test_boss_phase_transition_circle():
    """Boss should switch to circle pattern below 66% HP."""
    boss = Boss()
    boss.hp = int(boss.max_hp * 0.5)
    boss.phase = "fighting"
    boss.update()
    assert boss.current_pattern == "circle"


def test_boss_phase_transition_aimed():
    """Boss should switch to aimed pattern below 33% HP."""
    boss = Boss()
    boss.hp = int(boss.max_hp * 0.2)
    boss.phase = "fighting"
    boss.update()
    assert boss.current_pattern == "aimed"