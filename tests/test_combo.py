"""Tests for combo system."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.set_mode((1, 1))
pygame.font.init()

from game.settings import COMBO_THRESHOLD, COMBO_BUFF_FRAMES
from game.sprites.player import Player


def test_combo_starts_at_zero():
    p = Player()
    assert p.combo_count == 0
    assert p.combo_tier == 0
    assert p.combo_multiplier == 1.0
    assert not p.has_combo_buff()


def test_register_kill_increments():
    p = Player()
    p.register_kill()
    assert p.combo_count == 1


def test_register_kill_sets_timer():
    p = Player()
    p.register_kill()
    assert p.combo_timer > 0


def test_milestone_at_threshold():
    p = Player()
    for _ in range(COMBO_THRESHOLD - 1):
        p.register_kill()
    # No milestone yet
    assert p.combo_tier == 0
    assert p.combo_multiplier == 1.0
    # Threshold kill triggers milestone
    milestone = p.register_kill()
    assert milestone
    assert p.combo_tier == 1
    assert p.combo_multiplier > 1.0
    assert p.has_combo_buff()


def test_combo_buff_has_duration():
    p = Player()
    for _ in range(COMBO_THRESHOLD):
        p.register_kill()
    assert p.combo_buff_timer == COMBO_BUFF_FRAMES


def test_combo_timer_expiry():
    p = Player()
    p.register_kill()
    assert p.combo_count == 1

    # update_combo decrements first, then checks
    p.combo_timer = 2
    p.update_combo()
    assert p.combo_count == 1  # timer went 2→1, still > 0

    p.update_combo()
    assert p.combo_count == 0  # timer went 1→0, expired


def test_combo_buff_decays():
    p = Player()
    for _ in range(COMBO_THRESHOLD):
        p.register_kill()
    assert p.has_combo_buff()

    p.combo_buff_timer = 1
    p.update_combo()
    assert not p.has_combo_buff()


def test_reset_combo_clears():
    p = Player()
    for _ in range(COMBO_THRESHOLD):
        p.register_kill()
    assert p.combo_count > 0

    p.reset_combo()
    assert p.combo_count == 0
    assert p.combo_tier == 0
    assert p.combo_multiplier == 1.0
    assert not p.has_combo_buff()


def test_multiple_milestones():
    p = Player()
    # Reach threshold twice
    for _ in range(COMBO_THRESHOLD * 2):
        p.register_kill()
    assert p.combo_tier >= 2
    assert p.combo_multiplier >= 1.5
