# game/systems/spawner.py
import random
from game.settings import *
from game.sprites.enemy import Enemy


class Spawner:
    def __init__(self):
        self.timer = 0
        self.current_level = 0
        self.boss_active = False
        self.next_boss_score = BOSS_SCORE_INTERVAL

    def update(self, enemies_group, score):
        # Don't spawn regular enemies during boss fight
        if self.boss_active:
            return

        self.timer += 1
        # Calculate difficulty level from score
        self.current_level = min(score // SCORE_PER_LEVEL, len(DIFFICULTY_STEPS) - 1)
        config = DIFFICULTY_STEPS[self.current_level]

        spawn_interval = config["spawn_interval"]
        if self.timer >= spawn_interval:
            self.timer = 0
            enemy_type = random.choice(config["enemy_types"])
            enemy = Enemy(enemy_type)
            enemies_group.add(enemy)

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
        self.boss_active = False
        self.next_boss_score = BOSS_SCORE_INTERVAL