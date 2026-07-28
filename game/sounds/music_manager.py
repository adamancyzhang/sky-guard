# game/sounds/music_manager.py
import array
import math
import random

import pygame

SAMPLE_RATE = 22050


def _make_sound(samples, volume=0.5):
    """Convert a list of float samples (-1..1) to a pygame Sound."""
    max_amp = 32767 * min(volume, 1.0)
    buf = array.array('h', [
        int(max(-1, min(1, s)) * max_amp)
        for s in samples
    ])
    return pygame.mixer.Sound(buffer=buf)


def generate_menu_bgm(volume=0.5):
    """Slow ambient pad: overlapping sine waves in Cmaj7 (C E G B)."""
    duration = 8.0
    n = int(SAMPLE_RATE * duration)
    samples = [0.0] * n
    freqs = [261.63, 329.63, 392.00, 493.88]
    amplitudes = [0.12, 0.10, 0.08, 0.06]
    for freq, amp in zip(freqs, amplitudes):
        for i in range(n):
            t = i / SAMPLE_RATE
            mod = 1 + 0.005 * math.sin(2 * math.pi * 0.5 * t)
            samples[i] += amp * math.sin(2 * math.pi * freq * mod * t)
    for i in range(n):
        t = i / SAMPLE_RATE
        samples[i] += 0.05 * math.sin(2 * math.pi * 65.41 * t)
    fade_n = int(SAMPLE_RATE * 0.5)
    for i in range(fade_n):
        env = i / fade_n
        samples[i] *= env
        samples[n - 1 - i] *= env
    return _make_sound(samples, volume)


def generate_play_bgm(volume=0.5):
    """Action BGM: pulse bass + arpeggiated chords."""
    duration = 8.0
    n = int(SAMPLE_RATE * duration)
    samples = [0.0] * n
    bpm = 120
    beat_len = 60.0 / bpm
    bass_freqs = [65.41, 98.00, 110.00, 87.31]
    for i in range(n):
        t = i / SAMPLE_RATE
        beat_idx = int(t / beat_len) % len(bass_freqs)
        beat_t = (t % beat_len) / beat_len
        env = max(0, 1 - beat_t * 4) * 0.3
        freq = bass_freqs[beat_idx]
        samples[i] += env * math.sin(2 * math.pi * freq * t)
    arp_freqs = [523.25, 659.25, 783.99]
    eighth = beat_len / 2
    for i in range(n):
        t = i / SAMPLE_RATE
        arp_idx = int(t / eighth) % len(arp_freqs)
        arp_t = (t % eighth) / eighth
        env = max(0, 1 - arp_t * 2) * 0.08
        freq = arp_freqs[arp_idx]
        samples[i] += env * math.sin(2 * math.pi * freq * t)
    for i in range(n):
        t = i / SAMPLE_RATE
        beat_t = (t % beat_len) / beat_len
        if 0.4 < beat_t < 0.6:
            noise = random.uniform(-1, 1) * 0.06
            samples[i] += noise
    fade_n = int(SAMPLE_RATE * 0.3)
    for i in range(fade_n):
        env = i / fade_n
        samples[i] *= env
        samples[n - 1 - i] *= env
    return _make_sound(samples, volume)


def generate_boss_bgm(volume=0.5):
    """Intense boss theme: fast pulse + distorted saw bass + noise hi-hat."""
    duration = 8.0
    n = int(SAMPLE_RATE * duration)
    samples = [0.0] * n
    bpm = 140
    beat_len = 60.0 / bpm
    bass_freqs = [65.41, 77.78, 65.41, 92.50]
    for i in range(n):
        t = i / SAMPLE_RATE
        beat_idx = int(t / beat_len) % len(bass_freqs)
        beat_t = (t % beat_len) / beat_len
        env = max(0, 0.5 - beat_t * 2)
        freq = bass_freqs[beat_idx]
        phase = (freq * t) % 1.0
        saw = 2.0 * phase - 1.0
        samples[i] += env * saw * 0.15
    sixteenth = beat_len / 4
    for i in range(n):
        t = i / SAMPLE_RATE
        sixteenth_t = (t % sixteenth) / sixteenth
        if sixteenth_t < 0.15:
            noise = random.uniform(-1, 1)
            env = max(0, 1 - sixteenth_t * 6) * 0.08
            samples[i] += noise * env
    for i in range(n):
        t = i / SAMPLE_RATE
        samples[i] += 0.04 * math.sin(2 * math.pi * 55 * t)
        samples[i] += 0.03 * math.sin(2 * math.pi * 82.5 * t)
    fade_n = int(SAMPLE_RATE * 0.3)
    for i in range(fade_n):
        env = i / fade_n
        samples[i] *= env
        samples[n - 1 - i] *= env
    return _make_sound(samples, volume)


class MusicManager:
    """Manages BGM: generates tracks, handles transitions, volume control."""

    TRACK_MENU = "menu"
    TRACK_PLAY = "play"
    TRACK_BOSS = "boss"

    def __init__(self, volume=0.5, muted=False):
        self.volume = volume
        self.muted = muted
        self.current_track = None
        self._tracks = {}

    def _ensure_track(self, track_id: str):
        if track_id not in self._tracks:
            if track_id == self.TRACK_MENU:
                self._tracks[track_id] = generate_menu_bgm(self.volume)
            elif track_id == self.TRACK_PLAY:
                self._tracks[track_id] = generate_play_bgm(self.volume)
            elif track_id == self.TRACK_BOSS:
                self._tracks[track_id] = generate_boss_bgm(self.volume)

    def play(self, track_id: str, force=False):
        """Start playing a track. No-op if already playing (unless force=True)."""
        if self.muted:
            self.current_track = None
            return
        if track_id == self.current_track and not force:
            return
        self._ensure_track(track_id)
        sound = self._tracks.get(track_id)
        if sound:
            sound.set_volume(self.volume)
            sound.play(loops=-1)
            self.current_track = track_id

    def stop(self):
        for s in self._tracks.values():
            s.stop()
        self.current_track = None

    def set_volume(self, vol: float):
        self.volume = max(0.0, min(1.0, vol))
        if self.current_track and self.current_track in self._tracks:
            self._tracks[self.current_track].set_volume(self.volume)

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self.stop()
        return self.muted

    def set_muted(self, muted: bool):
        self.muted = muted
        if self.muted:
            self.stop()
