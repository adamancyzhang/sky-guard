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
POWERUP_DROP_CHANCE = 0.20        # 20% chance per enemy kill (increased from 15% due to larger pool)
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
    "power": {   # weapon upgrade (permanent)
        "color": (255, 255, 100),  # gold
        "duration": 0,
        "description_key": "item_power",
    },
    "option": {  # add an option satellite
        "color": (50, 255, 255),   # cyan
        "duration": 0,
        "description_key": "item_option",
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

# ══════════════════════════════════════════════════════════════════════
# 武器系统配置
# ══════════════════════════════════════════════════════════════════════

# 武器类型枚举
WEAPON_TYPES = ["normal", "spread", "laser", "homing"]

# 每种武器名称（用于 l10n key）
WEAPON_NAMES = {
    "normal": "weapon_normal",
    "spread": "weapon_spread",
    "laser": "weapon_laser",
    "homing": "weapon_homing",
}

# 武器等级配置
# level: {"bullet_count": N, "spread_angle": deg, "damage": N, "speed_mult": float, "cooldown_mult": float}
WEAPON_LEVEL_CONFIGS = {
    "normal": {
        1: {"count": 1, "spread_angle": 0,   "damage": 1, "speed_mult": 1.0, "cooldown_mult": 1.0},
        2: {"count": 2, "spread_angle": 6,   "damage": 1, "speed_mult": 1.0, "cooldown_mult": 1.0},
        3: {"count": 3, "spread_angle": 12,  "damage": 1, "speed_mult": 1.0, "cooldown_mult": 0.9},
        4: {"count": 5, "spread_angle": 20,  "damage": 1, "speed_mult": 1.0, "cooldown_mult": 0.8},
        5: {"count": 7, "spread_angle": 25,  "damage": 1, "speed_mult": 1.2, "cooldown_mult": 0.7},
    },
    "spread": {
        1: {"count": 3, "spread_angle": 20,  "damage": 1, "speed_mult": 1.0, "cooldown_mult": 1.3},
        2: {"count": 3, "spread_angle": 25,  "damage": 1, "speed_mult": 1.0, "cooldown_mult": 1.2},
        3: {"count": 5, "spread_angle": 30,  "damage": 1, "speed_mult": 1.0, "cooldown_mult": 1.1},
        4: {"count": 5, "spread_angle": 35,  "damage": 2, "speed_mult": 1.0, "cooldown_mult": 1.0},
        5: {"count": 7, "spread_angle": 40,  "damage": 2, "speed_mult": 1.0, "cooldown_mult": 0.9},
    },
    "laser": {
        1: {"count": 1, "spread_angle": 0,   "damage": 2, "speed_mult": 2.0, "cooldown_mult": 1.8},
        2: {"count": 1, "spread_angle": 0,   "damage": 3, "speed_mult": 2.0, "cooldown_mult": 1.6},
        3: {"count": 2, "spread_angle": 0,   "damage": 3, "speed_mult": 2.0, "cooldown_mult": 1.5},
        4: {"count": 2, "spread_angle": 0,   "damage": 4, "speed_mult": 2.5, "cooldown_mult": 1.4},
        5: {"count": 3, "spread_angle": 5,    "damage": 5, "speed_mult": 2.5, "cooldown_mult": 1.3},
    },
    "homing": {
        1: {"count": 1, "spread_angle": 0,   "damage": 1, "speed_mult": 0.8, "cooldown_mult": 1.2},
        2: {"count": 2, "spread_angle": 10,  "damage": 1, "speed_mult": 0.8, "cooldown_mult": 1.1},
        3: {"count": 2, "spread_angle": 15,  "damage": 1, "speed_mult": 0.9, "cooldown_mult": 1.0},
        4: {"count": 3, "spread_angle": 15,  "damage": 2, "speed_mult": 0.9, "cooldown_mult": 0.9},
        5: {"count": 4, "spread_angle": 20,  "damage": 2, "speed_mult": 1.0, "cooldown_mult": 0.8},
    },
}

# 最大武器等级
MAX_WEAPON_LEVEL = 5

# 初始武器等级
INITIAL_WEAPON_LEVEL = 1

# 蓄力射击配置
CHARGE_SHOT_ENABLED = True
CHARGE_TIERS = [
    {"hold_frames": 20,  "damage_mult": 2.0, "speed_mult": 1.5, "size_mult": 2.0},   # 蓄力 1 档
    {"hold_frames": 50,  "damage_mult": 4.0, "speed_mult": 2.0, "size_mult": 3.0},   # 蓄力 2 档
    {"hold_frames": 90,  "damage_mult": 8.0, "speed_mult": 3.0, "size_mult": 4.0, "piercing": True},  # 蓄力 3 档
]

# 连击系统
COMBO_THRESHOLD = 5          # 每 5 连击奖一次
COMBO_BUFF_FRAMES = 120       # 奖励持续 2 秒
COMBO_RESET_FRAMES = 90       # 1.5 秒内无击杀重置连击
COMBO_MULTIPLIER_PER_TIER = 2  # 每档连击分数倍率

# 子武器系统
SUB_WEAPONS = {
    "missile": {
        "name_key": "sub_missile",
        "energy_cost": 15,
        "cooldown": 20,
        "color": (255, 200, 50),
        "damage": 2,
        "speed": 6,
        "homing_strength": 0.05,
    },
    "bomb": {
        "name_key": "sub_bomb",
        "energy_cost": 30,
        "cooldown": 40,
        "color": (255, 100, 50),
        "damage": 4,
        "speed": 4,
        "explosion_radius": 40,
    },
    "mine": {
        "name_key": "sub_mine",
        "energy_cost": 10,
        "cooldown": 10,
        "color": (100, 255, 100),
        "damage": 3,
        "speed": 0,
        "drop_speed": 2,
    },
}

SUB_WEAPON_MAX_ENERGY = 100
SUB_WEAPON_REGEN_RATE = 0.3   # 每帧恢复
SUB_WEAPON_ENERGY_KILL_REWARD = 5  # 击杀回复

# Option 辅助机
OPTION_ENABLED = True
OPTION_MAX_COUNT = 2
OPTION_OFFSET_X = 35           # 与玩家的水平偏移
OPTION_OFFSET_Y = -20          # 与玩家的垂直偏移（负=上方）
OPTION_FOLLOW_SPEED = 0.15     # 跟随平滑度
OPTION_SHOOT_DELAY = 4         # 比玩家延迟几帧射击

# Weapon power-up item color
POWERUP_P_COLOR = (255, 255, 100)  # 武器升级道具 = 金色

# 武器颜色映射
WEAPON_COLORS = {
    "normal": YELLOW,
    "spread": ORANGE,
    "laser": CYAN,
    "homing": GREEN,
}