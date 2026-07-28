"""Tests for the pause system — toggle, menu, resume, and quit behavior."""
import sys
import os

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame
from game.state import GameState


def _make_game():
    """Create a minimal Game instance inside a dummy video driver."""
    from main import Game

    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    pygame.display.init()
    pygame.font.init()
    pygame.mixer.init(frequency=22050, size=-16, channels=1)

    g = Game()
    # Reset to known state
    g.state.set(GameState.PLAYING)
    g.pause_selection = 0
    return g


# ── State machine helpers ───────────────────────────────────────────────

def make_keydown(key):
    """Create a KEYDOWN event for the given pygame key constant."""
    e = pygame.event.Event(pygame.KEYDOWN, {"key": key})
    return e


# ════════════════════════════════════════════════════════════════════════
# 1. Pause toggle
# ════════════════════════════════════════════════════════════════════════

def test_escape_pauses_game():
    """Pressing Esc during PLAYING transitions to PAUSED."""
    g = _make_game()
    g.state.set(GameState.PLAYING)
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))
    assert g.state.is_paused(), "Expected PAUSED after Esc"


def test_p_key_pauses_game():
    """Pressing P key during PLAYING transitions to PAUSED."""
    g = _make_game()
    g.state.set(GameState.PLAYING)
    g._handle_single_playing_key(make_keydown(pygame.K_p))
    assert g.state.is_paused(), "Expected PAUSED after P"


def test_escape_resumes_game():
    """Pressing Esc while PAUSED transitions back to PLAYING."""
    g = _make_game()
    g.state.set(GameState.PLAYING)
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))  # pause
    assert g.state.is_paused()
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))  # resume
    assert g.state.is_playing(), "Expected PLAYING after Esc resume"


def test_p_key_resumes_game():
    """Pressing P while PAUSED transitions back to PLAYING."""
    g = _make_game()
    g.state.set(GameState.PLAYING)
    g._handle_single_playing_key(make_keydown(pygame.K_p))  # pause
    assert g.state.is_paused()
    g._handle_single_playing_key(make_keydown(pygame.K_p))  # resume
    assert g.state.is_playing(), "Expected PLAYING after P resume"


def test_pause_selection_resets_on_pause():
    """pause_selection resets to 0 when entering pause."""
    g = _make_game()
    g.state.set(GameState.PLAYING)
    g.pause_selection = 1  # simulate previous selection
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))
    assert g.pause_selection == 0, "pause_selection should reset to 0 on pause"


def test_pause_selection_resets_on_resume():
    """pause_selection resets to 0 when resuming from pause."""
    g = _make_game()
    g.state.set(GameState.PLAYING)
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))
    g.pause_selection = 1
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))
    assert g.pause_selection == 0, "pause_selection should reset to 0 on resume"


# ════════════════════════════════════════════════════════════════════════
# 2. Pause menu navigation
# ════════════════════════════════════════════════════════════════════════

def test_pause_menu_down_selects_quit():
    """Down arrow selects the quit option (index 1)."""
    g = _make_game()
    g.state.set(GameState.PLAYING)
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))  # pause
    g._handle_single_playing_key(make_keydown(pygame.K_DOWN))
    assert g.pause_selection == 1, "Expected quit option selected"


def test_pause_menu_up_wraps_to_quit():
    """Up arrow from index 0 wraps to quit (index 1)."""
    g = _make_game()
    g.state.set(GameState.PLAYING)
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))  # pause
    g._handle_single_playing_key(make_keydown(pygame.K_UP))
    assert g.pause_selection == 1, "Expected wrap to quit"


def test_pause_menu_up_from_quit_goes_to_resume():
    """Up arrow from quit option goes back to resume."""
    g = _make_game()
    g.state.set(GameState.PLAYING)
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))  # pause
    g._handle_single_playing_key(make_keydown(pygame.K_DOWN))    # to quit
    g._handle_single_playing_key(make_keydown(pygame.K_UP))      # back to resume
    assert g.pause_selection == 0, "Expected resume (index 0)"


def test_pause_menu_down_wraps_to_resume():
    """Down arrow from quit wraps back to resume."""
    g = _make_game()
    g.state.set(GameState.PLAYING)
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))  # pause
    g._handle_single_playing_key(make_keydown(pygame.K_DOWN))    # to quit
    g._handle_single_playing_key(make_keydown(pygame.K_DOWN))    # wrap to resume
    assert g.pause_selection == 0, "Expected wrap to resume (index 0)"


