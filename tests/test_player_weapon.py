"""Tests for player weapon leveling and weapon type switching."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.set_mode((1, 1))
pygame.font.init()

from game.settings import WEAPON_LEVEL_CONFIGS, WEAPON_TYPES, MAX_WEAPON_LEVEL
from game.sprites.player import Player


def test_initial_weapon_level_is_one():
    p = Player()
    assert p.get_weapon_level("normal") == 1


def test_upgrade_increases_level():
    p = Player()
    p.upgrade_weapon("normal")
    assert p.get_weapon_level("normal") == 2


def test_upgrade_caps_at_max():
    p = Player()
    for _ in range(MAX_WEAPON_LEVEL + 5):
        p.upgrade_weapon("normal")
    assert p.get_weapon_level("normal") == MAX_WEAPON_LEVEL


def test_downgrade_decreases_level():
    p = Player()
    p.upgrade_weapon("normal")
    p.upgrade_weapon("normal")
    p.downgrade_weapon("normal")
    assert p.get_weapon_level("normal") == 2


def test_downgrade_floor_is_one():
    p = Player()
    p.downgrade_weapon("normal")
    assert p.get_weapon_level("normal") == 1


def test_switch_weapon_cycles_forward():
    p = Player()
    p.available_weapons = ["normal", "spread"]
    assert p.active_weapon == "normal"
    p.switch_weapon(1)
    assert p.active_weapon == "spread"


def test_switch_weapon_cycles_backward():
    p = Player()
    p.available_weapons = ["normal", "spread"]
    p.switch_weapon(-1)
    assert p.active_weapon == "spread"


def test_switch_weapon_wraps():
    p = Player()
    p.available_weapons = ["normal", "spread"]
    p.switch_weapon(1)
    p.switch_weapon(1)
    assert p.active_weapon == "normal"


def test_single_weapon_no_switch():
    p = Player()
    p.available_weapons = ["normal"]
    p.switch_weapon(1)
    assert p.active_weapon == "normal"


def test_unlock_adds_to_available():
    p = Player()
    assert "laser" not in p.available_weapons
    p.unlock_weapon("laser")
    assert "laser" in p.available_weapons
    assert "laser" in p.unlocked_weapons


def test_unlock_ignores_duplicate():
    p = Player()
    p.unlock_weapon("normal")
    assert len(p.unlocked_weapons) == 1


def test_unlock_ignores_invalid_type():
    p = Player()
    result = p.unlock_weapon("invalid")
    assert result is False


def test_get_weapon_config_returns_valid():
    p = Player()
    cfg = p.get_weapon_config("normal")
    assert cfg["count"] >= 1
    assert cfg["damage"] >= 1
    assert cfg["speed_mult"] > 0
    assert cfg["cooldown_mult"] > 0


def test_all_weapon_types_have_configs():
    for wt in WEAPON_TYPES:
        configs = WEAPON_LEVEL_CONFIGS.get(wt)
        assert configs is not None, f"Missing config for {wt}"
        for level in range(1, MAX_WEAPON_LEVEL + 1):
            cfg = configs.get(level)
            assert cfg is not None, f"Missing {wt} level {level}"
            assert cfg["count"] >= 1
            assert cfg["damage"] >= 1
            assert cfg["speed_mult"] > 0
            assert cfg["cooldown_mult"] > 0
