# game/settings.py

# 显示设置
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 720
FPS = 60
WINDOW_TITLE = "像素飞机大战"

# 颜色（RGB）
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

# 玩家设置
PLAYER_SPEED = 5
PLAYER_MAX_LIVES = 3
PLAYER_SHOOT_COOLDOWN = 15  # 帧数间隔
PLAYER_INVINCIBLE_FRAMES = 90  # 受伤后无敌帧

# 子弹设置
BULLET_SPEED = -10  # 负值=向上
BULLET_WIDTH = 4
BULLET_HEIGHT = 12
BULLET_COLOR = YELLOW

# 敌机设置
ENEMY_BASE_SPEED = 3
ENEMY_SPAWN_INTERVAL = 60  # 帧数间隔（游戏会随分数减少）
ENEMY_MIN_SPAWN_INTERVAL = 15
ENEMY_TYPES = {
    "basic": {"speed": 3, "hp": 1, "score": 10, "color": RED},
    "fast":  {"speed": 5, "hp": 1, "score": 15, "color": PURPLE},
    "tank":  {"speed": 2, "hp": 3, "score": 30, "color": GREEN},
}

# 爆炸效果
EXPLOSION_FRAMES = 12
EXPLOSION_PARTICLES = 8

# 难度
SCORE_PER_LEVEL = 200  # 每多少分增加一级难度
DIFFICULTY_STEPS = {
    0: {"spawn_interval": 60, "enemy_types": ["basic"]},
    1: {"spawn_interval": 50, "enemy_types": ["basic", "fast"]},
    2: {"spawn_interval": 40, "enemy_types": ["basic", "fast"]},
    3: {"spawn_interval": 35, "enemy_types": ["basic", "fast", "tank"]},
    4: {"spawn_interval": 30, "enemy_types": ["basic", "fast", "tank"]},
    5: {"spawn_interval": 25, "enemy_types": ["basic", "fast", "tank"]},
}

# 背景星空
STAR_COUNT = 60
STAR_SPEED = 2
