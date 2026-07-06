# tests/test_highscore.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tempfile
import json

# Patch the file path before importing
import game.highscore
game.highscore.HIGHSCORE_FILE = os.path.join(tempfile.gettempdir(), "test_highscore.json")

from game.highscore import HighScore


def setup():
    """Clean up test file before each test."""
    if os.path.exists(game.highscore.HIGHSCORE_FILE):
        os.remove(game.highscore.HIGHSCORE_FILE)


def test_highscore_default_zero():
    """No file = high score 0."""
    setup()
    assert HighScore.load() == 0


def test_highscore_save():
    """Saving a score should persist it."""
    setup()
    result = HighScore.save_if_beaten(100)
    assert result is True
    assert HighScore.load() == 100


def test_highscore_not_beaten():
    """Lower score should not overwrite."""
    setup()
    HighScore.save_if_beaten(200)
    result = HighScore.save_if_beaten(150)
    assert result is False
    assert HighScore.load() == 200


def test_highscore_beaten():
    """Higher score should overwrite."""
    setup()
    HighScore.save_if_beaten(100)
    result = HighScore.save_if_beaten(300)
    assert result is True
    assert HighScore.load() == 300


def test_highscore_reset():
    """Reset should set score to 0."""
    setup()
    HighScore.save_if_beaten(500)
    HighScore.reset()
    assert HighScore.load() == 0