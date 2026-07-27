# game/sprites/player.py
import pygame
from game.settings import *
from game.graphics.pixel_art import create_player_ship


class Player(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.image = create_player_ship(scale=3)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 30
        self.speed = PLAYER_SPEED
        self.lives = PLAYER_MAX_LIVES
        self.score = 0
        self.shoot_cooldown = 0
        self.invincible_timer = 0
        self.active_powerups = {}  # power_type -> remaining frames

        # ── 武器系统字段 ──
        self.weapon_levels = {w: INITIAL_WEAPON_LEVEL for w in WEAPON_TYPES}
        self.active_weapon = "normal"      # 当前使用的武器类型
        self.unlocked_weapons = ["normal"]  # 已解锁的武器列表
        self.available_weapons = ["normal"]  # 当前可用的武器

        # ── 蓄力系统 ──
        self.charge_timer = 0
        self.charge_tier = 0          # 0=未蓄力, 1/2/3=蓄力档位
        self.is_charging = False
        self.charge_released = False  # 标记本帧已释放蓄力
        self.is_firing = False        # 标记本帧是否在射击（供Option使用）

        # ── 连击系统 ──
        self.combo_count = 0
        self.combo_timer = 0
        self.combo_buff_timer = 0
        self.combo_tier = 0
        self.combo_multiplier = 1.0

        # ── 子武器系统 ──
        self.sub_weapon_type = "missile"
        self.sub_weapon_energy = SUB_WEAPON_MAX_ENERGY
        self.sub_weapon_cooldown = 0
        self.unlocked_sub_weapons = ["missile"]

        # ── Option 辅助机 ──
        self.options = []

        # ── 道具系统 (Item System) ──
        self.inventory = []               # 持有的道具列表，最多 ITEM_MAX_INVENTORY
        self.inventory_cooldown = 0       # 使用道具后的冷却帧

        # ── 道具特效状态 ──
        self.time_slow_timer = 0          # 时间减速剩余帧
        self.reflect_shield_timer = 0     # 反射护盾剩余帧
        self.score_boost_timer = 0        # 分数增益剩余帧
        self.invincible_bonus_timer = 0   # 无敌增益剩余帧（用于 repair 等）

    # ── 帧更新 ──

    def update(self, keys_pressed, *args, **kwargs):
        self._handle_movement(keys_pressed)
        self._handle_shoot_cooldown()
        self._handle_invincibility()
        self._update_powerups()
        self.update_sub_weapon()
        self.update_combo()
        self._update_item_timers()
        # Clean up charge state if not actively charging
        if not self.is_charging and self.charge_timer > 0:
            self.charge_timer = 0
            self.charge_tier = 0

    def _handle_movement(self, keys_pressed):
        speed = self.speed * 2 if self.has_powerup("speed") else self.speed
        if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.rect.x -= speed
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.rect.x += speed
        if keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            self.rect.y -= speed
        if keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            self.rect.y += speed
        # Boundary clamp
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

    def _handle_shoot_cooldown(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def _handle_invincibility(self):
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            # Blinking effect
            alpha = 128 if (self.invincible_timer // 6) % 2 == 0 else 255
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)

    def _update_powerups(self):
        """Tick down active power-up timers each frame."""
        expired = []
        for ptype, frames in self.active_powerups.items():
            self.active_powerups[ptype] = frames - 1
            if self.active_powerups[ptype] <= 0:
                expired.append(ptype)
        for ptype in expired:
            del self.active_powerups[ptype]

    def can_shoot(self):
        return self.shoot_cooldown == 0

    def shoot(self):
        self.shoot_cooldown = PLAYER_SHOOT_COOLDOWN

    # ── 武器等级系统 ──

    def upgrade_weapon(self, weapon_type=None):
        """Upgrade a weapon type by 1 level (max MAX_WEAPON_LEVEL)."""
        wt = weapon_type or self.active_weapon
        current = self.weapon_levels.get(wt, 1)
        if current < MAX_WEAPON_LEVEL:
            self.weapon_levels[wt] = current + 1
            return True
        return False

    def downgrade_weapon(self, weapon_type=None):
        """Downgrade a weapon type by 1 level (min 1) on death."""
        wt = weapon_type or self.active_weapon
        current = self.weapon_levels.get(wt, 1)
        if current > 1:
            self.weapon_levels[wt] = current - 1
            return True
        return False

    def switch_weapon(self, direction=1):
        """Switch active weapon type. direction: +1 = next, -1 = prev."""
        if len(self.available_weapons) <= 1:
            return
        idx = self.available_weapons.index(self.active_weapon)
        idx = (idx + direction) % len(self.available_weapons)
        self.active_weapon = self.available_weapons[idx]

    def unlock_weapon(self, weapon_type):
        """Permanently unlock a weapon type."""
        if weapon_type in WEAPON_TYPES and weapon_type not in self.unlocked_weapons:
            self.unlocked_weapons.append(weapon_type)
            self.available_weapons.append(weapon_type)
            return True
        return False

    def get_weapon_level(self, weapon_type=None):
        """Get the current level for the specified weapon."""
        wt = weapon_type or self.active_weapon
        return self.weapon_levels.get(wt, 1)

    def get_weapon_config(self, weapon_type=None):
        """Get the full config dict for the current (weapon, level)."""
        wt = weapon_type or self.active_weapon
        level = self.get_weapon_level(wt)
        configs = WEAPON_LEVEL_CONFIGS.get(wt, WEAPON_LEVEL_CONFIGS["normal"])
        return configs.get(level, configs[1])

    # ── 蓄力系统 ──

    def start_charge(self):
        """Begin charging."""
        self.is_charging = True
        self.charge_released = False

    def continue_charge(self):
        """Continue charging (call each frame while holding fire)."""
        if not self.is_charging:
            return
        self.charge_timer += 1
        # Calculate current tier
        new_tier = 0
        for i, tier in enumerate(CHARGE_TIERS):
            if self.charge_timer >= tier["hold_frames"]:
                new_tier = i + 1
        self.charge_tier = new_tier

    def release_charge(self):
        """Release the charge. Returns (was_charged, tier)."""
        if not self.is_charging or self.charge_timer < CHARGE_TIERS[0]["hold_frames"]:
            self.is_charging = False
            self.charge_timer = 0
            self.charge_tier = 0
            return (False, 0)
        tier = self.charge_tier
        # Reset charge state
        self.is_charging = False
        self.charge_released = True
        self.charge_timer = 0
        self.charge_tier = 0
        return (True, tier)

    def cancel_charge(self):
        """Cancel charge without firing."""
        self.is_charging = False
        self.charge_released = False
        self.charge_timer = 0
        self.charge_tier = 0

    def get_charge_progress(self):
        """Return charge progress as float 0.0-1.0 for HUD."""
        if not self.is_charging or self.charge_timer == 0:
            return 0.0
        # Find the highest tier threshold reached
        highest = 0
        for i, tier in enumerate(CHARGE_TIERS):
            if self.charge_timer >= tier["hold_frames"]:
                highest = i + 1
        if highest >= len(CHARGE_TIERS):
            return 1.0
        # Progress within current tier
        prev_threshold = CHARGE_TIERS[highest - 1]["hold_frames"] if highest > 0 else 0
        next_threshold = CHARGE_TIERS[highest]["hold_frames"]
        progress = (self.charge_timer - prev_threshold) / (next_threshold - prev_threshold)
        return (highest + progress) / len(CHARGE_TIERS)

    def get_charge_tier_config(self, tier):
        """Get charge tier config (1-indexed)."""
        if 1 <= tier <= len(CHARGE_TIERS):
            return CHARGE_TIERS[tier - 1]
        return None

    # ── 连击系统 ──

    def register_kill(self):
        """Register an enemy kill for combo tracking. Returns True if milestone reached."""
        self.combo_count += 1
        self.combo_timer = COMBO_RESET_FRAMES

        # Check if combo threshold reached
        if self.combo_count % COMBO_THRESHOLD == 0:
            self.combo_tier = self.combo_count // COMBO_THRESHOLD
            self.combo_multiplier = 1.0 + (self.combo_tier - 1) * 0.5  # 1x, 1.5x, 2x, ...
            self.combo_buff_timer = COMBO_BUFF_FRAMES
            return True  # combo milestone reached
        return False

    def update_combo(self):
        """Update combo timer each frame."""
        if self.combo_count > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.combo_count = 0
                self.combo_tier = 0
                self.combo_multiplier = 1.0
        if self.combo_buff_timer > 0:
            self.combo_buff_timer -= 1
            if self.combo_buff_timer <= 0:
                self.combo_tier = 0
                self.combo_multiplier = 1.0

    def reset_combo(self):
        """Reset combo on player hit."""
        self.combo_count = 0
        self.combo_timer = 0
        self.combo_buff_timer = 0
        self.combo_tier = 0
        self.combo_multiplier = 1.0

    def has_combo_buff(self):
        """Check if combo buff is active."""
        return self.combo_buff_timer > 0

    # ── 子武器系统 ──

    def can_fire_sub_weapon(self):
        """Check if sub-weapon can be fired."""
        if self.sub_weapon_cooldown > 0:
            return False
        config = SUB_WEAPONS.get(self.sub_weapon_type, {})
        cost = config.get("energy_cost", 15)
        return self.sub_weapon_energy >= cost

    def fire_sub_weapon(self):
        """Consume energy and return config for creating the sub-weapon sprite."""
        config = SUB_WEAPONS.get(self.sub_weapon_type, {})
        cost = config.get("energy_cost", 15)
        self.sub_weapon_energy -= cost
        self.sub_weapon_cooldown = config.get("cooldown", 20)
        return self.sub_weapon_type, config

    def update_sub_weapon(self):
        """Update sub-weapon cooldown and energy regen each frame."""
        if self.sub_weapon_cooldown > 0:
            self.sub_weapon_cooldown -= 1
        if self.sub_weapon_energy < SUB_WEAPON_MAX_ENERGY:
            self.sub_weapon_energy = min(
                SUB_WEAPON_MAX_ENERGY,
                self.sub_weapon_energy + SUB_WEAPON_REGEN_RATE,
            )

    def switch_sub_weapon(self):
        """Cycle to next unlocked sub-weapon type."""
        if len(self.unlocked_sub_weapons) <= 1:
            return
        idx = self.unlocked_sub_weapons.index(self.sub_weapon_type)
        idx = (idx + 1) % len(self.unlocked_sub_weapons)
        self.sub_weapon_type = self.unlocked_sub_weapons[idx]

    def get_sub_weapon_energy_ratio(self):
        """Return energy bar ratio 0.0-1.0 for HUD."""
        return self.sub_weapon_energy / SUB_WEAPON_MAX_ENERGY

    # ── Option 辅助机 ──

    def add_option(self):
        """Add one option satellite (if under max)."""
        if len(self.options) < OPTION_MAX_COUNT:
            # Import here to avoid circular dependency
            from game.sprites.option import Option
            opt = Option(self, len(self.options))
            self.options.append(opt)
            self.max_options = len(self.options)
            return True
        return False

    def remove_options(self):
        """Remove all options (on death)."""
        self.options.clear()

    def update_options(self):
        """Update all option positions and shooting state."""
        should_shoot = self.is_firing
        for opt in self.options:
            opt.update_position(self.rect.centerx, self.rect.centery, self.rect.bottom)
            opt.update_shoot_state(should_shoot)

    # ── 道具系统 (Item System) ──

    def _update_item_timers(self):
        """Update all item effect timers each frame."""
        if self.inventory_cooldown > 0:
            self.inventory_cooldown -= 1
        if self.time_slow_timer > 0:
            self.time_slow_timer -= 1
        if self.reflect_shield_timer > 0:
            self.reflect_shield_timer -= 1
        if self.score_boost_timer > 0:
            self.score_boost_timer -= 1
        if self.invincible_bonus_timer > 0:
            self.invincible_bonus_timer -= 1

    def can_collect_item(self):
        """Check if the player can pick up another item."""
        return len(self.inventory) < ITEM_MAX_INVENTORY

    def collect_item(self, item_type):
        """Add an item to the inventory. Returns True if collected."""
        if len(self.inventory) >= ITEM_MAX_INVENTORY:
            return False
        self.inventory.append(item_type)
        return True

    def has_item(self):
        """Check if player has any item in inventory."""
        return len(self.inventory) > 0

    def use_item(self):
        """Use the first (leftmost) item in inventory. Returns (item_type, config) or None."""
        if not self.inventory or self.inventory_cooldown > 0:
            return None
        item_type = self.inventory.pop(0)
        self.inventory_cooldown = 10  # 10 frames cooldown between uses
        config = ITEM_TYPES.get(item_type, {})
        return (item_type, config)

    def activate_item_effect(self, item_type):
        """Apply the effect of a consumed item. Returns a dict with effect details for main.py."""
        effect = {"type": item_type}
        if item_type == "full_bomb":
            effect["clear_enemies"] = True
            effect["clear_bullets"] = True
        elif item_type == "time_slow":
            self.time_slow_timer = ITEM_TYPES["time_slow"]["duration"]
        elif item_type == "reflect_shield":
            self.reflect_shield_timer = ITEM_TYPES["reflect_shield"]["duration"]
        elif item_type == "repair":
            if self.lives < PLAYER_MAX_LIVES:
                self.lives += 1
                effect["healed"] = True
            else:
                effect["healed"] = False
        elif item_type == "score_boost":
            self.score_boost_timer = ITEM_TYPES["score_boost"]["duration"]
        elif item_type == "gravity_bomb":
            effect["pull_enemies"] = True
            effect["gravity_damage"] = True
        return effect

    def has_reflect_shield(self):
        """Check if reflect shield is active."""
        return self.reflect_shield_timer > 0

    def has_time_slow(self):
        """Check if time slow is active."""
        return self.time_slow_timer > 0

    def has_score_boost(self):
        """Check if score boost is active."""
        return self.score_boost_timer > 0

    def get_score_multiplier(self):
        """Get current score multiplier (item system + combo)."""
        mult = self.combo_multiplier
        if self.has_score_boost():
            mult *= 2.0
        return mult

    # ── 伤害/道具 ──

    def hit(self):
        """Take a hit. Returns True if was actually hit."""
        # Reflect shield: does not consume the barrier, just reflects
        if self.has_reflect_shield():
            return False
        if self.invincible_timer > 0:
            return False
        self.lives -= 1
        # Reset combo on hit
        self.reset_combo()
        # Downgrade weapon on death (if still alive)
        if self.lives > 0:
            self.downgrade_weapon()
        if self.lives > 0:
            self.invincible_timer = PLAYER_INVINCIBLE_FRAMES
        return True  # was hit

    def apply_powerup(self, power_type):
        """Apply a power-up effect to the player."""
        config = POWERUP_TYPES.get(power_type)
        if not config:
            return
        duration = config.get("duration", 0)
        if power_type == "bomb":
            # bomb handled externally (clear enemies)
            pass
        elif power_type == "life":
            self.lives = min(self.lives + 1, PLAYER_MAX_LIVES)
        elif power_type == "power":
            self.upgrade_weapon()
        elif power_type == "option":
            self.add_option()
        else:
            self.active_powerups[power_type] = duration

    def has_powerup(self, power_type):
        """Check if a timed power-up is currently active."""
        return power_type in self.active_powerups

    def reset(self):
        """Reset player state for a new game (keeps weapon levels/options)."""
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 30
        self.lives = PLAYER_MAX_LIVES
        self.score = 0
        self.invincible_timer = PLAYER_INVINCIBLE_FRAMES  # respawn protection
        self.shoot_cooldown = 0
        self.active_powerups.clear()
        self.charge_timer = 0
        self.charge_tier = 0
        self.is_charging = False
        self.charge_released = False
        self.is_firing = False
        self.reset_combo()
        # Reset item system
        self.inventory.clear()
        self.inventory_cooldown = 0
        self.time_slow_timer = 0
        self.reflect_shield_timer = 0
        self.score_boost_timer = 0
        self.invincible_bonus_timer = 0
        # Keep weapon levels and unlocked weapons across games
        # Keep options

    def destroy(self):
        """Full cleanup on game end."""
        self.options.clear()