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
    "power": [
        "01111110",
        "11111111",
        "11000011",
        "11111111",
        "11111111",
        "11000011",
        "11111111",
        "01111110",
    ],
    "option": [
        "00111100",
        "01111110",
        "11111111",
        "11111111",
        "11111111",
        "11111111",
        "01111110",
        "00111100",
    ],
}


def create_powerup_surface(power_type, color, scale=3):
    """Create a Surface for a power-up icon."""
    matrix = POWERUP_MATRICES.get(power_type, POWERUP_MATRICES["shield"])
    return matrix_to_surface(matrix, color, scale)


# ══════════════════════════════════════════════════════════════════════
# 武器系统子弹像素
# ══════════════════════════════════════════════════════════════════════

# 不同武器类型的子弹 Matrix
BULLET_MATRICES = {
    "normal": [
        "00100",
        "01110",
        "11111",
        "01110",
    ],
    "spread": [
        "00100",
        "01110",
        "11111",
        "01110",
        "00100",
    ],
    "laser": [
        "00100",
        "00100",
        "11111",
        "11111",
        "11111",
        "11111",
        "00100",
        "00100",
    ],
    "homing": [
        "01010",
        "10101",
        "11111",
        "01110",
        "01110",
        "11111",
        "10101",
        "01010",
    ],
}

# 蓄力子弹矩阵（放大版）
CHARGE_BULLET_MATRICES = {
    1: [
        "01110",
        "11111",
        "11111",
        "11111",
        "01110",
    ],
    2: [
        "0011100",
        "0111110",
        "1111111",
        "1111111",
        "1111111",
        "0111110",
        "0011100",
    ],
    3: [
        "0001111000",
        "0011111100",
        "0111111110",
        "1111111111",
        "1111111111",
        "1111111111",
        "0111111110",
        "0011111100",
        "0001111000",
    ],
}

# 子武器矩阵（8x8）
SUB_WEAPON_MATRICES = {
    "missile": [
        "00011000",
        "00111100",
        "01111110",
        "11111111",
        "11111111",
        "01111110",
        "00011000",
        "00000000",
    ],
    "bomb": [
        "00000000",
        "00011000",
        "00111100",
        "01111110",
        "11111111",
        "01111110",
        "00111100",
        "00011000",
    ],
    "mine": [
        "00111100",
        "01000010",
        "10011001",
        "11111111",
        "11111111",
        "10011001",
        "01000010",
        "00111100",
    ],
}

# Option 辅助机矩阵（6x6）
OPTION_MATRIX = [
    "011110",
    "111111",
    "111111",
    "111111",
    "011110",
    "001100",
]

# 武器颜色映射 — imported from game.settings
# WEAPON_COLORS = { ... }

# ══════════════════════════════════════════════════════════════════════
# 道具系统图标像素矩阵 (Item System)
# ══════════════════════════════════════════════════════════════════════

ITEM_MATRICES = {
    "full_bomb": [        # 全屏炸弹 — 圆圈 + 引信火花
        "00000000",
        "00011000",
        "00111100",
        "01111110",
        "01111110",
        "00111100",
        "00011000",
        "00001000",
    ],
    "time_slow": [        # 时间减速 — 沙漏/时钟图案
        "01111110",
        "11000011",
        "10011001",
        "00011000",
        "00011000",
        "10011001",
        "11000011",
        "01111110",
    ],
    "reflect_shield": [   # 反射护盾 — 三角形盾 + 箭头
        "00011000",
        "00111100",
        "01111110",
        "11111111",
        "10000001",
        "10000001",
        "01111110",
        "00011000",
    ],
    "repair": [           # 修复 — 十字医疗
        "00011000",
        "00011000",
        "01111110",
        "11111111",
        "11111111",
        "01111110",
        "00011000",
        "00011000",
    ],
    "score_boost": [      # 分数增益 — 星星
        "00011000",
        "00011000",
        "01111110",
        "11111111",
        "11111111",
        "01111110",
        "10011001",
        "01000010",
    ],
    "gravity_bomb": [     # 重力炸弹 — 靶心+引力圈
        "00000000",
        "00111100",
        "01000010",
        "10011001",
        "10011001",
        "01000010",
        "00111100",
        "00000000",
    ],
}


def create_item_surface(item_type, color, scale=3):
    """Create a Surface for an item pickup icon."""
    matrix = ITEM_MATRICES.get(item_type, ITEM_MATRICES["full_bomb"])
    return matrix_to_surface(matrix, color, scale)


def create_weapon_bullet(weapon_type, level, is_charged=False, charge_tier=0, scale=2):
    """Create a bullet surface based on weapon type and level."""
    matrix = BULLET_MATRICES.get(weapon_type, BULLET_MATRICES["normal"])
    color = WEAPON_COLORS.get(weapon_type, YELLOW)

    if is_charged and charge_tier > 0:
        charge_matrix = CHARGE_BULLET_MATRICES.get(charge_tier)
        if charge_matrix:
            matrix = charge_matrix
        # Charged bullets get brighter color
        r = min(255, color[0] + 80)
        g = min(255, color[1] + 80)
        b = min(255, color[2] + 80)
        color = (r, g, b)
        charge_scale = charge_tier + 1
        surf = matrix_to_surface(matrix, color, scale * charge_scale)
    else:
        # Larger bullet at higher levels
        s = scale + (level // 2)
        surf = matrix_to_surface(matrix, color, s)

    return surf


def create_sub_weapon_surface(sub_type, scale=2):
    """Create a surface for a sub-weapon projectile."""
    matrix = SUB_WEAPON_MATRICES.get(sub_type, SUB_WEAPON_MATRICES["missile"])
    configs = {
        "missile": (255, 200, 50),
        "bomb": (255, 100, 50),
        "mine": (100, 255, 100),
    }
    color = configs.get(sub_type, (255, 200, 50))
    return matrix_to_surface(matrix, color, scale)


def create_option_surface(scale=2):
    """Create a surface for an option satellite."""
    return matrix_to_surface(OPTION_MATRIX, CYAN, scale)