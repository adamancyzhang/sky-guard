# game/graphics/hud.py
import pygame
import os
from game.settings import *

# Path to bundled DejaVu Sans font (OFL licensed, Unicode-safe)
_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "fonts")
_FONT_REGULAR = os.path.join(_FONT_DIR, "DejaVuSans.ttf")
_FONT_BOLD = os.path.join(_FONT_DIR, "DejaVuSans-Bold.ttf")

# Safe content area
_MARGIN = 15
_CONTENT_W = SCREEN_WIDTH - _MARGIN * 2  # 450px usable


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


# ── HUD (in-game) ──────────────────────────────────────────────────

def draw_hud(screen, score, lives, level, active_powerups=None):
    from game.l10n import L10n
    _ = L10n._

    font = _get_font(26)

    # Score (top-left)
    score_surf = font.render(_("score", score), True, WHITE)
    screen.blit(score_surf, (_MARGIN, _MARGIN))

    # Level (top-left, second row)
    level_surf = font.render(_("level", level), True, LIGHT_GRAY)
    screen.blit(level_surf, (_MARGIN, _MARGIN + 32))

    # Lives (top-right)
    hearts = "\u2665" * lives + "\u2661" * (PLAYER_MAX_LIVES - lives)
    lives_text = _("lives") + hearts
    lives_surf = font.render(lives_text, True, RED)
    lives_rect = lives_surf.get_rect()
    lives_rect.topright = (SCREEN_WIDTH - _MARGIN, _MARGIN)
    screen.blit(lives_surf, lives_rect)

    # Active power-up indicators (bottom-left)
    if active_powerups:
        draw_powerup_indicators(screen, active_powerups)


# ── Main Menu ──────────────────────────────────────────────────────

def draw_menu_screen(screen, selected):
    """Draw the main menu with localized strings, 3 options + language toggle."""
    from game.l10n import L10n
    _ = L10n._

    screen.fill(BLACK)

    # Title
    title_font = _get_font(64, bold=True)
    title = title_font.render(_("title"), True, CYAN)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
    screen.blit(title, title_rect)

    # Subtitle
    sub_font = _get_font(22)
    sub = sub_font.render(_("subtitle"), True, LIGHT_GRAY)
    sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4 + 50))
    screen.blit(sub, sub_rect)

    # Menu items
    items = [_("start_game"), _("help"), _("exit")]
    item_font_big = _get_font(42, bold=True)
    item_font_small = _get_font(32)

    start_y = SCREEN_HEIGHT // 2 - 40
    for i, item in enumerate(items):
        if i == selected:
            color = YELLOW
            prefix = "> "
            fnt = item_font_big
        else:
            color = WHITE
            prefix = "  "
            fnt = item_font_small

        surf = fnt.render(prefix + item, True, color)
        rect = surf.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 65))
        screen.blit(surf, rect)

    # Language toggle
    toggle_font = _get_font(20)
    toggle_text = _("lang_toggle")
    toggle_surf = toggle_font.render(toggle_text, True, LIGHT_GRAY)
    toggle_rect = toggle_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 70))
    screen.blit(toggle_surf, toggle_rect)

    # Controls hint (two lines)
    hint_font = _get_font(17)
    hint1 = hint_font.render(_("menu_hint"), True, DARK_GRAY)
    hint1_rect = hint1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 38))
    screen.blit(hint1, hint1_rect)
    hint2 = hint_font.render("L  —  中文/EN", True, DARK_GRAY)
    hint2_rect = hint2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 18))
    screen.blit(hint2, hint2_rect)


# ── Game Over ──────────────────────────────────────────────────────

def draw_game_over_screen(screen, score):
    """Draw the game over screen with properly-sized text."""
    from game.l10n import L10n
    _ = L10n._

    screen.fill(BLACK)

    font_large = _get_font(48, bold=True)
    font_medium = _get_font(26)
    font_small = _get_font(22)

    # Title
    title = font_large.render(_("game_over"), True, RED)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 - 20))
    screen.blit(title, title_rect)

    # Score
    score_text = font_medium.render(_("final_score", score), True, WHITE)
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10))
    screen.blit(score_text, score_rect)

    # Prompt — split into two lines to avoid overflow
    prompt_line1 = font_small.render(_("restart_prompt_line1"), True, LIGHT_GRAY)
    prompt1_rect = prompt_line1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
    screen.blit(prompt_line1, prompt1_rect)

    prompt_line2 = font_small.render(_("restart_prompt_line2"), True, LIGHT_GRAY)
    prompt2_rect = prompt_line2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 66))
    screen.blit(prompt_line2, prompt2_rect)


# ── Help Screen ────────────────────────────────────────────────────

def draw_help_screen(screen):
    """Draw the help screen with controls and power-up descriptions."""
    from game.l10n import L10n
    _ = L10n._

    screen.fill(BLACK)

    # Title
    title_font = _get_font(42, bold=True)
    title = title_font.render(_("help_title"), True, CYAN)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 28))
    screen.blit(title, title_rect)

    sub_font = _get_font(19, bold=True)
    body_font = _get_font(16)

    y = 72

    # Controls section
    ctrl_title = sub_font.render(_("controls_title"), True, YELLOW)
    screen.blit(ctrl_title, (_MARGIN, y))
    y += 28

    for key in ["controls_move", "controls_shoot", "controls_pause"]:
        line = body_font.render(_(key), True, WHITE)
        screen.blit(line, (_MARGIN + 8, y))
        y += 22

    y += 6

    # Items section
    items_title = sub_font.render(_("items_title"), True, YELLOW)
    screen.blit(items_title, (_MARGIN, y))
    y += 28

    for key in ["item_shield", "item_rapid", "item_triple", "item_bomb", "item_speed", "item_life"]:
        line = body_font.render(_(key), True, WHITE)
        screen.blit(line, (_MARGIN + 8, y))
        y += 22

    # Back prompt
    y = max(y + 14, SCREEN_HEIGHT - 50)
    hint = body_font.render(_("help_back"), True, DARK_GRAY)
    hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, y))
    screen.blit(hint, hint_rect)


# ── Power-up indicators ────────────────────────────────────────────

def draw_powerup_indicators(screen, active_powerups):
    """Show active power-ups at the bottom of the screen."""
    from game.settings import POWERUP_TYPES
    font = _get_font(16)
    x = _MARGIN
    y = SCREEN_HEIGHT - 28
    for ptype in active_powerups:
        config = POWERUP_TYPES.get(ptype)
        color = config["color"] if config else (255, 255, 255)
        text = ptype.upper()
        surf = font.render(text, True, color)
        screen.blit(surf, (x, y))
        x += surf.get_width() + 10