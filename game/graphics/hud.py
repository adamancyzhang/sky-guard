# game/graphics/hud.py
import pygame
from game.settings import *


def draw_hud(screen, score, lives, level):
    font = pygame.font.Font(None, 36)  # 使用默认字体
    # 分数（左上）
    score_surf = font.render(f"SCORE: {score}", True, WHITE)
    screen.blit(score_surf, (10, 10))

    # 关卡/难度（左上第二行）
    level_surf = font.render(f"LEVEL: {level}", True, LIGHT_GRAY)
    screen.blit(level_surf, (10, 45))

    # 生命值（右上）
    lives_text = "LIVES: " + "♥" * lives + "♡" * (PLAYER_MAX_LIVES - lives)
    lives_surf = font.render(lives_text, True, RED)
    lives_rect = lives_surf.get_rect()
    lives_rect.topright = (SCREEN_WIDTH - 10, 10)
    screen.blit(lives_surf, lives_rect)


def draw_menu_screen(screen):
    """绘制开始菜单"""
    screen.fill(BLACK)

    # 标题
    title_font = pygame.font.Font(None, 72)
    title = title_font.render("飞机大战", True, CYAN)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
    screen.blit(title, title_rect)

    # 提示
    hint_font = pygame.font.Font(None, 36)
    hint1 = hint_font.render("按 ENTER 开始游戏", True, WHITE)
    hint1_rect = hint1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(hint1, hint1_rect)

    hint2 = hint_font.render("方向键 / WASD 移动", True, LIGHT_GRAY)
    hint2_rect = hint2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    screen.blit(hint2, hint2_rect)

    hint3 = hint_font.render("空格 / Z 射击", True, LIGHT_GRAY)
    hint3_rect = hint3.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
    screen.blit(hint3, hint3_rect)

    # 闪烁的"准备"提示
    if pygame.time.get_ticks() % 1000 < 500:
        blink_font = pygame.font.Font(None, 28)
        blink = blink_font.render("- ENTER TO START -", True, YELLOW)
        blink_rect = blink.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4))
        screen.blit(blink, blink_rect)


def draw_game_over_screen(screen, score):
    """绘制游戏结束界面"""
    screen.fill(BLACK)

    font_large = pygame.font.Font(None, 64)
    font_medium = pygame.font.Font(None, 36)

    title = font_large.render("GAME OVER", True, RED)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
    screen.blit(title, title_rect)

    score_text = font_medium.render(f"最终得分: {score}", True, WHITE)
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(score_text, score_rect)

    prompt = font_medium.render("按 ENTER 重新开始 / ESC 退出", True, LIGHT_GRAY)
    prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 2 // 3))
    screen.blit(prompt, prompt_rect)
