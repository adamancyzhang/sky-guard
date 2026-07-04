# game/sprites/explosion.py
import pygame
import random
import math
from game.settings import *


class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(*groups)
        self.particles = []
        for _ in range(EXPLOSION_PARTICLES):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 5)
            self.particles.append({
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "size": random.randint(2, 5),
                "color": random.choice([YELLOW, RED, ORANGE, WHITE]),
                "life": EXPLOSION_FRAMES,
                "max_life": EXPLOSION_FRAMES,
            })
        self.frame = 0

    def update(self, *args, **kwargs):
        self.frame += 1
        alive = False
        for p in self.particles:
            if p["life"] > 0:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 0.2  # gravity
                p["life"] -= 1
                p["size"] = max(1, p["size"] - 0.2)
                alive = True
        if not alive:
            self.kill()

    def draw(self, screen):
        for p in self.particles:
            if p["life"] > 0:
                alpha = int(255 * (p["life"] / p["max_life"]))
                size = int(p["size"])
                color = (*p["color"][:3], alpha)
                s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, color, (size, size), size)
                screen.blit(s, (p["x"] - size, p["y"] - size))