# game/systems/collision.py
import random
import pygame
from game.settings import POWERUP_DROP_CHANCE, POWERUP_TYPES
from game.sprites.explosion import Explosion
from game.sprites.powerup import PowerUp


def check_bullet_enemy_collisions(bullets_group, enemies_group, explosions_group, powerups_group=None, killed_info_out=None):
    """Check bullet-enemy collisions. Returns score earned this frame.
    When powerups_group is provided, enemies may drop power-ups on death.
    When killed_info_out (list) is provided, appends (eid, score, ptype_or_None) tuples.
    """
    score_earned = 0
    for bullet in bullets_group:
        hit_enemies = pygame.sprite.spritecollide(bullet, enemies_group, False)
        for enemy in hit_enemies:
            destroyed = enemy.take_damage()
            bullet.kill()
            if destroyed:
                score_earned += enemy.score_value
                # 判断是否掉落道具
                dropped_ptype = None
                if powerups_group is not None and random.random() < POWERUP_DROP_CHANCE:
                    dropped_ptype = random.choice(list(POWERUP_TYPES.keys()))
                    PowerUp(enemy.rect.centerx, enemy.rect.centery, dropped_ptype, powerups_group)
                if killed_info_out is not None:
                    killed_info_out.append((getattr(enemy, 'eid', -1), enemy.score_value, dropped_ptype))
                Explosion(enemy.rect.centerx, enemy.rect.centery, explosions_group)
                enemy.kill()
            break  # one bullet damages at most one enemy
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


def check_enemy_bullet_player_collisions(player, enemy_bullets_group, explosions_group):
    """Check enemy bullet - player collisions. Returns True if player was hit."""
    hit_bullets = pygame.sprite.spritecollide(player, enemy_bullets_group, True)
    if hit_bullets:
        if hasattr(player, 'has_powerup') and player.has_powerup("shield"):
            return False
        for bullet in hit_bullets:
            if bullet.rect:
                Explosion(bullet.rect.centerx, bullet.rect.centery, explosions_group)
        return player.hit()
    return False