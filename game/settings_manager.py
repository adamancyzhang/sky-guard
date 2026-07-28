# game/settings_manager.py
import json
import os

SETTINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")

_DEFAULT = {
    "sfx_volume": 0.7,
    "music_volume": 0.5,
    "muted": False,
}


def load():
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            # Merge with defaults to handle missing keys after updates
            merged = dict(_DEFAULT)
            merged.update(data)
            return merged
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return dict(_DEFAULT)


def save(settings: dict):
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    # Read existing, merge, write
    current = load()
    current.update(settings)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(current, f, indent=2)


def get(key: str, default=None):
    return load().get(key, default)
