# game/highscore.py
import json
import os

HIGHSCORE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "highscore.json")


class HighScore:
    """Persistent high score storage using JSON."""

    @classmethod
    def load(cls):
        """Load the saved high score, or 0 if not found."""
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                data = json.load(f)
                return data.get("highscore", 0)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            return 0

    @classmethod
    def save_if_beaten(cls, score):
        """Save score if it's higher than the current high score.
        Returns True if it's a new high score.
        """
        current = cls.load()
        if score > current:
            os.makedirs(os.path.dirname(HIGHSCORE_FILE), exist_ok=True)
            with open(HIGHSCORE_FILE, "w") as f:
                json.dump({"highscore": score}, f)
            return True
        return False

    @classmethod
    def reset(cls):
        """Reset high score to 0."""
        os.makedirs(os.path.dirname(HIGHSCORE_FILE), exist_ok=True)
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump({"highscore": 0}, f)