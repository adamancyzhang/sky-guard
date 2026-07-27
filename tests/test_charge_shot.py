"""Tests for charge shot mechanics."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.set_mode((1, 1))
pygame.font.init()

from game.settings import CHARGE_TIERS
from game.sprites.player import Player


def test_initial_charge_state():
    p = Player()
    assert p.charge_tier == 0
    assert not p.is_charging
    assert p.charge_timer == 0
    assert not p.charge_released


def test_start_charge_sets_flag():
    p = Player()
    p.start_charge()
    assert p.is_charging
    assert not p.charge_released


def test_continue_charge_increases_timer():
    p = Player()
    p.start_charge()
    for _ in range(10):
        p.continue_charge()
    assert p.charge_timer == 10


def test_charge_reaches_tier_1():
    p = Player()
    p.start_charge()
    tier_1_frames = CHARGE_TIERS[0]["hold_frames"]
    for _ in range(tier_1_frames):
        p.continue_charge()
    assert p.charge_tier >= 1


def test_charge_reaches_tier_2():
    p = Player()
    p.start_charge()
    tier_2_frames = CHARGE_TIERS[1]["hold_frames"]
    for _ in range(tier_2_frames):
        p.continue_charge()
    assert p.charge_tier >= 2


def test_charge_reaches_tier_3():
    p = Player()
    p.start_charge()
    tier_3_frames = CHARGE_TIERS[2]["hold_frames"]
    for _ in range(tier_3_frames):
        p.continue_charge()
    assert p.charge_tier == 3


def test_release_charge_returns_true_and_tier():
    p = Player()
    p.start_charge()
    for _ in range(CHARGE_TIERS[0]["hold_frames"] + 5):
        p.continue_charge()
    released, tier = p.release_charge()
    assert released
    assert tier >= 1
    assert not p.is_charging


def test_release_without_enough_charge():
    p = Player()
    p.start_charge()
    # Release before tier 1 threshold
    released, tier = p.release_charge()
    assert not released
    assert tier == 0
    assert not p.is_charging


def test_cancel_charge_resets_state():
    p = Player()
    p.start_charge()
    for _ in range(30):
        p.continue_charge()
    assert p.is_charging
    assert p.charge_timer > 0
    p.cancel_charge()
    assert not p.is_charging
    assert p.charge_timer == 0
    assert p.charge_tier == 0


def test_charge_progress_zero_when_not_charging():
    p = Player()
    assert p.get_charge_progress() == 0.0


def test_charge_progress_increases():
    p = Player()
    p.start_charge()
    for _ in range(10):
        p.continue_charge()
    progress = p.get_charge_progress()
    assert 0 < progress < 1.0


def test_charge_progress_full():
    p = Player()
    p.start_charge()
    for _ in range(CHARGE_TIERS[2]["hold_frames"] + 10):
        p.continue_charge()
    assert p.get_charge_progress() == 1.0


def test_get_charge_tier_config():
    p = Player()
    cfg = p.get_charge_tier_config(1)
    assert cfg is not None
    assert cfg["damage_mult"] > 0
    cfg3 = p.get_charge_tier_config(3)
    assert cfg3.get("piercing") is True


def test_get_charge_tier_config_invalid():
    p = Player()
    assert p.get_charge_tier_config(0) is None
    assert p.get_charge_tier_config(99) is None
