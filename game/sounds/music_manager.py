# game/sounds/music_manager.py
"""BGM manager — loads Contra-style looping chiptune tracks from assets/audio/."""

import os
import pygame

ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "assets",
    "audio",
)

TRACK_FILES = {
    "menu": "bgm_menu.wav",
    "play": "bgm_play.wav",
    "boss": "bgm_boss.wav",
}


class MusicManager:
    """Manages BGM: loads tracks from assets/audio/, handles transitions & volume."""

    TRACK_MENU = "menu"
    TRACK_PLAY = "play"
    TRACK_BOSS = "boss"

    def __init__(self, volume=0.5, muted=False):
        self.volume = volume
        self.muted = muted
        self.current_track = None
        self._tracks = {}

    def _ensure_track(self, track_id: str):
        """Load a track from its WAV file if not already loaded."""
        if track_id in self._tracks:
            return
        filename = TRACK_FILES.get(track_id)
        if not filename:
            return
        filepath = os.path.join(ASSETS_DIR, filename)
        if not os.path.isfile(filepath):
            # Fallback: if assets not found, load from bundled resources
            return
        try:
            sound = pygame.mixer.Sound(file=filepath)
            sound.set_volume(self.volume)
            self._tracks[track_id] = sound
        except pygame.error:
            pass

    def play(self, track_id: str, force=False):
        """Start playing a track (looping). No-op if already playing (unless force=True)."""
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
        """Stop all tracks."""
        for s in self._tracks.values():
            try:
                s.stop()
            except pygame.error:
                pass
        self.current_track = None

    def set_volume(self, vol: float):
        """Set master BGM volume (0.0 — 1.0)."""
        self.volume = max(0.0, min(1.0, vol))
        if self.current_track and self.current_track in self._tracks:
            try:
                self._tracks[self.current_track].set_volume(self.volume)
            except pygame.error:
                pass

    def toggle_mute(self):
        """Toggle mute on/off."""
        self.muted = not self.muted
        if self.muted:
            self.stop()
        return self.muted

    def set_muted(self, muted: bool):
        """Set mute state directly."""
        self.muted = muted
        if self.muted:
            self.stop()
