# game/graphics/pixel_art.py
import pygame
from game.settings import *

# Pixel art uses 0/1 matrices: "1" = fill color, "0" = transparent
# Each matrix will be scaled to actual sprite size

# Player ship 8x10 pixel matrix
PLAYER_MATRIX = [
    "00011000",
    "00011000",
    "00111100",
    "00111100",
    "01111110",
    "11111111",
    "11111111",
    "01111110",
    "00100100",
    "00100100",
]

# Basic enemy 8x8 pixel matrix
BASIC_ENEMY_MATRIX = [
    "00111100",
    "01100110",
    "11111111",
    "11111111",
    "11111111",
    "10011001",
    "01000010",
    "00111100",
]

# Fast enemy 8x6
FAST_ENEMY_MATRIX = [
    "00011000",
    "00111100",
    "01111110",
    "11111111",
    "01111110",
    "00011000",
]

# Tank enemy 10x10
TANK_ENEMY_MATRIX = [
    "0000110000",
    "0001111000",
    "0011111100",
    "1111111111",
    "1111111111",
    "1111111111",
    "1111111111",
    "1001111001",
    "0100110010",
    "0011001100",
]


def scale_matrix(matrix, scale):
    """Scale a pixel matrix to a target size."""
    rows = len(matrix)
    cols = len(matrix[0])
    scaled = []
    for row in matrix:
        scaled_row = ""
        for ch in row:
            scaled_row += ch * scale
        for _ in range(scale):
            scaled.append(scaled_row)
    return scaled


def matrix_to_surface(matrix, color, scale=3):
    """Convert a pixel matrix to a Pygame Surface."""
    scaled = scale_matrix(matrix, scale)
    h = len(scaled)
    w = len(scaled[0])
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(scaled):
        for x, ch in enumerate(row):
            if ch == "1":
                surf.set_at((x, y), color)
    return surf


def create_player_ship(scale=3):
    """Create the player ship Surface."""
    return matrix_to_surface(PLAYER_MATRIX, CYAN, scale)


def create_enemy_surface(enemy_type, scale=3):
    """Create a Surface for a given enemy type."""
    mapping = {
        "basic": (BASIC_ENEMY_MATRIX, RED),
        "fast": (FAST_ENEMY_MATRIX, PURPLE),
        "tank": (TANK_ENEMY_MATRIX, GREEN),
    }
    if enemy_type not in mapping:
        enemy_type = "basic"
    matrix, color = mapping[enemy_type]
    return matrix_to_surface(matrix, color, scale)


def create_boss_surface(scale=3):
    """Create the Boss enemy Surface (larger, menacing)."""
    from game.settings import BOSS_MATRIX, BOSS_COLOR, SCREEN_HEIGHT
    surf = pygame.Surface((16 * scale, 16 * scale), pygame.SRCALPHA)
    for y, row in enumerate(BOSS_MATRIX):
        for x, ch in enumerate(row):
            if ch == "1":
                color = BOSS_COLOR
                # Add some highlights
                if y < 4 and x > 3 and x < 12:
                    color = (255, 100, 255)
                pygame.draw.rect(surf, color, (x * scale, y * scale, scale, scale))
    # Eye glow
    eye_color = (255, 50, 50)
    for ex, ey in [(5 * scale, 6 * scale), (10 * scale, 6 * scale)]:
        pygame.draw.circle(surf, eye_color, (ex + scale // 2, ey + scale // 2), scale)
    return surf


def create_bullet_surface():
    """Create the bullet Surface."""
    surf = pygame.Surface((BULLET_WIDTH, BULLET_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(surf, BULLET_COLOR, (0, 0, BULLET_WIDTH, BULLET_HEIGHT))
    # Add highlight effect
    pygame.draw.rect(surf, WHITE, (1, 1, BULLET_WIDTH - 2, 4))
    return surf


# Power-up icon matrices (8x8 each)
POWERUP_MATRICES = {
    "shield": [
        "01111110",
        "11111111",
        "11111111",
        "11111111",
        "11111111",
        "11111111",
        "11111111",
        "01111110",
    ],
    "rapid": [
        "00100100",
        "00100100",
        "00111100",
        "00011000",
        "00011000",
        "00111100",
        "00100100",
        "00100100",
    ],
    "triple": [
        "00100010",
        "00100010",
        "00111110",
        "00011100",
        "00011100",
        "00111110",
        "00100010",
        "00100010",
    ],
    "bomb": [
        "00011000",
        "00111100",
        "01111110",
        "11111111",
        "11111111",
        "01111110",
        "00111100",
        "00011000",
    ],
    "speed": [
        "00011000",
        "00111000",
        "01111111",
        "00011110",
        "00001100",
        "00011000",
        "00110000",
        "01100000",
    ],
    "life": [
        "01100110",
        "11111111",
        "11111111",
        "11111111",
        "01111110",
        "00111100",
        "00011000",
        "00000000",
    ],
}


def create_powerup_surface(power_type, color, scale=3):
    """Create a Surface for a power-up icon."""
    matrix = POWERUP_MATRICES.get(power_type, POWERUP_MATRICES["shield"])
    return matrix_to_surface(matrix, color, scale)