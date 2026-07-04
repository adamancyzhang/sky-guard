# game/sounds/sound_manager.py
import pygame
import math
import array
import random


class SoundManager:
    def __init__(self):
        self.available = True
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        except pygame.error:
            self.available = False
        self.sounds = {}
        if self.available:
            self._create_sounds()

    def _create_sounds(self):
        self.sounds["shoot"] = self._generate_tone(440, 0.08, "square")
        self.sounds["explosion"] = self._generate_noise(0.3)
        self.sounds["hit"] = self._generate_tone(220, 0.15, "saw")
        self.sounds["game_over"] = self._generate_sweep(400, 100, 0.5)
        self.sounds["level_up"] = self._generate_sweep(300, 600, 0.2)

    def _generate_tone(self, freq, duration, wave_type="sine"):
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        buf = array.array('h', [0]) * n_samples
        for i in range(n_samples):
            t = i / sample_rate
            if wave_type == "sine":
                val = math.sin(2 * math.pi * freq * t)
            elif wave_type == "square":
                val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
            elif wave_type == "saw":
                val = 2.0 * (freq * t - math.floor(freq * t + 0.5))
            else:
                val = 0
            # Fade out
            fade = 1.0 - (i / n_samples)
            buf[i] = int(val * 8000 * fade)
        return pygame.mixer.Sound(buffer=buf)

    def _generate_noise(self, duration):
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        buf = array.array('h', [0]) * n_samples
        for i in range(n_samples):
            val = random.uniform(-1, 1)
            fade = 1.0 - (i / n_samples)
            buf[i] = int(val * 12000 * fade)
        return pygame.mixer.Sound(buffer=buf)

    def _generate_sweep(self, start_freq, end_freq, duration):
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        buf = array.array('h', [0]) * n_samples
        for i in range(n_samples):
            t = i / sample_rate
            freq = start_freq + (end_freq - start_freq) * (i / n_samples)
            val = math.sin(2 * math.pi * freq * t)
            fade = 1.0 - (i / n_samples)
            buf[i] = int(val * 8000 * fade)
        return pygame.mixer.Sound(buffer=buf)

    def play(self, name):
        if self.available and name in self.sounds:
            try:
                self.sounds[name].play()
            except pygame.error:
                pass