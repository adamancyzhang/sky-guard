# game/graphics/screen_shake.py
import pygame
import random
import math


class ScreenShake:
    """Screen shake effect manager.

    Accumulates shake intensity from events and produces an offset vector
    that decays over time.
    """

    def __init__(self):
        self.intensity = 0.0       # Current shake magnitude (pixels)
        self.decay_rate = 0.85     # Multiplier per frame
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.shake_angle = 0.0

    def shake(self, intensity=4.0):
        """Trigger a shake with given initial intensity."""
        self.intensity = max(self.intensity, intensity)
        self.shake_angle = random.uniform(0, math.pi * 2)

    def update(self):
        """Update shake state. Call once per frame."""
        if self.intensity > 0.2:
            # Perlin-ish jitter: random angle that changes slowly
            self.shake_angle += random.uniform(-0.5, 0.5)
            self.offset_x = math.cos(self.shake_angle) * self.intensity
            self.offset_y = math.sin(self.shake_angle) * self.intensity
            self.intensity *= self.decay_rate
        else:
            self.intensity = 0.0
            self.offset_x = 0.0
            self.offset_y = 0.0

    def get_offset(self):
        """Return (dx, dy) pixel offset to apply to rendering."""
        return (int(self.offset_x), int(self.offset_y))

    def is_shaking(self):
        return self.intensity > 0.2