def test_pause_menu_wsd_navigation():
    """W/S keys also navigate the pause menu."""
    g = _make_game()
    g.state.set(GameState.PLAYING)
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))
    g._handle_single_playing_key(make_keydown(pygame.K_s))  # down
    assert g.pause_selection == 1, "S key should move to quit"
    g._handle_single_playing_key(make_keydown(pygame.K_w))  # up
    assert g.pause_selection == 0, "W key should move back to resume"


# ════════════════════════════════════════════════════════════════════════
# 3. Resume
# ════════════════════════════════════════════════════════════════════════

def test_resume_enter_key():
    """Pressing Enter on RESUME transitions back to PLAYING."""
    g = _make_game()
    g.state.set(GameState.PLAYING)
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))
    assert g.state.is_paused()
    # Enter on RESUME (index 0, default)
    g._handle_single_playing_key(make_keydown(pygame.K_RETURN))
    assert g.state.is_playing(), "Expected PLAYING after resume"


def test_resume_selection_stays_zero():
    """After resume, pause_selection is 0."""
    g = _make_game()
    g.state.set(GameState.PLAYING)
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))
    g._handle_single_playing_key(make_keydown(pygame.K_DOWN))  # move to quit
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))  # toggle resume
    assert g.pause_selection == 0, "Resume should reset selection to 0"


# ════════════════════════════════════════════════════════════════════════
# 4. Quit to menu
# ════════════════════════════════════════════════════════════════════════

def test_quit_to_menu_enter_key():
    """Pressing Enter on QUIT transitions to MENU."""
    g = _make_game()
    g.state.set(GameState.PLAYING)
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))  # pause
    g._handle_single_playing_key(make_keydown(pygame.K_DOWN))     # to quit
    g._handle_single_playing_key(make_keydown(pygame.K_RETURN))   # confirm quit
    assert g.state.is_menu(), "Expected MENU after quit to menu"


def test_quit_to_menu_running():
    """Quit to menu does not stop the game loop."""
    g = _make_game()
    assert g.running
    g.state.set(GameState.PLAYING)
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))  # pause
    g._handle_single_playing_key(make_keydown(pygame.K_DOWN))
    g._handle_single_playing_key(make_keydown(pygame.K_RETURN))  # quit
    assert g.running, "Game should still be running after quit to menu"


def test_quit_to_menu_clears_sprites():
    """Quit to menu empties all sprite groups."""
    g = _make_game()
    g.state.set(GameState.PLAYING)

    # Add some sprites to simulate active game
    s = pygame.sprite.Sprite()
    g.enemies_group.add(s)
    assert len(g.enemies_group) > 0

    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))  # pause
    g._handle_single_playing_key(make_keydown(pygame.K_DOWN))
    g._handle_single_playing_key(make_keydown(pygame.K_RETURN))  # quit

    assert len(g.enemies_group) == 0, "Enemies should be cleared on quit"
    assert len(g.bullets_group) == 0, "Bullets should be cleared on quit"
    assert len(g.powerups_group) == 0, "Powerups should be cleared on quit"


# ════════════════════════════════════════════════════════════════════════
# 5. Game freeze while paused
# ════════════════════════════════════════════════════════════════════════

def test_update_skipped_when_paused():
    """update() returns immediately when paused — no game progress."""
    g = _make_game()
    g.state.set(GameState.PLAYING)
    start_score = g.player.score
    g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))
    g.update()  # should be a no-op
    assert g.player.score == start_score, "Score should not change while paused"


def test_pause_can_alternate():
    """Multiple pause/resume cycles work correctly."""
    g = _make_game()
    for i in range(5):
        g.state.set(GameState.PLAYING)
        g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))
        assert g.state.is_paused(), f"Cycle {i}: should pause"
        g._handle_single_playing_key(make_keydown(pygame.K_ESCAPE))
        assert g.state.is_playing(), f"Cycle {i}: should resume"


# ════════════════════════════════════════════════════════════════════════
# 6. PAUSED state is a valid GameState constant
# ════════════════════════════════════════════════════════════════════════

def test_paused_is_valid_state():
    """PAUSED must be a non-empty string."""
    assert isinstance(GameState.PAUSED, str)
    assert len(GameState.PAUSED) > 0


def test_is_paused_method():
    """is_paused() returns True only when current is PAUSED."""
    g = _make_game()
    g.state.current = GameState.PAUSED
    assert g.state.is_paused()
    g.state.current = GameState.PLAYING
    assert not g.state.is_paused()
    g.state.current = GameState.MENU
    assert not g.state.is_paused()


def test_is_playing_excludes_paused():
    """is_playing() returns False when paused."""
    g = _make_game()
    g.state.current = GameState.PAUSED
    assert not g.state.is_playing(), "PAUSED should not count as playing"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
