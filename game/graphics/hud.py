# game/graphics/hud.py
import pygame
import os
from game.settings import *

# Path to bundled DejaVu Sans font (OFL licensed, Unicode-safe)
_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "fonts")
_FONT_REGULAR = os.path.join(_FONT_DIR, "DejaVuSans.ttf")
_FONT_BOLD = os.path.join(_FONT_DIR, "DejaVuSans-Bold.ttf")


def _get_font(size, bold=False):
    """Load bundled DejaVu Sans font. Falls back to default on failure."""
    path = _FONT_BOLD if bold else _FONT_REGULAR
    if os.path.isfile(path):
        try:
            font = pygame.font.Font(path, size)
            # Verify the font is valid by rendering a test glyph
            test_surf = font.render("A", True, (255, 255, 255))
            if test_surf.get_width() > 0:
                return font
        except pygame.error:
            pass
    return pygame.font.Font(None, size)


def draw_hud(screen, score, lives, level):
    font = _get_font(36)
    # Score (top-left)
    score_surf = font.render(f"SCORE: {score}", True, WHITE)
    screen.blit(score_surf, (10, 10))

    # Level (top-left, second row)
    level_surf = font.render(f"LEVEL: {level}", True, LIGHT_GRAY)
    screen.blit(level_surf, (10, 45))

    # Lives (top-right)
    lives_text = "LIVES: " + "♥" * lives + "♡" * (PLAYER_MAX_LIVES - lives)
    lives_surf = font.render(lives_text, True, RED)
    lives_rect = lives_surf.get_rect()
    lives_rect.topright = (SCREEN_WIDTH - 10, 10)
    screen.blit(lives_surf, lives_rect)


def draw_menu_screen(screen, selected):
    """Draw the main menu with a selectable list."""
    screen.fill(BLACK)

    # Title
    title_font = _get_font(72, bold=True)
    title = title_font.render("SKY GUARD", True, CYAN)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
    screen.blit(title, title_rect)

    # Subtitle / tagline
    sub_font = _get_font(24)
    sub = sub_font.render("~ PIXEL SHOOTER ~", True, LIGHT_GRAY)
    sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4 + 50))
    screen.blit(sub, sub_rect)

    # Menu items
    items = ["START GAME", "EXIT"]
    item_font = _get_font(48, bold=True)
    item_font_small = _get_font(36)

    for i, item in enumerate(items):
        if i == selected:
            color = YELLOW
            prefix = "> "
            text = prefix + item
            fnt = item_font
        else:
            color = WHITE
            prefix = "  "
            text = prefix + item
            fnt = item_font_small

        surf = fnt.render(text, True, color)
        rect = surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 70))
        screen.blit(surf, rect)

    # Controls hint
    hint_font = _get_font(24)
    hint = hint_font.render("UP / DOWN to select  |  ENTER to confirm", True, DARK_GRAY)
    hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4 + 30))
    screen.blit(hint, hint_rect)


def draw_game_over_screen(screen, score):
    """Draw the game over screen."""
    screen.fill(BLACK)

    font_large = _get_font(64, bold=True)
    font_medium = _get_font(36)

    title = font_large.render("GAME OVER", True, RED)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
    screen.blit(title, title_rect)

    score_text = font_medium.render(f"FINAL SCORE: {score}", True, WHITE)
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(score_text, score_rect)

    prompt = font_medium.render("PRESS ENTER TO RESTART  |  ESC TO QUIT", True, LIGHT_GRAY)
    prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 2 // 3))
    screen.blit(prompt, prompt_rect)