"""Tests for Player: movement, invincibility, powerups, hit/reset mechanics."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.set_mode((1, 1))
pygame.font.init()

from game.settings import PLAYER_SPEED, PLAYER_MAX_LIVES, PLAYER_INVINCIBLE_FRAMES, SCREEN_WIDTH, SCREEN_HEIGHT
from game.sprites.player import Player


# ── Movement ──

def test_player_initial_position():
    p = Player()
    assert p.rect.centerx == SCREEN_WIDTH // 2
    assert p.rect.bottom == SCREEN_HEIGHT - 30


def test_player_moves_left():
    p = Player()
    x_before = p.rect.x
    dummy_keys = {pygame.K_LEFT: 1, pygame.K_RIGHT: 0, pygame.K_UP: 0, pygame.K_DOWN: 0,
                  pygame.K_a: 0, pygame.K_d: 0, pygame.K_w: 0, pygame.K_s: 0}
    # wrap in a dict-like object
    class KeyDict(dict):
        def __getitem__(self, key):
            return self.get(key, 0)
    keys = KeyDict({pygame.K_LEFT: 1, pygame.K_RIGHT: 0, pygame.K_UP: 0, pygame.K_DOWN: 0,
                    pygame.K_a: 0, pygame.K_d: 0, pygame.K_w: 0, pygame.K_s: 0})
    p.update(keys)
    assert p.rect.x < x_before


def test_player_moves_right():
    p = Player()
    x_before = p.rect.x
    class KeyDict(dict):
        def __getitem__(self, key):
            return self.get(key, 0)
    keys = KeyDict({pygame.K_LEFT: 0, pygame.K_RIGHT: 1, pygame.K_UP: 0, pygame.K_DOWN: 0,
                    pygame.K_a: 0, pygame.K_d: 0, pygame.K_w: 0, pygame.K_s: 0})
    p.update(keys)
    assert p.rect.x > x_before


def test_player_clamped_to_screen():
    p = Player()
    class KeyDict(dict):
        def __getitem__(self, key):
            return self.get(key, 0)
    # Force movement far left
    p.rect.x = -100
    p.update(KeyDict())
    assert p.rect.x >= 0

    # Force movement far right
    p.rect.x = SCREEN_WIDTH + 100
    p.update(KeyDict())
    assert p.rect.right <= SCREEN_WIDTH


# ── Lives ──

def test_player_starts_with_max_lives():
    p = Player()
    assert p.lives == PLAYER_MAX_LIVES


def test_hit_reduces_lives():
    p = Player()
    p.lives = 2
    p.invincible_timer = 0
    p.hit()
    assert p.lives == 1


def test_hit_invincible_blocks():
    p = Player()
    p.lives = 2
    p.invincible_timer = 10
    result = p.hit()
    assert result is False
    assert p.lives == 2  # not reduced


def test_invincibility_after_hit():
    p = Player()
    p.lives = 2
    p.invincible_timer = 0
    p.hit()
    assert p.invincible_timer == PLAYER_INVINCIBLE_FRAMES


def test_invincibility_decays():
    p = Player()
    p.invincible_timer = 10
    p.update({})
    assert p.invincible_timer == 9


def test_death_when_lives_zero():
    p = Player()
    p.lives = 1
    p.invincible_timer = 0
    p.hit()
    assert p.lives == 0


# ── Powerups ──

def test_apply_shield():
    p = Player()
    p.apply_powerup("shield")
    assert p.has_powerup("shield")


def test_apply_rapid():
    p = Player()
    p.apply_powerup("rapid")
    assert p.has_powerup("rapid")


def test_apply_triple():
    p = Player()
    p.apply_powerup("triple")
    assert p.has_powerup("triple")


def test_apply_speed():
    p = Player()
    p.apply_powerup("speed")
    assert p.has_powerup("speed")


def test_apply_bomb():
    """Bomb power-up is no-op on the player (handled externally)."""
    p = Player()
    p.apply_powerup("bomb")
    # No state change on player
    assert not p.has_powerup("bomb")


def test_apply_life():
    p = Player()
    p.lives = 1
    p.apply_powerup("life")
    assert p.lives == 2


def test_life_capped_at_max():
    p = Player()
    p.apply_powerup("life")  # already at max
    assert p.lives == PLAYER_MAX_LIVES


def test_apply_unknown_powerup():
    p = Player()
    p.apply_powerup("unknown_type")
    # Should not crash, no state change


def test_powerup_timer_decays():
    p = Player()
    p.apply_powerup("shield")
    assert p.has_powerup("shield")
    # Simulate decay past duration
    from game.settings import POWERUP_TYPES
    duration = POWERUP_TYPES["shield"]["duration"]
    p.active_powerups["shield"] = 1
    p.update({})
    assert not p.has_powerup("shield")


def test_hit_downgrades_weapon():
    p = Player()
    p.upgrade_weapon("normal")
    p.upgrade_weapon("normal")
    assert p.get_weapon_level("normal") == 3
    p.lives = 2
    p.invincible_timer = 0
    p.hit()
    assert p.get_weapon_level("normal") == 2


def test_hit_resets_combo():
    p = Player()
    p.register_kill()
    p.register_kill()
    assert p.combo_count > 0
    p.lives = 2
    p.invincible_timer = 0
    p.hit()
    assert p.combo_count == 0


# ── Reset ──

def test_reset_restores_position():
    p = Player()
    p.rect.centerx = 10
    p.rect.bottom = 10
    p.reset()
    assert p.rect.centerx == SCREEN_WIDTH // 2
    assert p.rect.bottom == SCREEN_HEIGHT - 30


def test_reset_restores_lives():
    p = Player()
    p.lives = 1
    p.reset()
    assert p.lives == PLAYER_MAX_LIVES


def test_reset_clears_powerups():
    p = Player()
    p.apply_powerup("shield")
    p.reset()
    assert not p.has_powerup("shield")


def test_reset_preserves_weapon_levels():
    p = Player()
    p.upgrade_weapon("normal")
    p.upgrade_weapon("normal")
    p.reset()
    assert p.get_weapon_level("normal") == 3


def test_reset_preserves_options():
    p = Player()
    p.add_option()
    p.reset()
    assert len(p.options) == 1


def test_destroy_clears_options():
    p = Player()
    p.add_option()
    p.destroy()
    assert len(p.options) == 0


# ── Shoot cooldown ──

def test_can_shoot_initial():
    p = Player()
    assert p.can_shoot()


def test_shoot_sets_cooldown():
    from game.settings import PLAYER_SHOOT_COOLDOWN
    p = Player()
    p.shoot()
    assert p.shoot_cooldown == PLAYER_SHOOT_COOLDOWN
    assert not p.can_shoot()


def test_cooldown_decays():
    p = Player()
    p.shoot()
    for _ in range(20):
        p.update({})
    assert p.can_shoot()
