# game/systems/collision.py
import pygame
from game.sprites.explosion import Explosion


def check_bullet_enemy_collisions(bullets_group, enemies_group, explosions_group):
    """子弹击中敌机逻辑。返回本次帧获得的分数"""
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
            break  # 一颗子弹只伤害一个敌机
    return score_earned


def check_player_enemy_collisions(player, enemies_group, explosions_group):
    """玩家与敌机碰撞。返回是否被击中"""
    hit_enemies = pygame.sprite.spritecollide(player, enemies_group, False)
    if hit_enemies:
        # 消灭所有碰撞的敌机（同归于尽）
        for enemy in hit_enemies:
            Explosion(enemy.rect.centerx, enemy.rect.centery, explosions_group)
            enemy.kill()
        return player.hit()
    return False
