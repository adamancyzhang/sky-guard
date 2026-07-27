# game/systems/collision.py
import random
import math
import pygame
from game.settings import POWERUP_DROP_CHANCE, POWERUP_TYPES, ITEM_DROP_CHANCE, ITEM_TYPES, SCREEN_WIDTH, SCREEN_HEIGHT
from game.sprites.explosion import Explosion
from game.sprites.powerup import PowerUp
from game.sprites.item import Item


def check_bullet_enemy_collisions(bullets_group, enemies_group, explosions_group,
                                   powerups_group=None, items_group=None,
                                   killed_info_out=None, player=None):
    """Check bullet-enemy collisions. Returns score earned this frame.
    Supports bullet damage, piercing, and combo system when player is provided.
    When powerups_group is provided, enemies may drop power-ups on death.
    When items_group is provided, enemies may drop items on death.
    When killed_info_out (list) is provided, appends (eid, score, ptype_or_None) tuples.
    """
    score_earned = 0
    for bullet in bullets_group:
        if not hasattr(bullet, 'damage'):
            bullet.damage = 1
        if not hasattr(bullet, 'piercing'):
            bullet.piercing = False

        hit_enemies = pygame.sprite.spritecollide(bullet, enemies_group, False)
        for enemy in hit_enemies:
            destroyed = enemy.take_damage(bullet.damage)
            if not bullet.piercing:
                bullet.kill()
            if destroyed:
                score_earned += enemy.score_value
                # ── 连击系统 ──
                if player:
                    milestone = player.register_kill()
                    score_mult = player.get_score_multiplier()
                    score_earned = int(score_earned * score_mult)
                # ── 道具掉落 ──
                dropped_ptype = None
                if powerups_group is not None and random.random() < POWERUP_DROP_CHANCE:
                    dropped_ptype = random.choice(list(POWERUP_TYPES.keys()))
                    PowerUp(enemy.rect.centerx, enemy.rect.centery, dropped_ptype, powerups_group)
                # ── 道具掉落（独立于 PowerUp 掉落） ──
                if items_group is not None and random.random() < ITEM_DROP_CHANCE:
                    item_type = random.choice(list(ITEM_TYPES.keys()))
                    Item(enemy.rect.centerx, enemy.rect.centery, item_type, items_group)
                if killed_info_out is not None:
                    killed_info_out.append((getattr(enemy, 'eid', -1), enemy.score_value, dropped_ptype))
                Explosion(enemy.rect.centerx, enemy.rect.centery, explosions_group)
                enemy.kill()
            if not bullet.piercing:
                break  # non-piercing: one bullet damages at most one enemy
    return score_earned


def check_sub_weapon_collisions(sub_weapons_group, enemies_group, explosions_group):
    """Check sub-weapon projectiles against enemies."""
    score_earned = 0
    for proj in sub_weapons_group:
        if not hasattr(proj, 'check_hit') or not hasattr(proj, 'get_damage'):
            continue

        hit_enemies = pygame.sprite.spritecollide(proj, enemies_group, False)
        for enemy in hit_enemies:
            if proj.check_hit(enemy):
                destroyed = enemy.take_damage(proj.get_damage())
                if destroyed:
                    score_earned += enemy.score_value
                    Explosion(enemy.rect.centerx, enemy.rect.centery, explosions_group)
                    enemy.kill()
                if not proj.is_area_damage():
                    proj.kill()
                else:
                    # Area damage: create big explosion, damage all nearby
                    cx, cy = proj.get_explosion_center()
                    for other in enemies_group:
                        dx = other.rect.centerx - cx
                        dy = other.rect.centery - cy
                        if math.sqrt(dx*dx + dy*dy) <= getattr(proj, 'explosion_radius', 40):
                            destroyed2 = other.take_damage(proj.get_damage())
                            if destroyed2:
                                score_earned += other.score_value
                                Explosion(other.rect.centerx, other.rect.centery, explosions_group)
                                other.kill()
                    proj.kill()
                break
    return score_earned


