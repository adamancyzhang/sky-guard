# game/settings.py

# Display settings (logical resolution — actual window size is auto-calculated)
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 720
FPS = 60
WINDOW_TITLE = "Sky Guard"

# Colors (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 50, 255)
YELLOW = (255, 255, 50)
CYAN = (50, 255, 255)
PURPLE = (200, 50, 255)
DARK_GRAY = (30, 30, 30)
LIGHT_GRAY = (150, 150, 150)
ORANGE = (255, 150, 50)

# Player settings
PLAYER_SPEED = 5
PLAYER_MAX_LIVES = 3
PLAYER_SHOOT_COOLDOWN = 15  # frames between shots
PLAYER_INVINCIBLE_FRAMES = 90  # invincibility after being hit

# Bullet settings
BULLET_SPEED = -10  # negative = upward
BULLET_WIDTH = 4
BULLET_HEIGHT = 12
BULLET_COLOR = YELLOW

# Enemy settings
ENEMY_BASE_SPEED = 3
ENEMY_SPAWN_INTERVAL = 60  # frames between spawns (decreases with score)
ENEMY_MIN_SPAWN_INTERVAL = 15
ENEMY_TYPES = {
    "basic": {"speed": 3, "hp": 1, "score": 10, "color": RED},
    "fast":  {"speed": 5, "hp": 1, "score": 15, "color": PURPLE},
    "tank":  {"speed": 2, "hp": 3, "score": 30, "color": GREEN},
}

# Explosion effects
EXPLOSION_FRAMES = 12
EXPLOSION_PARTICLES = 8

# Difficulty
SCORE_PER_LEVEL = 200  # score needed per level increase
DIFFICULTY_STEPS = {
    0: {"spawn_interval": 60, "enemy_types": ["basic"]},
    1: {"spawn_interval": 50, "enemy_types": ["basic", "fast"]},
    2: {"spawn_interval": 40, "enemy_types": ["basic", "fast"]},
    3: {"spawn_interval": 35, "enemy_types": ["basic", "fast", "tank"]},
    4: {"spawn_interval": 30, "enemy_types": ["basic", "fast", "tank"]},
    5: {"spawn_interval": 25, "enemy_types": ["basic", "fast", "tank"]},
}

# Starfield background
STAR_COUNT = 60
STAR_SPEED = 2

# Enemy bullet settings
ENEMY_BULLET_SPEED = 5
ENEMY_BULLET_COLOR = (255, 100, 100)
ENEMY_BULLET_WIDTH = 3
ENEMY_BULLET_HEIGHT = 8
ENEMY_SHOOT_INTERVAL = 90      # frames between enemy shots (reduces with difficulty)
ENEMY_SHOOT_MIN_INTERVAL = 30  # minimum at high difficulty

# Parallax background layers (speed = pixels/frame)
BACKGROUND_LAYERS = [
    {"name": "sky",       "speed": 0.3, "color": (10, 10, 40)},      # 深空
    {"name": "mountains", "speed": 0.6, "color": (20, 20, 50)},      # 远山
    {"name": "city",      "speed": 1.2, "color": (25, 25, 45)},      # 城市天际线
    {"name": "ground",    "speed": 2.0, "color": (15, 25, 20)},      # 近地
]

# Power-up settings
POWERUP_DROP_CHANCE = 0.15        # 15% chance per enemy kill
POWERUP_SPEED = 2                  # fall speed
POWERUP_TYPES = {
    "shield": {
        "color": (50, 50, 255),
        "duration": 5 * FPS,       # 5 seconds in frames
        "description_key": "item_shield",
    },
    "rapid": {
        "color": ORANGE,
        "duration": 8 * FPS,
        "description_key": "item_rapid",
    },
    "triple": {
        "color": PURPLE,
        "duration": 8 * FPS,
        "description_key": "item_triple",
    },
    "bomb": {
        "color": RED,
        "duration": 0,             # instant, no timer
        "description_key": "item_bomb",
    },
    "speed": {
        "color": GREEN,
        "duration": 8 * FPS,
        "description_key": "item_speed",
    },
    "life": {
        "color": (255, 105, 180),  # pink
        "duration": 0,             # instant
        "description_key": "item_life",
    },
}