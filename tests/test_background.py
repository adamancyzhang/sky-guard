# tests/test_background.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.set_mode((1, 1))

from game.settings import BACKGROUND_LAYERS, SCREEN_WIDTH, SCREEN_HEIGHT, BG_THEMES, BG_TRANSITION_DURATION
from game.graphics.background import generate_layer_surface, ScrollingBackground, LevelBackgroundManager


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


# ── New background system tests ───────────────────────────────────

def test_bg_themes_all_levels_defined():
    """Every level in DIFFICULTY_STEPS should have a BG_THEME."""
    from game.settings import DIFFICULTY_STEPS
    for level in DIFFICULTY_STEPS:
        assert level in BG_THEMES, f"Level {level} missing from BG_THEMES"


def test_level_background_manager_init():
    """LevelBackgroundManager starts at level 0."""
    bg = LevelBackgroundManager()
    assert bg.current_level == 0
    assert len(bg.layers) == len(BG_THEMES[0]["layers"])


def test_switch_to_level_changes_theme():
    """Switching level changes the layer surfaces."""
    bg = LevelBackgroundManager()
    old_surf = bg.layers[0]["surface"]
    bg.switch_to_level(3)
    new_surf = bg.layers[0]["surface"]
    assert old_surf is not new_surf


def test_switch_to_level_returns_false_for_same():
    """Switching to the same level returns False."""
    bg = LevelBackgroundManager()
    result = bg.switch_to_level(0)
    assert result is False


def test_switch_to_level_creates_transition():
    """Switching level creates a TransitionEffect."""
    bg = LevelBackgroundManager()
    assert bg.transition is None
    bg.switch_to_level(2)
    assert bg.transition is not None
    assert not bg.transition.is_done()


def test_boss_mode_overlay():
    """Boss mode applies visual overlay (survives draw)."""
    bg = LevelBackgroundManager()
    bg.set_boss_mode(True)
    assert bg.boss_active is True
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    bg.update()
    bg.draw(surf)  # should not crash


def test_particle_system_per_theme():
    """Each theme should have correct particle configs loaded."""
    for level in BG_THEMES:
        bg = LevelBackgroundManager()
        bg.switch_to_level(level)
        bg.update()
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.draw(surf)  # should not crash with any particle config


def test_update_wraps_all_layers():
    """y_offset wraps correctly for all layers after many updates."""
    bg = LevelBackgroundManager()
    for _ in range(1000):
        bg.update()
    for layer in bg.layers:
        assert layer["y_offset"] < SCREEN_HEIGHT
        assert layer["y_offset"] >= 0


def test_transition_completes():
    """Transition should be done after duration frames."""
    bg = LevelBackgroundManager()
    bg.switch_to_level(4)
    for _ in range(BG_TRANSITION_DURATION + 5):
        bg.update()
    assert bg.transition is None or bg.transition.is_done()


def test_speed_increases_with_level():
    """Higher levels should scroll faster (speed_mult > 1)."""
    bg = LevelBackgroundManager()
    bg.switch_to_level(0)
    # Record movement at level 0
    bg.update()
    offset_l0 = bg.layers[0]["y_offset"]

    bg = LevelBackgroundManager()
    bg.switch_to_level(5)
    bg.update()
    offset_l5 = bg.layers[0]["y_offset"]

    assert offset_l5 > offset_l0, "Level 5 should scroll faster than level 0"


def test_boss_mode_restores_theme_particles():
    """After boss mode off, particle system reverts to theme particles."""
    bg = LevelBackgroundManager()
    bg.switch_to_level(2)
    theme_particles = bg.current_theme.get("particles", [])
    bg.set_boss_mode(True)
    assert bg.boss_active is True
    bg.set_boss_mode(False)
    assert bg.boss_active is False
    # particle system should be reset to theme particles
    assert bg.particle_system.configs == theme_particles


def test_switch_clamps_max_level():
    """Switching beyond max clamped to highest level."""
    bg = LevelBackgroundManager()
    bg.switch_to_level(999)
    assert bg.current_level <= max(BG_THEMES.keys())