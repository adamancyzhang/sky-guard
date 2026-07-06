# tests/test_background.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.set_mode((1, 1))

from game.settings import BACKGROUND_LAYERS, SCREEN_WIDTH, SCREEN_HEIGHT
from game.graphics.background import generate_layer_surface, ScrollingBackground


def test_background_layers_defined():
    """Verify BACKGROUND_LAYERS has all expected layers."""
    names = [l["name"] for l in BACKGROUND_LAYERS]
    assert "sky" in names
    assert "mountains" in names
    assert "city" in names
    assert "ground" in names


def test_generate_layer_sky():
    """Sky layer should be a surface of SCREEN_WIDTH x SCREEN_HEIGHT."""
    cfg = {"name": "sky", "speed": 0.3, "color": (10, 10, 40)}
    surf = generate_layer_surface(cfg)
    assert surf.get_width() == SCREEN_WIDTH
    assert surf.get_height() == SCREEN_HEIGHT


def test_generate_layer_city():
    """City layer should be a surface, not crash."""
    cfg = {"name": "city", "speed": 1.2, "color": (25, 25, 45)}
    surf = generate_layer_surface(cfg)
    assert surf.get_width() == SCREEN_WIDTH


def test_scrolling_background_update():
    """ScrollingBackground.update() should increase y_offset."""
    bg = ScrollingBackground()
    initial = bg.layers[0]["y_offset"]
    for _ in range(10):
        bg.update()
    assert bg.layers[0]["y_offset"] > initial


def test_scrolling_background_wrap():
    """y_offset should wrap at SCREEN_HEIGHT."""
    bg = ScrollingBackground()
    bg.layers[0]["y_offset"] = SCREEN_HEIGHT - 1
    bg.update()
    assert bg.layers[0]["y_offset"] < SCREEN_HEIGHT


def test_scrolling_background_draw():
    """draw() should not crash."""
    bg = ScrollingBackground()
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    bg.draw(surf)  # should not raise
    assert surf.get_at((0, 0)) is not None