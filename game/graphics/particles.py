# game/graphics/particles.py
import math
import random

import pygame

from game.settings import *

# ── Shape constants ──
SHAPE_CIRCLE = "circle"
SHAPE_SQUARE = "square"
SHAPE_DIAMOND = "diamond"


class Particle:
    __slots__ = (
        "_combo_tier",
        "_score_text",
        "age",
        "alpha",
        "color",
        "friction",
        "gravity",
        "lifetime",
        "shape",
        "size",
        "vx",
        "vy",
        "x",
        "y",
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.x = 0
        self.y = 0
        self.vx = 0
        self.vy = 0
        self.color = (255, 255, 255)
        self.size = 2
        self.alpha = 255
        self.lifetime = 20
        self.age = 0
        self.shape = SHAPE_CIRCLE
        self.gravity = 0
        self.friction = 0.98
        self._score_text = None
        self._combo_tier = 0

    @property
    def dead(self):
        return self.age >= self.lifetime or self.alpha <= 0

    def update(self):
        self.age += 1
        self.vx *= self.friction
        self.vy *= self.friction
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        # Fade out over lifetime
        t = self.age / max(self.lifetime, 1)
        self.alpha = max(0, int(255 * (1 - t)))

    def draw(self, surf):
        if self.alpha <= 0:
            return
        c = self.color
        alpha = min(self.alpha, 255)
        sz = max(1, int(self.size))
        if alpha < 255:
            s = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
        else:
            s = surf
        if self.shape == SHAPE_CIRCLE:
            if alpha < 255:
                pygame.draw.circle(s, (c[0], c[1], c[2], alpha), (sz, sz), sz)
                surf.blit(s, (self.x - sz, self.y - sz), special_flags=pygame.BLEND_ALPHA_SDL2)
            else:
                pygame.draw.circle(surf, c, (int(self.x), int(self.y)), sz)
        elif self.shape == SHAPE_SQUARE:
            r = pygame.Rect(int(self.x - sz / 2), int(self.y - sz / 2), sz, sz)
            if alpha < 255:
                pygame.draw.rect(s, (c[0], c[1], c[2], alpha), r)
                surf.blit(s, (self.x - sz / 2, self.y - sz / 2),
                          special_flags=pygame.BLEND_ALPHA_SDL2)
            else:
                pygame.draw.rect(surf, c, r)
        elif self.shape == SHAPE_DIAMOND:
            pts = [
                (int(self.x), int(self.y - sz)),
                (int(self.x + sz), int(self.y)),
                (int(self.x), int(self.y + sz)),
                (int(self.x - sz), int(self.y)),
            ]
            if alpha < 255:
                pygame.draw.polygon(s, (c[0], c[1], c[2], alpha), pts)
                surf.blit(s, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
            else:
                pygame.draw.polygon(surf, c, pts)


class ParticleManager:
    def __init__(self, max_particles=PARTICLE_POOL_SIZE):
        self.pool = [Particle() for _ in range(max_particles)]

    def emit(self, x, y, count=5, **kwargs):
        """Spawn `count` particles at (x, y) with optional overrides.

        kwargs can set: vx, vy, color, size, lifetime, shape, gravity, friction
        Each numeric value can be a tuple (min, max) for random range, or a single float/int.
        color can be a tuple (r, g, b) or a list of tuples to pick from.
        """
        spawned = 0
        for p in self.pool:
            if p.dead:
                p.reset()
                p.x = x
                p.y = y
                for key in ("vx", "vy", "size", "lifetime", "gravity", "friction", "alpha"):
                    val = kwargs.get(key)
                    if val is not None:
                        if isinstance(val, (list, tuple)):
                            if len(val) == 2 and all(isinstance(v, (int, float)) for v in val):
                                setattr(p, key, random.uniform(val[0], val[1]))
                            else:
                                setattr(p, key, random.choice(val))
                        else:
                            setattr(p, key, val)
                # Color handling
                clr = kwargs.get("color", (255, 255, 255))
                if isinstance(clr, list):
                    p.color = random.choice(clr)
                else:
                    p.color = clr
                # Shape
                p.shape = kwargs.get("shape", SHAPE_CIRCLE)
                spawned += 1
                if spawned >= count:
                    break
        return spawned

    def update(self):
        for p in self.pool:
            if not p.dead:
                p.update()

    def draw(self, surf):
        for p in self.pool:
            if not p.dead:
                p.draw(surf)


# ── Helper functions (convenience wrappers) ──

def spawn_muzzle_flash(pm: ParticleManager, x, y):
    """3-5 warm sparks from the gun tip."""
    pm.emit(x, y, count=random.randint(3, 5),
            vx=(-1.5, 1.5), vy=(-3.0, -0.5),
            color=SPARK_COLOR_PLAYER,
            size=(1, 3), lifetime=(4, 8), shape=SHAPE_SQUARE,
            friction=0.85)


def spawn_enemy_death(pm: ParticleManager, x, y, color=None):
    """6-12 colored fragments on enemy kill."""
    if color is None:
        color = (255, 100, 50)
    pm.emit(x, y, count=random.randint(6, 12),
            vx=(-4, 4), vy=(-4, 4),
            color=color,
            size=(2, 5), lifetime=(10, 25), shape=SHAPE_DIAMOND,
            friction=0.90, gravity=0.05)


def spawn_score_popup(pm: ParticleManager, x, y, score_text="+10",
                      color=(255, 255, 255)):
    """Floating score text that drifts upward and fades.
    Uses a single particle with size==0 as a text marker — the HUD renders
    the text overlay from this marker data.
    """
    for p in pm.pool:
        if p.dead:
            p.reset()
            p.x = x
            p.y = y
            p.vy = -SCORE_POPUP_SPEED
            p.color = color
            p.size = 0  # sentinel: text marker
            p.lifetime = SCORE_POPUP_LIFETIME
            p.alpha = 255
            p._score_text = score_text
            break


def spawn_engine_trail(pm: ParticleManager, x, y):
    """One blue-white trail particle from the engine."""
    pm.emit(x, y, count=1,
            vx=(-0.5, 0.5), vy=(1.0, 2.5),
            color=[(100, 180, 255), (50, 80, 200), (150, 200, 255)],
            size=(2, 4), lifetime=(15, 30), shape=SHAPE_CIRCLE,
            friction=0.92)


def spawn_boss_hit(pm: ParticleManager, x, y):
    """8-12 red sparks on boss hit."""
    pm.emit(x, y, count=random.randint(8, 12),
            vx=(-5, 5), vy=(-5, 5),
            color=SPARK_COLOR_BOSS,
            size=(2, 6), lifetime=(8, 20), shape=SHAPE_CIRCLE,
            friction=0.88, gravity=0.02)


def spawn_pickup_ring(pm: ParticleManager, x, y):
    """Ring of 8 gold glow particles expanding outward."""
    for i in range(8):
        angle = (2 * math.pi / 8) * i
        speed = random.uniform(1.5, 3.0)
        pm.emit(x, y, count=1,
                vx=(math.cos(angle) * speed, math.cos(angle) * speed),
                vy=(math.sin(angle) * speed, math.sin(angle) * speed),
                color=SPARK_COLOR_PICKUP,
                size=(3, 5), lifetime=(15, 25), shape=SHAPE_CIRCLE,
                friction=0.90)


def spawn_menu_stars(pm: ParticleManager, width, height, count=30):
    """Pre-populate menu background with floating stars."""
    for _ in range(count):
        pm.emit(random.randint(0, width), random.randint(0, height),
                count=1,
                vx=(-0.2, 0.2), vy=(-0.3, -0.05),
                color=[(200, 200, 255), (255, 200, 200), (200, 255, 200),
                       (255, 255, 200), (200, 255, 255)],
                size=(1, 3), lifetime=9999, shape=SHAPE_CIRCLE,
                friction=1.0, alpha=(80, 200))


def spawn_boss_phase_pulse(pm: ParticleManager, x, y, color=None):
    """Expanding ring pulse for boss phase transition."""
    if color is None:
        color = (255, 200, 50)
    for i in range(16):
        angle = (2 * math.pi / 16) * i
        speed = random.uniform(2, 4)
        pm.emit(x, y, count=1,
                vx=(math.cos(angle) * speed, math.cos(angle) * speed),
                vy=(math.sin(angle) * speed, math.sin(angle) * speed),
                color=color,
                size=(3, 6), lifetime=(20, 35), shape=SHAPE_CIRCLE,
                friction=0.95)
