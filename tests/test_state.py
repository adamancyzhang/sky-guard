"""Tests for GameState state machine."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game.state import GameState


def test_initial_state_is_menu():
    s = GameState()
    assert s.current == GameState.MENU


def test_is_menu():
    s = GameState()
    assert s.is_menu()
    s.set(GameState.PLAYING)
    assert not s.is_menu()


def test_is_playing():
    s = GameState()
    assert not s.is_playing()
    s.set(GameState.PLAYING)
    assert s.is_playing()


def test_is_playing_network():
    s = GameState()
    s.set(GameState.NETWORK_PLAYING)
    assert s.is_playing()


def test_is_game_over():
    s = GameState()
    assert not s.is_game_over()
    s.set(GameState.GAME_OVER)
    assert s.is_game_over()


def test_is_help():
    s = GameState()
    s.set(GameState.HELP)
    assert s.is_help()


def test_is_network_state():
    s = GameState()
    assert not s.is_network_state()
    s.set(GameState.LOBBY)
    assert s.is_network_state()
    s.set(GameState.ROOM)
    assert s.is_network_state()
    s.set(GameState.NETWORK_MENU)
    assert s.is_network_state()


def test_set_changes_state():
    s = GameState()
    s.set(GameState.HELP)
    assert s.current == GameState.HELP
    s.set(GameState.GAME_OVER)
    assert s.current == GameState.GAME_OVER


def test_not_transitioning_by_default():
    s = GameState()
    assert s.transitioning is False
    assert s.transition_timer == 0


def test_constants_are_unique():
    values = [
        GameState.MENU,
        GameState.PLAYING,
        GameState.GAME_OVER,
        GameState.HELP,
        GameState.NETWORK_MENU,
        GameState.CONNECTING,
        GameState.LOBBY,
        GameState.MATCHMAKING,
        GameState.ROOM,
        GameState.NETWORK_COUNTDOWN,
        GameState.NETWORK_PLAYING,
        GameState.NETWORK_GAME_OVER,
    ]
    assert len(values) == len(set(values)), "GameState constants must be unique"
