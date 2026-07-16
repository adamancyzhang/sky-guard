# game/systems/spawner.py
import random
from game.settings import *
from game.sprites.enemy import Enemy


class Spawner:
    def __init__(self):
        self.timer = 0
        self.current_level = 0
        self._prev_level = 0
        self.boss_active = False
        self.next_boss_score = BOSS_SCORE_INTERVAL
        self.on_level_up = None  # callback(level: int) -> None
        self.enemy_counter = 0   # 敌机 ID 计数器（合作模式同步用）
        self._formation_cooldown = 0  # 距下次阵型还有多少帧
        self._formation_index = 0     # 当前阵型中的第几架

    def update(self, enemies_group, score):
        # Don't spawn regular enemies during boss fight
        if self.boss_active:
            return

        self.timer += 1
        # Calculate difficulty level from score
        self.current_level = min(score // SCORE_PER_LEVEL, len(DIFFICULTY_STEPS) - 1)

        # Fire level-up callback
        if self.current_level != self._prev_level:
            if self.on_level_up:
                self.on_level_up(self.current_level)
            self._prev_level = self.current_level

        config = DIFFICULTY_STEPS[self.current_level]

        spawn_interval = config["spawn_interval"]
        if self.timer >= spawn_interval:
            self.timer = 0

            # 阵型冷却递减
            if self._formation_cooldown > 0:
                self._formation_cooldown -= 1

            if self._formation_cooldown == 0 and random.random() < 0.35:
                # ── 开始一个阵型 ──
                patterns = ["line", "v", "staggered"]
                pattern = random.choice(patterns)
                self._spawn_formation(enemies_group, pattern, config)
                self._formation_cooldown = random.randint(120, 240)  # 2-4 秒后下一次阵型
            else:
                # ── 随机单架 ──
                enemy_type = random.choice(config["enemy_types"])
                self.enemy_counter += 1
                enemy = Enemy(enemy_type, eid=self.enemy_counter)
                enemies_group.add(enemy)

    # ── 阵型生成 ────────────────────────────────────────────────────────

    def _spawn_formation(self, group, pattern, config):
        """生成一个编队阵型"""
        enemy_type = random.choice(config["enemy_types"])
        count = random.randint(3, 5)
        spacing = random.randint(50, 80)
        start_x = (SCREEN_WIDTH - (count - 1) * spacing) // 2

        for i in range(count):
            self.enemy_counter += 1
            if pattern == "line":
                x = start_x + i * spacing
            elif pattern == "v":
                # V 形：中间前凸
                offset = abs(i - count // 2) * (spacing // 3)
                x = start_x + i * spacing
                self.enemy_counter += offset // 10  # 错开 EID 以保证唯一性
            else:  # staggered
                x = start_x + i * spacing + (30 if i % 2 == 0 else 0)

            enemy = Enemy(enemy_type, eid=self.enemy_counter, x=int(x))
            group.add(enemy)

    def check_boss_spawn(self, score):
        """Returns True if a boss should spawn this frame."""
        if self.boss_active:
            return False
        if score >= self.next_boss_score:
            self.boss_active = True
            self.next_boss_score += BOSS_SCORE_INTERVAL
            return True
        return False

    def reset(self):
        self.timer = 0
        self.current_level = 0
        self._prev_level = 0
        self.boss_active = False
        self.next_boss_score = BOSS_SCORE_INTERVAL
        self.on_level_up = None
        self.enemy_counter = 0