def check_player_enemy_collisions(player, enemies_group, explosions_group):
    """Check player-enemy collisions. Returns whether the player was hit."""
    hit_enemies = pygame.sprite.spritecollide(player, enemies_group, False)
    if hit_enemies:
        # Skip if player has shield
        if hasattr(player, 'has_powerup') and player.has_powerup("shield"):
            # Destroy enemies but player takes no damage
            for enemy in hit_enemies:
                Explosion(enemy.rect.centerx, enemy.rect.centery, explosions_group)
                enemy.kill()
            return False
        # Skip if player has reflect shield (also protects from body contact)
        if hasattr(player, 'has_reflect_shield') and player.has_reflect_shield():
            for enemy in hit_enemies:
                Explosion(enemy.rect.centerx, enemy.rect.centery, explosions_group)
                enemy.kill()
            return False
        # Destroy all hit enemies (mutual destruction)
        for enemy in hit_enemies:
            Explosion(enemy.rect.centerx, enemy.rect.centery, explosions_group)
            enemy.kill()
        return player.hit()
    return False


def check_player_powerup_collisions(player, powerups_group):
    """Check player-powerup collisions. Returns the power-up type if collected."""
    collected = pygame.sprite.spritecollide(player, powerups_group, True)
    for pu in collected:
        return pu.power_type
    return None


def check_player_item_collisions(player, items_group):
    """Check player-item collisions. Returns the item type if collected, or None."""
    collected = pygame.sprite.spritecollide(player, items_group, True)
    for it in collected:
        # Try to add to inventory; if inventory full, drop the item back
        if player.can_collect_item():
            player.collect_item(it.item_type)
            return it.item_type
        else:
            # Inventory full — don't collect
            items_group.add(it)  # put it back (sprite already removed by True)
            return None
    return None


def check_enemy_bullet_player_collisions(player, enemy_bullets_group, explosions_group):
    """Check enemy bullet - player collisions. Returns True if player was hit.
    Also handles reflect shield: when active, enemy bullets are reflected back."""
    hit_bullets = pygame.sprite.spritecollide(player, enemy_bullets_group, True)
    if hit_bullets:
        # Reflect shield: bounce bullets back at enemies
        if hasattr(player, 'has_reflect_shield') and player.has_reflect_shield():
            for bullet in hit_bullets:
                if hasattr(bullet, 'reflect') and callable(bullet.reflect):
                    bullet.reflect()
                    enemy_bullets_group.add(bullet)  # re-add as reflected
                elif hasattr(bullet, 'vx') and hasattr(bullet, 'vy'):
                    # Generic reversal if reflect method not available
                    bullet.vy = -abs(bullet.vy)  # send upward
                    enemy_bullets_group.add(bullet)  # re-add
            return False
        if hasattr(player, 'has_powerup') and player.has_powerup("shield"):
            return False
        for bullet in hit_bullets:
            if bullet.rect:
                Explosion(bullet.rect.centerx, bullet.rect.centery, explosions_group)
        return player.hit()
    return False


def apply_gravity_bomb(enemies_group, explosions_group):
    """Gravity bomb: pull all enemies toward center of screen and damage them."""
    cx = SCREEN_WIDTH // 2
    cy = SCREEN_HEIGHT // 2
    damage_dealt = 0

    for enemy in enemies_group:
        # Pull toward center
        dx = cx - enemy.rect.centerx
        dy = cy - enemy.rect.centery
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0:
            pull = 8.0
            enemy.rect.centerx += int(dx / dist * pull)
            enemy.rect.centery += int(dy / dist * pull)

        # Damage all enemies
        destroyed = enemy.take_damage(3)
        if destroyed:
            damage_dealt += enemy.score_value
            Explosion(enemy.rect.centerx, enemy.rect.centery, explosions_group)
            enemy.kill()

    # Big explosion at center
    Explosion(cx, cy, explosions_group)
    return damage_dealt