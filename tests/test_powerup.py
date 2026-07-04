import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game.settings import POWERUP_TYPES, POWERUP_DROP_CHANCE


def test_powerup_types_defined():
    assert "shield" in POWERUP_TYPES
    assert "rapid" in POWERUP_TYPES
    assert "triple" in POWERUP_TYPES
    assert "bomb" in POWERUP_TYPES
    assert "speed" in POWERUP_TYPES
    assert "life" in POWERUP_TYPES


def test_powerup_drop_chance():
    assert 0 < POWERUP_DROP_CHANCE < 1


def test_powerup_configs():
    for ptype, config in POWERUP_TYPES.items():
        assert "color" in config
        assert "duration" in config
        assert isinstance(config["duration"], int)
        assert config["duration"] >= 0


def test_powerup_descriptions():
    for ptype, config in POWERUP_TYPES.items():
        assert "description_key" in config
        assert config["description_key"].startswith("item_")