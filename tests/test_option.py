"""Tests for Option satellite system."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.set_mode((1, 1))
pygame.font.init()

from game.settings import OPTION_MAX_COUNT
from game.sprites.player import Player
from game.sprites.option import Option


def test_no_options_by_default():
    p = Player()
    assert len(p.options) == 0


def test_add_option_increases_count():
    p = Player()
    p.add_option()
    assert len(p.options) == 1


def test_add_option_up_to_max():
    p = Player()
    for _ in range(OPTION_MAX_COUNT):
        p.add_option()
    assert len(p.options) == OPTION_MAX_COUNT


def test_add_beyond_max_ignored():
    p = Player()
    for _ in range(OPTION_MAX_COUNT + 3):
        p.add_option()
    assert len(p.options) == OPTION_MAX_COUNT


def test_remove_options_clears():
    p = Player()
    p.add_option()
    p.add_option()
    assert len(p.options) == 2
    p.remove_options()
    assert len(p.options) == 0


def test_option_has_position():
    p = Player()
    p.rect.centerx = 240
    p.rect.bottom = 600
    opt = Option(p, 0)
    assert opt.rect is not None
    assert opt.rect.centerx > 0


def test_option_follows_player():
    p = Player()
    opt = Option(p, 0)

    # Move player right
    p.rect.centerx = 300
    opt.update_position(p.rect.centerx, p.rect.centery, p.rect.bottom)

    # Option should have moved toward new position
    center_before = opt.rect.centerx
    p.rect.centerx = 400
    for _ in range(10):
        opt.update_position(p.rect.centerx, p.rect.centery, p.rect.bottom)

    assert opt.rect.centerx > center_before


def test_option_get_shoot_position():
    p = Player()
    p.rect.centerx = 240
    p.rect.bottom = 600
    opt = Option(p, 0)
    opt.update_position(p.rect.centerx, p.rect.centery, p.rect.bottom)
    x, y = opt.get_shoot_position()
    assert x > 0
    assert y > 0


def test_option_shoot_state_delayed():
    """Option should delay shooting by OPTION_SHOOT_DELAY frames."""
    from game.settings import OPTION_SHOOT_DELAY
    p = Player()
    opt = Option(p, 0)

    # Player fires
    opt.update_shoot_state(True)
    assert not opt.should_fire  # delayed

    # Wait for delay
    for _ in range(OPTION_SHOOT_DELAY + 1):
        opt.update_shoot_state(True)

    assert opt.should_fire


def test_apply_option_powerup():
    p = Player()
    assert len(p.options) == 0
    p.apply_powerup("option")
    assert len(p.options) == 1
