# game/systems/collision.py
import pygame
from game.sprites.explosion import Explosion


def check_bullet_enemy_collisions(bullets_group, enemies_group, explosions_group):
    """Check bullet-enemy collisions. Returns score earned this frame."""
    score_earned = 0
    for bullet in bullets_group:
        hit_enemies = pygame.sprite.spritecollide(bullet, enemies_group, False)
        for enemy in hit_enemies:
            destroyed = enemy.take_damage()
            bullet.kill()
            if destroyed:
                score_earned += enemy.score_value
                Explosion(enemy.rect.centerx, enemy.rect.centery, explosions_group)
                enemy.kill()
            break  # one bullet damages at most one enemy
    return score_earned


def check_player_enemy_collisions(player, enemies_group, explosions_group):
    """Check player-enemy collisions. Returns whether the player was hit."""
    hit_enemies = pygame.sprite.spritecollide(player, enemies_group, False)
    if hit_enemies:
        # Destroy all hit enemies (mutual destruction)
        for enemy in hit_enemies:
            Explosion(enemy.rect.centerx, enemy.rect.centery, explosions_group)
            enemy.kill()
        return player.hit()
    return False