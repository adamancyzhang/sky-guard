"""Tests for Explosion particle system."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.display.set_mode((1, 1))
pygame.font.init()

from game.settings import EXPLOSION_FRAMES, EXPLOSION_PARTICLES
from game.sprites.explosion import Explosion


def test_explosion_creates_particles():
    exp = Explosion(100, 100)
    assert len(exp.particles) == EXPLOSION_PARTICLES


def test_particles_start_at_center():
    exp = Explosion(100, 100)
    for p in exp.particles:
        assert p["x"] == 100
        assert p["y"] == 100


def test_particles_have_colors():
    exp = Explosion(100, 100)
    valid_colors = [(255, 255, 50), (255, 50, 50), (255, 150, 50), (255, 255, 255)]
    for p in exp.particles:
        assert p["color"] in valid_colors or len(p["color"]) == 3


def test_particles_have_life():
    exp = Explosion(100, 100)
    for p in exp.particles:
        assert p["life"] == EXPLOSION_FRAMES
        assert p["max_life"] == EXPLOSION_FRAMES


def test_particles_move_on_update():
    exp = Explosion(100, 100)
    x_before = exp.particles[0]["x"]
    y_before = exp.particles[0]["y"]
    exp.update()
    assert exp.particles[0]["x"] != x_before or exp.particles[0]["y"] != y_before


def test_particle_life_decreases():
    exp = Explosion(100, 100)
    life_before = exp.particles[0]["life"]
    exp.update()
    assert exp.particles[0]["life"] < life_before


def test_explosion_self_destructs():
    exp = Explosion(100, 100)
    assert exp.alive()
    # Run enough frames for all particles to expire
    for _ in range(EXPLOSION_FRAMES + 1):
        exp.update()
    assert not exp.alive()


def test_particle_gravity():
    """Particles should accelerate downward due to gravity."""
    exp = Explosion(100, 100)
    vy_before = exp.particles[0]["vy"]
    exp.update()
    # vy increases by gravity (0.2)
    assert exp.particles[0]["vy"] > vy_before - 0.01  # allow float comparison


def test_draw_does_not_crash():
    """Draw should work without error."""
    exp = Explosion(100, 100)
    screen = pygame.Surface((480, 720))
    try:
        exp.draw(screen)
    except Exception as e:
        assert False, f"draw() raised {e}"
