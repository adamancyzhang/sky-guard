# game/graphics/background.py
import pygame
import random
from game.settings import SCREEN_WIDTH, SCREEN_HEIGHT, BACKGROUND_LAYERS


def generate_layer_surface(layer_config):
    """Generate a pixel-art scrolling surface for a background layer.

    Each layer is a solid-colored surface with procedurally drawn
    silhouette shapes (mountains, buildings, etc.) based on the layer name.
    """
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    color = layer_config["color"]
    name = layer_config["name"]

    if name == "sky":
        # Deep space — draw faint stars
        for _ in range(40):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            r = random.randint(1, 2)
            bright = random.randint(30, 80)
            pygame.draw.circle(surf, (bright, bright, bright + 20), (x, y), r)

    elif name == "mountains":
        # Procedural mountain silhouette
        points = [(0, SCREEN_HEIGHT)]
        for x in range(0, SCREEN_WIDTH + 10, 10):
            h = SCREEN_HEIGHT - random.randint(40, 120)
            points.append((x, h))
        points.append((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.draw.polygon(surf, color, points)

    elif name == "city":
        # City skyline — random rectangles
        x = 0
        while x < SCREEN_WIDTH:
            w = random.randint(20, 60)
            h = random.randint(60, 180)
            y = SCREEN_HEIGHT - h
            pygame.draw.rect(surf, color, (x, y, w, h))
            # Window lights
            for wx in range(x + 4, x + w - 4, 10):
                for wy in range(y + 4, y + h - 4, 12):
                    if random.random() < 0.3:
                        pygame.draw.rect(surf, (60, 60, 30), (wx, wy, 4, 6))
            x += w + random.randint(5, 15)

    elif name == "ground":
        # Ground silhouette with slight texture
        points = [(0, SCREEN_HEIGHT)]
        for x in range(0, SCREEN_WIDTH + 10, 10):
            h = SCREEN_HEIGHT - random.randint(10, 30)
            points.append((x, h))
        points.append((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.draw.polygon(surf, color, points)

    return surf


class ScrollingBackground:
    """Manages multiple parallax scrolling background layers."""

    def __init__(self):
        self.layers = []
        for cfg in BACKGROUND_LAYERS:
            surf = generate_layer_surface(cfg)
            self.layers.append({
                "surface": surf,
                "speed": cfg["speed"],
                "y_offset": 0.0,
            })

    def update(self):
        """Scroll each layer downward at its own speed."""
        for layer in self.layers:
            layer["y_offset"] += layer["speed"]
            # Wrap when a full screen has passed
            if layer["y_offset"] >= SCREEN_HEIGHT:
                layer["y_offset"] -= SCREEN_HEIGHT

    def draw(self, screen):
        """Draw all layers in order (back to front)."""
        for layer in self.layers:
            y_int = int(layer["y_offset"])
            screen.blit(layer["surface"], (0, y_int))
            # Tile the wrapping slice above/below
            if y_int > 0:
                screen.blit(layer["surface"], (0, y_int - SCREEN_HEIGHT))
            else:
                screen.blit(layer["surface"], (0, y_int + SCREEN_HEIGHT))