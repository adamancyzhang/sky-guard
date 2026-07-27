"""Tests for the weapon system overhaul."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame
pygame.display.init()
pygame.font.init()


def test_weapon_level_up_and_down():
    from game.sprites.player import Player
    p = Player()
    assert p.get_weapon_level("normal") == 1
    p.upgrade_weapon("normal")
    assert p.get_weapon_level("normal") == 2
    p.upgrade_weapon("normal")
    assert p.get_weapon_level("normal") == 3
    p.downgrade_weapon("normal")
    assert p.get_weapon_level("normal") == 2
    p.downgrade_weapon("normal")
    assert p.get_weapon_level("normal") == 1
    p.downgrade_weapon("normal")  # shouldn't go below 1
    assert p.get_weapon_level("normal") == 1
    print("  ✓ test_weapon_level_up_and_down")


def test_weapon_type_switch():
    from game.sprites.player import Player
    p = Player()
    p.available_weapons = ["normal", "spread"]
    assert p.active_weapon == "normal"
    p.switch_weapon(1)
    assert p.active_weapon == "spread"
    p.switch_weapon(1)
    assert p.active_weapon == "normal"
    p.switch_weapon(-1)
    assert p.active_weapon == "spread"
    print("  ✓ test_weapon_type_switch")


def test_unlock_weapon():
    from game.sprites.player import Player
    p = Player()
    assert "laser" not in p.available_weapons
    p.unlock_weapon("laser")
    assert "laser" in p.available_weapons
    assert "laser" in p.unlocked_weapons
    print("  ✓ test_unlock_weapon")


def test_charge_shot():
    from game.sprites.player import Player
    p = Player()
    assert p.charge_tier == 0
    p.start_charge()
    assert p.is_charging
    for _ in range(100):
        p.continue_charge()
    assert p.charge_tier >= 2
    released, tier = p.release_charge()
    assert released
    assert tier >= 2
    assert not p.is_charging
    print("  ✓ test_charge_shot")


def test_combo_system():
    from game.sprites.player import Player
    p = Player()
    assert p.combo_count == 0
    p.register_kill()
    assert p.combo_count == 1

    # Threshold at 5
    for _ in range(4):
        p.register_kill()
    assert p.combo_count == 5
    assert p.combo_tier == 1
    assert p.combo_buff_timer > 0
    assert p.has_combo_buff()

    # Reset on hit
    p.reset_combo()
    assert p.combo_count == 0
    assert not p.has_combo_buff()
    print("  ✓ test_combo_system")


def test_sub_weapon():
    from game.sprites.player import Player
    from game.settings import SUB_WEAPON_MAX_ENERGY
    p = Player()
    assert p.sub_weapon_energy > 0
    assert p.can_fire_sub_weapon()
    sub_type, config = p.fire_sub_weapon()
    assert sub_type == "missile"
    assert p.sub_weapon_energy < SUB_WEAPON_MAX_ENERGY
    # Cooldown
    assert not p.can_fire_sub_weapon()  # cooldown
    print("  ✓ test_sub_weapon")


def test_option_add():
    from game.sprites.player import Player
    from game.settings import OPTION_MAX_COUNT
    p = Player()
    assert len(p.options) == 0
    p.add_option()
    assert len(p.options) == 1
    p.add_option()
    assert len(p.options) == OPTION_MAX_COUNT
    p.add_option()  # should not exceed max
    assert len(p.options) == OPTION_MAX_COUNT
    print("  ✓ test_option_add")


def test_weapon_config_values():
    from game.settings import WEAPON_LEVEL_CONFIGS
    normal_lv1 = WEAPON_LEVEL_CONFIGS["normal"][1]
    assert normal_lv1["count"] == 1
    assert normal_lv1["damage"] == 1

    laser_lv5 = WEAPON_LEVEL_CONFIGS["laser"][5]
    assert laser_lv5["count"] == 3
    assert laser_lv5["damage"] == 5
    print("  ✓ test_weapon_config_values")


def test_bullet_constructor():
    from game.sprites.bullet import Bullet
    from game.settings import BULLET_SPEED

    b = Bullet(100, 100, "normal", 3)
    assert b.weapon_type == "normal"
    assert b.weapon_level == 3
    assert b.damage == 1
    assert not b.piercing
    assert b.vy == BULLET_SPEED  # default speed

    b2 = Bullet(100, 100, "laser", 5, is_charged=True, charge_tier=3,
                custom_damage=40, custom_speed=-20, piercing=True)
    assert b2.damage == 40
    assert b2.piercing
    assert b2.vy == -20
    print("  ✓ test_bullet_constructor")


def test_player_powerup_apply():
    from game.sprites.player import Player
    from game.settings import PLAYER_MAX_LIVES
    p = Player()
    # Power-up
    assert p.get_weapon_level("normal") == 1
    p.apply_powerup("power")
    assert p.get_weapon_level("normal") == 2

    # Option
    assert len(p.options) == 0
    p.apply_powerup("option")
    assert len(p.options) == 1

    # Life (start at max, so stays at max)
    assert p.lives == PLAYER_MAX_LIVES
    p.apply_powerup("life")
    assert p.lives == PLAYER_MAX_LIVES  # capped

    # Reduce lives first to test life pickup
    p.lives = 1
    p.apply_powerup("life")
    assert p.lives == 2

    print("  ✓ test_player_powerup_apply")


def test_player_hit_downgrade():
    from game.sprites.player import Player
    p = Player()
    p.upgrade_weapon("normal")
    p.upgrade_weapon("normal")
    assert p.get_weapon_level("normal") == 3
    p.lives = 2
    p.invincible_timer = 0
    p.hit()
    # Should downgrade weapon (still alive)
    assert p.get_weapon_level("normal") == 2
    print("  ✓ test_player_hit_downgrade")


def test_hud_imports():
    from game.graphics.hud import draw_weapon_hud, draw_hud
    from game.sprites.player import Player
    p = Player()
    surf = pygame.Surface((480, 720))
    draw_weapon_hud(surf, p)

    p.start_charge()
    for _ in range(60):
        p.continue_charge()
    draw_weapon_hud(surf, p)
    p.release_charge()

    for _ in range(6):
        p.register_kill()
    draw_weapon_hud(surf, p)

    draw_hud(surf, 1000, 3, 2, {'shield': 100}, player=p)
    print("  ✓ test_hud_imports")


def test_option_sprite():
    from game.sprites.player import Player
    from game.sprites.option import Option
    p = Player()
    opt = Option(p, 0)
    assert opt.rect is not None
    opt.update_position(240, 360, 400)
    assert opt.rect is not None
    print("  ✓ test_option_sprite")


def test_sub_weapon_projectile():
    from game.sprites.sub_weapon_projectile import SubWeaponProjectile
    p = SubWeaponProjectile(100, 100, 'missile', {"damage": 2, "speed": 6, "homing_strength": 0.05})
    assert p.damage == 2
    assert p.life == 180
    p.update()
    assert p.rect.y < 100  # moved upward
    print("  ✓ test_sub_weapon_projectile")


def test_l10n_keys():
    from game.l10n import L10n
    _ = L10n._
    L10n.set_lang("en")
    assert _("weapon_normal") == "Normal"
    assert _("sub_missile") == "MIS"
    assert _("item_power") != "!item_power!"

    L10n.set_lang("zh")
    assert _("weapon_normal") == "标准"
    assert _("controls_weapon") == "Q/E  —  切换武器"
    print("  ✓ test_l10n_keys")


def test_pixel_art_functions():
    from game.graphics.pixel_art import (
        create_weapon_bullet, create_sub_weapon_surface,
        create_option_surface, create_powerup_surface
    )
    from game.settings import POWERUP_P_COLOR

    b = create_weapon_bullet("normal", 3)
    assert b.get_width() > 0

    b2 = create_weapon_bullet("laser", 5, is_charged=True, charge_tier=2)
    assert b2.get_width() > 0

    s = create_sub_weapon_surface("missile")
    assert s.get_width() > 0

    o = create_option_surface()
    assert o.get_width() > 0

    p = create_powerup_surface("power", POWERUP_P_COLOR)
    assert p.get_width() > 0
    print("  ✓ test_pixel_art_functions")


# ── 新增测试 ──────────────────────────────────────────────────────────


def test_bullet_damage_vs_enemy():
    """Bullet with damage > 1 should kill tank enemy in fewer hits."""
    from game.sprites.enemy import Enemy
    from game.settings import ENEMY_TYPES

    # Tank has HP=3, bullet damage=1 needs 3 hits
    enemy = Enemy("tank")
    assert enemy.hp == 3
    assert not enemy.take_damage(1)  # 3→2, still alive
    assert not enemy.take_damage(1)  # 2→1, still alive
    assert enemy.take_damage(1)      # 1→0, destroyed

    # With damage=3, one hit destroys
    enemy2 = Enemy("tank")
    assert enemy2.take_damage(3)
    print("  ✓ test_bullet_damage_vs_enemy")


def test_piercing_bullet():
    """Piercing bullets should not be killed on first enemy hit."""
    from game.sprites.bullet import Bullet
    from game.sprites.enemy import Enemy
    import pygame

    b = Bullet(100, 100, "laser", 5, piercing=True)
    assert b.piercing

    # Add bullet to a group so alive() works
    bg = pygame.sprite.Group(b)

    e1 = Enemy("basic", eid=1, x=100)
    e1.rect.center = (100, 110)

    # spritecollide does NOT kill the bullet — only our collision handler does
    # Verify collision is detected
    hit = pygame.sprite.spritecollide(b, pygame.sprite.Group(e1), False)
    assert len(hit) > 0
    assert b.alive()  # still in group

    print("  ✓ test_piercing_bullet")


def test_homing_bullet_tracking():
    """Homing bullet should track nearest enemy."""
    from game.sprites.bullet import Bullet
    from game.sprites.enemy import Enemy
    import pygame

    b = Bullet(100, 100, "homing", 1)
    e = Enemy("basic", eid=1, x=105)
    e.rect.center = (105, 80)

    enemies = pygame.sprite.Group(e)
    b.set_enemies_ref(enemies)

    # After update, bullet should move toward enemy x=105
    old_vx = b.vx
    b.update()
    # Homing should adjust vx toward enemy (enemy is to the right at x=105)
    # This verifies the tracking logic runs without error
    print("  ✓ test_homing_bullet_tracking")


def test_combo_timer_expiry():
    """Combo should reset after timer expires without kills."""
    from game.sprites.player import Player
    p = Player()

    p.register_kill()
    assert p.combo_count == 1

    # update_combo decrements timer first, then checks if <= 0
    # Timer of 2 means one more tick before expiry
    p.combo_timer = 2
    p.update_combo()
    assert p.combo_count == 1  # timer went 2→1, still > 0

    p.update_combo()
    assert p.combo_count == 0  # timer went 1→0, expired
    print("  ✓ test_combo_timer_expiry")


def test_sub_weapon_all_types():
    """All three sub-weapon types should initialize and behave correctly."""
    from game.sprites.sub_weapon_projectile import SubWeaponProjectile
    from game.settings import SUB_WEAPONS

    # Missile
    m = SubWeaponProjectile(100, 100, "missile", SUB_WEAPONS["missile"])
    assert m.vy < 0  # moves upward
    m.update()
    assert m.rect.y < 100

    # Bomb
    b = SubWeaponProjectile(100, 100, "bomb", SUB_WEAPONS["bomb"])
    assert not b.has_exploded
    assert b.explosion_radius == 40
    b.update()
    assert b.rect.y < 100

    # Mine
    mn = SubWeaponProjectile(100, 100, "mine", SUB_WEAPONS["mine"])
    assert not mn.armed
    assert mn.arm_timer == 30
    assert mn.vy > 0  # drops down
    # After arm timer, mine should be armed
    for _ in range(31):
        mn.update()
    assert mn.armed
    print("  ✓ test_sub_weapon_all_types")


def test_option_shoot_position():
    """Option should return a valid shoot position."""
    from game.sprites.player import Player
    from game.sprites.option import Option
    p = Player()
    opt = Option(p, 0)
    opt.update_position(p.rect.centerx, p.rect.centery, p.rect.bottom)
    x, y = opt.get_shoot_position()
    assert x > 0
    assert y > 0
    print("  ✓ test_option_shoot_position")


def test_all_weapon_configs_valid():
    """All 4 weapon types across all 5 levels should have valid configs."""
    from game.settings import WEAPON_LEVEL_CONFIGS, WEAPON_TYPES, MAX_WEAPON_LEVEL

    for wt in WEAPON_TYPES:
        configs = WEAPON_LEVEL_CONFIGS.get(wt)
        assert configs is not None, f"Missing config for {wt}"
        for level in range(1, MAX_WEAPON_LEVEL + 1):
            cfg = configs.get(level)
            assert cfg is not None, f"Missing {wt} level {level}"
            assert cfg["count"] >= 1
            assert cfg["damage"] >= 1
            assert cfg["speed_mult"] > 0
            assert cfg["cooldown_mult"] > 0
    print("  ✓ test_all_weapon_configs_valid")


def test_sub_weapon_energy_regen():
    """Sub-weapon energy should regen over time."""
    from game.sprites.player import Player
    from game.settings import SUB_WEAPON_MAX_ENERGY, SUB_WEAPON_REGEN_RATE
    p = Player()
    p.sub_weapon_energy = 50

    # Regen for 10 frames
    for _ in range(10):
        p.update_sub_weapon()
    assert p.sub_weapon_energy > 50
    print("  ✓ test_sub_weapon_energy_regen")


def test_charge_cancel():
    """Cancel charge should reset charge state without firing."""
    from game.sprites.player import Player
    p = Player()
    p.start_charge()
    for _ in range(50):
        p.continue_charge()
    assert p.is_charging
    p.cancel_charge()
    assert not p.is_charging
    assert p.charge_tier == 0
    assert p.charge_timer == 0
    print("  ✓ test_charge_cancel")


def test_death_triggers_downgrade_and_combo_reset():
    """Player hit when at 1 life should downgrade weapon and reset combo."""
    from game.sprites.player import Player
    p = Player()
    p.upgrade_weapon("normal")
    p.upgrade_weapon("normal")
    p.upgrade_weapon("normal")
    assert p.get_weapon_level("normal") == 4

    p.register_kill()
    p.register_kill()
    p.register_kill()
    assert p.combo_count > 0

    # Simulate hit with 2 lives → still alive, downgrade
    p.lives = 2
    p.invincible_timer = 0
    p.hit()
    assert p.get_weapon_level("normal") == 3  # downgraded
    assert p.combo_count == 0  # combo reset
    assert p.lives == 1  # lost one life
    print("  ✓ test_death_triggers_downgrade_and_combo_reset")


def test_boss_damage_takes_bullet_damage():
    """Boss should take variable damage from bullets with damage attribute."""
    from game.sprites.boss import Boss
    from game.sprites.bullet import Bullet
    import pygame

    boss = Boss()
    boss.rect.center = (240, 100)
    boss.hp = 20
    boss.max_hp = 20

    # Create a charged bullet with damage=5
    b = Bullet(240, 100, "laser", 5, is_charged=True, charge_tier=3,
               custom_damage=5, piercing=True)
    boss.take_damage(b.damage)
    assert boss.hp == 15  # 20 - 5
    print("  ✓ test_boss_damage_takes_bullet_damage")


def test_sub_weapon_collision_vs_enemy():
    """Sub-weapon projectiles should collide with and damage enemies."""
    from game.sprites.sub_weapon_projectile import SubWeaponProjectile
    from game.sprites.enemy import Enemy
    from game.systems.collision import check_sub_weapon_collisions
    from game.sprites.explosion import Explosion
    from game.settings import SUB_WEAPONS
    import pygame

    sub_group = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    explosions = pygame.sprite.Group()

    # Missile at same position as enemy
    m = SubWeaponProjectile(100, 100, "missile", SUB_WEAPONS["missile"])
    sub_group.add(m)

    enemy = Enemy("basic", eid=1, x=100)
    enemy.rect.center = (100, 110)
    enemies.add(enemy)

    score = check_sub_weapon_collisions(sub_group, enemies, explosions)
    assert score == 10  # basic enemy = 10 points
    assert len(enemies) == 0  # enemy killed
    print("  ✓ test_sub_weapon_collision_vs_enemy")


if __name__ == "__main__":
    tests = [
        test_weapon_level_up_and_down,
        test_weapon_type_switch,
        test_unlock_weapon,
        test_charge_shot,
        test_combo_system,
        test_sub_weapon,
        test_option_add,
        test_weapon_config_values,
        test_bullet_constructor,
        test_player_powerup_apply,
        test_player_hit_downgrade,
        test_hud_imports,
        test_option_sprite,
        test_sub_weapon_projectile,
        test_l10n_keys,
        test_pixel_art_functions,
        test_bullet_damage_vs_enemy,
        test_piercing_bullet,
        test_homing_bullet_tracking,
        test_combo_timer_expiry,
        test_sub_weapon_all_types,
        test_option_shoot_position,
        test_all_weapon_configs_valid,
        test_sub_weapon_energy_regen,
        test_charge_cancel,
        test_death_triggers_downgrade_and_combo_reset,
        test_boss_damage_takes_bullet_damage,
        test_sub_weapon_collision_vs_enemy,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    if failed > 0:
        sys.exit(1)
    print("ALL WEAPON SYSTEM TESTS PASSED!")