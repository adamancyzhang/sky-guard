# game/sprites/boss.py
import pygame
import random
import math
from game.settings import *
from game.graphics.pixel_art import create_boss_surface, create_boss_surface_variant


class Boss(pygame.sprite.Sprite):
    """Large boss enemy with phase-based attack patterns, multi-stage visuals,
    minion summoning, and defeat sequence."""

    def __init__(self, *groups):
        super().__init__(*groups)
        self.image = create_boss_surface(scale=3)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.y = -self.rect.height

        self.max_hp = BOSS_BASE_HP
        self.hp = self.max_hp
        self.score_value = BOSS_SCORE_VALUE
        self.speed = BOSS_SPEED

        # Movement: enter from top, then strafe horizontally
        self.phase = "entering"  # entering -> fighting -> defeated
        self.enter_y_target = 60
        self.move_direction = 1
        self.shoot_timer = 0
        self.current_pattern = "spread"

        # ── 多阶段视觉 ──
        self._phase_color = (200, 50, 200)  # default purple
        self._pulse_frame = 0
        self._pulse_dir = 1

        # ── 召唤小兵 ──
        self.summon_timer = BOSS_SUMMON_INTERVAL
        self._summon_enabled = False  # becomes True at HP threshold

        # ── Laser Sweep 弹幕 ──
        self._laser_aim_timer = 0      # countdown before laser fires
        self._laser_active = False
        self._laser_y = 0
        self._laser_sweep_dir = 1
        self._laser_warning_alpha = 0

        # ── 击败序列 ──
        self._defeat_timer = 0
        self._defeat_flash_visible = True

        # ── 跟踪弹 ──
        self._homing_targets = {}      # missile_id -> target info

    # ── 帧更新 ────────────────────────────────────────────────────

    def update(self, *args, **kwargs):
        if self.phase == "entering":
            self.rect.y += self.speed
            if self.rect.y >= self.enter_y_target:
                self.rect.y = self.enter_y_target
                self.phase = "fighting"
            return

        if self.phase == "defeated":
            self._update_defeat()
            return

        # Phase: fighting — horizontal strafe
        self.rect.x += self.move_direction * self.speed * 2
        if self.rect.right >= SCREEN_WIDTH - 20:
            self.move_direction = -1
        elif self.rect.left <= 20:
            self.move_direction = 1

        # Update phase based on HP
        hp_ratio = self.hp / self.max_hp
        if hp_ratio <= 0.33:
            self.current_pattern = "aimed"
        elif hp_ratio <= 0.66:
            self.current_pattern = "circle"

        # ── 多阶段视觉效果 ──
        self._update_phase_visuals(hp_ratio)

        # ── 召唤小兵 ──
        if BOSS_SUMMON_ENABLED:
            self.summon_timer -= 1
            if hp_ratio <= BOSS_SUMMON_HP_THRESHOLD:
                self._summon_enabled = True

    def _update_phase_visuals(self, hp_ratio):
        """Update boss appearance based on HP phase."""
        self._pulse_frame += self._pulse_dir
        if abs(self._pulse_frame) > 2:
            self._pulse_dir *= -1

        if hp_ratio <= 0.33:
            # Aimed phase: gold pulse
            self._phase_color = BOSS_PHASE_COLORS["aimed"]
            pulse = 0 if self._pulse_frame == 0 else 1 if self._pulse_frame > 0 else -1
            self.image = create_boss_surface_variant(scale=3, tint_color=self._phase_color, pulse=pulse)
        elif hp_ratio <= 0.66:
            # Circle phase: red-orange
            self._phase_color = BOSS_PHASE_COLORS["circle"]
            self.image = create_boss_surface_variant(scale=3, tint_color=self._phase_color)
        else:
            # Default: purple
            self._phase_color = BOSS_PHASE_COLORS["fighting"]
            self.image = create_boss_surface_variant(scale=3, tint_color=self._phase_color)

        # Recenter after visual change
        cx, cy = self.rect.center
        self.rect = self.image.get_rect(center=(cx, cy))

    def _update_defeat(self):
        """Handle defeat animation sequence."""
        self._defeat_timer += 1
        # Flash on/off for first phase
        if self._defeat_timer <= BOSS_DEFEAT_FLASH_FRAMES:
            self._defeat_flash_visible = self._defeat_timer % 6 < 3
            if self._defeat_flash_visible:
                self.image = create_boss_surface_variant(scale=3, tint_color=(255, 50, 50))
            else:
                self.image.fill((0, 0, 0, 0))
        elif self._defeat_timer <= BOSS_DEFEAT_FLASH_FRAMES + BOSS_DEFEAT_FINAL_FRAMES:
            # After flash: keep invisible, particles handle visual
            self.image.fill((0, 0, 0, 0))
        else:
            self.kill()

    # ── 射击逻辑 ──────────────────────────────────────────────────

    def should_shoot(self):
        """Timer-based shooting. Returns True when boss should fire."""
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            interval = BOSS_SHOOT_INTERVAL
            for cfg in BOSS_BULLET_CONFIGS:
                if cfg["pattern"] == self.current_pattern:
                    interval = cfg["interval"]
                    break
            # Add laser sweep and homing into rotation
            additional = []
            hp_ratio = self.hp / self.max_hp
            if hp_ratio <= 0.50 and random.random() < 0.25:
                additional.append("laser_sweep")
            if hp_ratio <= 0.40 and random.random() < 0.20:
                additional.append("homing_missile")
            if additional:
                choice = random.choice(additional)
                for cfg in BOSS_BULLET_CONFIGS:
                    if cfg["pattern"] == choice:
                        interval = cfg["interval"]
                        self.current_pattern = choice
                        break
            else:
                # Keep main pattern rotation
                pass
            self.shoot_timer = interval
            return True
        return False

    def should_summon(self):
        """Returns True if boss should summon minions this frame."""
        if not BOSS_SUMMON_ENABLED:
            return False
        if not self._summon_enabled:
            return False
        if self.phase != "fighting":
            return False
        if self.summon_timer > 0:
            return False
        self.summon_timer = BOSS_SUMMON_INTERVAL
        return True

    def get_summon_positions(self):
        """Return (x, y) positions for summoned minions."""
        positions = []
        for i in range(BOSS_SUMMON_COUNT):
            offset_x = (i - (BOSS_SUMMON_COUNT - 1) / 2) * 40
            x = self.rect.centerx + offset_x
            y = self.rect.bottom + 10 + i * 10
            positions.append((x, y))
        return positions

    def get_bullet_vectors(self, player_x, player_y):
        """Return a list of (vx, vy) tuples for the current pattern.
        Also returns sweep/homing metadata for special patterns."""
        vectors = []
        metadata = {}
        pattern_config = None
        for cfg in BOSS_BULLET_CONFIGS:
            if cfg["pattern"] == self.current_pattern:
                pattern_config = cfg
                break
        if not pattern_config:
            pattern_config = BOSS_BULLET_CONFIGS[0]

        if self.current_pattern == "spread":
            count = pattern_config["count"]
            spread = pattern_config["angle_spread"]
            dx = player_x - self.rect.centerx
            dy = player_y - self.rect.centery
            base_angle = math.degrees(math.atan2(dy, dx))
            for i in range(count):
                angle = math.radians(base_angle - spread / 2 + (spread / (count - 1)) * i)
                vx = math.cos(angle) * ENEMY_BULLET_SPEED
                vy = math.sin(angle) * ENEMY_BULLET_SPEED
                vectors.append((vx, vy))

        elif self.current_pattern == "aimed":
            dx = player_x - self.rect.centerx
            dy = player_y - self.rect.centery
            dist = max(1, (dx * dx + dy * dy) ** 0.5)
            vx = (dx / dist) * ENEMY_BULLET_SPEED * 1.2
            vy = (dy / dist) * ENEMY_BULLET_SPEED * 1.2
            vectors.append((vx, vy))

        elif self.current_pattern == "circle":
            count = pattern_config["count"]
            for i in range(count):
                angle = math.radians((360 / count) * i)
                vx = math.cos(angle) * ENEMY_BULLET_SPEED * 0.8
                vy = math.sin(angle) * ENEMY_BULLET_SPEED * 0.8
                vectors.append((vx, vy))

        elif self.current_pattern == "laser_sweep":
            # Laser sweep: one horizontal beam that sweeps across
            start_x = -20 if self._laser_sweep_dir > 0 else SCREEN_WIDTH + 20
            self._laser_y = self.rect.centery + 20
            self._laser_sweep_dir *= -1  # alternate direction
            metadata["laser_sweep"] = {
                "start_x": start_x,
                "y": self._laser_y,
                "direction": self._laser_sweep_dir,
                "speed": BOSS_LASER_SPEED,
                "width": BOSS_LASER_WIDTH,
                "color": BOSS_LASER_COLOR,
                "aim_frames": BOSS_LASER_AIM_FRAMES,
            }
            # No regular bullet vectors for this pattern
            vectors = []

        elif self.current_pattern == "homing_missile":
            count = pattern_config["count"]
            for i in range(count):
                # Start near boss, spread initial angles
                start_angle = math.radians(-20 + (40 / max(count - 1, 1)) * i)
                vx = math.cos(start_angle) * HOMING_MISSILE_CONFIG["speed"]
                vy = math.sin(start_angle) * HOMING_MISSILE_CONFIG["speed"]
                vectors.append((vx, vy))
            metadata["homing_missile"] = {
                "homing_strength": HOMING_MISSILE_CONFIG["homing_strength"],
                "lifetime": HOMING_MISSILE_CONFIG["lifetime"],
                "speed": HOMING_MISSILE_CONFIG["speed"],
                "damage": HOMING_MISSILE_CONFIG["damage"],
            }

        return vectors, metadata

    # ── 伤害系统 ──────────────────────────────────────────────────

    def take_damage(self, amount=1):
        """Apply damage to boss. Returns True if defeated."""
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self._start_defeat()
            return True
        return False

    def _start_defeat(self):
        """Begin defeat animation sequence."""
        self.phase = "defeated"
        self._defeat_timer = 0

    def is_defeated(self):
        return self.hp <= 0

    def is_defeat_animating(self):
        return self.phase == "defeated"

    def get_hp_ratio(self):
        return max(0, self.hp / self.max_hp) if self.max_hp > 0 else 0

    def is_alive(self):
        """Compatibility alias for alive()."""
        return self.alive()

    def get_minion_spawn_y(self):
        return self.rect.bottom + 10

    def can_summon(self):
        return self._summon_enabled and self.phase == "fighting" and self.alive()
