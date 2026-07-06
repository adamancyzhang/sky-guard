# tests/test_screen_shake.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.set_mode((1, 1))

from game.graphics.screen_shake import ScreenShake


def test_shake_initial():
    """ScreenShake starts with zero intensity."""
    ss = ScreenShake()
    assert ss.intensity == 0.0
    assert ss.get_offset() == (0, 0)


def test_shake_trigger():
    """After shake(), intensity should be set."""
    ss = ScreenShake()
    ss.shake(5.0)
    assert ss.intensity == 5.0


def test_shake_decay():
    """Intensity should decay over time."""
    ss = ScreenShake()
    ss.shake(10.0)
    initial = ss.intensity
    for _ in range(10):
        ss.update()
    assert ss.intensity < initial


def test_shake_returns_to_zero():
    """After enough updates, offset should be zero."""
    ss = ScreenShake()
    ss.shake(2.0)
    for _ in range(60):  # 60 frames
        ss.update()
    assert ss.is_shaking() is False
    assert ss.get_offset() == (0, 0)


def test_shake_accumulation():
    """Multiple shakes should stack (max wins)."""
    ss = ScreenShake()
    ss.shake(3.0)
    ss.shake(8.0)
    assert ss.intensity == 8.0  # max wins


def test_offset_nonzero_during_shake():
    """Offset should be non-zero while shaking."""
    ss = ScreenShake()
    ss.shake(5.0)
    ss.update()
    ox, oy = ss.get_offset()
    assert ox != 0 or oy != 0