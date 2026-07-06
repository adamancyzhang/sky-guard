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

# Boss settings
BOSS_SCORE_INTERVAL = 1000      # Boss every 1000 score
BOSS_BASE_HP = 20
BOSS_SPEED = 1
BOSS_SCORE_VALUE = 200
BOSS_SHOOT_INTERVAL = 30        # frames between boss bullet volleys
BOSS_COLOR = (200, 50, 200)
BOSS_MATRIX = [                  # 16x16 pixel art
    "0001111111111000",
    "0011111111111100",
    "0111111111111110",
    "1111100000011111",
    "1111000000001111",
    "1111011111101111",
    "1111111111111111",
    "1111111111111111",
    "1111111111111111",
    "1111011111101111",
    "1111000000001111",
    "1111100000011111",
    "0111111111111110",
    "0011111111111100",
    "0001111111111000",
    "0000110011000000",
]
BOSS_BULLET_CONFIGS = [
    # Pattern 1: spread (3 bullets at angles)
    {"pattern": "spread", "count": 3, "angle_spread": 30, "interval": 40},
    # Pattern 2: aimed (directly at player)
    {"pattern": "aimed", "count": 1, "interval": 25},
    # Pattern 3: circle (full 360 burst)
    {"pattern": "circle", "count": 8, "interval": 60},
]
BOSS_PHASE_THRESHOLDS = {
    0.66: "circle",    # below 66% HP: circle pattern
    0.33: "aimed",     # below 33% HP: aimed pattern
}

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

# ── Level-based background themes ────────────────────────────────────
# Each theme defines: colors, speed multipliers, particle effects
# Layer names: "sky", "clouds", "mountains", "city", "ground", "foreground"

BG_THEMES = {
    0: {  # 夜城 Night City
        "name": "night_city",
        "label_key": "theme_night",
        "layers": [
            {"name": "sky",        "speed": 0.3, "color": (10, 10, 40),  "stars": 40},
            {"name": "mountains",  "speed": 0.6, "color": (20, 20, 50),  "seed": 0},
            {"name": "city",       "speed": 1.2, "color": (25, 25, 45),  "seed": 0},
            {"name": "ground",     "speed": 2.0, "color": (15, 25, 20),  "seed": 0},
        ],
        "particles": [],
        "ambient_color": None,
    },
    1: {  # 黎明 Dawn
        "name": "dawn",
        "label_key": "theme_dawn",
        "layers": [
            {"name": "sky",        "speed": 0.4, "color": (60, 30, 80),   "stars": 20},
            {"name": "clouds",     "speed": 0.7, "color": (80, 50, 90),   "alpha": 100},
            {"name": "mountains",  "speed": 0.9, "color": (40, 25, 55),   "seed": 1},
            {"name": "ground",     "speed": 2.2, "color": (30, 20, 40),   "seed": 1},
        ],
        "particles": [{"type": "bird",    "rate": 0.02}],
        "ambient_color": (60, 30, 80),
    },
    2: {  # 深空 Deep Space
        "name": "deep_space",
        "label_key": "theme_space",
        "layers": [
            {"name": "sky",        "speed": 0.5, "color": (5, 5, 30),     "stars": 80},
            {"name": "clouds",     "speed": 0.8, "color": (15, 10, 40),   "alpha": 80},
            {"name": "mountains",  "speed": 1.2, "color": (10, 10, 35),   "seed": 2},
            {"name": "ground",     "speed": 2.5, "color": (8, 8, 25),     "seed": 2},
        ],
        "particles": [{"type": "shooting_star", "rate": 0.01}],
        "ambient_color": None,
    },
    3: {  # 风暴 Storm
        "name": "storm",
        "label_key": "theme_storm",
        "layers": [
            {"name": "sky",        "speed": 0.6, "color": (20, 20, 50),   "stars": 10},
            {"name": "clouds",     "speed": 1.0, "color": (40, 40, 60),   "alpha": 160},
            {"name": "mountains",  "speed": 1.5, "color": (15, 15, 35),   "seed": 3},
            {"name": "ground",     "speed": 3.0, "color": (20, 20, 30),   "seed": 3},
        ],
        "particles": [{"type": "lightning", "rate": 0.005}, {"type": "rain", "rate": 0.3}],
        "ambient_color": (20, 20, 50),
    },
    4: {  # 异星 Alien
        "name": "alien",
        "label_key": "theme_alien",
        "layers": [
            {"name": "sky",        "speed": 0.7, "color": (30, 10, 50),   "stars": 30},
            {"name": "clouds",     "speed": 1.2, "color": (50, 20, 70),   "alpha": 100},
            {"name": "mountains",  "speed": 1.8, "color": (40, 15, 55),   "seed": 4},
            {"name": "ground",     "speed": 3.2, "color": (30, 40, 20),   "seed": 4},
        ],
        "particles": [{"type": "spore", "rate": 0.05}],
        "ambient_color": (30, 10, 50),
    },
    5: {  # 终局 Final / 熔岩
        "name": "final",
        "label_key": "theme_final",
        "layers": [
            {"name": "sky",        "speed": 0.8, "color": (50, 10, 10),   "stars": 15},
            {"name": "clouds",     "speed": 1.5, "color": (70, 20, 15),   "alpha": 200},
            {"name": "mountains",  "speed": 2.0, "color": (40, 8, 8),     "seed": 5},
            {"name": "ground",     "speed": 3.5, "color": (60, 15, 5),    "seed": 5},
        ],
        "particles": [{"type": "ember", "rate": 0.1}],
        "ambient_color": (50, 10, 10),
    },
}

# Boss battle overlay
BOSS_BG_OVERLAY_COLOR = (40, 0, 0)     # dark red overlay
BOSS_BG_OVERLAY_ALPHA = 80             # 0-255
BOSS_PARTICLE_TYPE = "boss_storm"
BOSS_PARTICLE_RATE = 0.2               # particles per frame

# Transition
BG_TRANSITION_DURATION = 30  # frames (0.5s at 60fps)