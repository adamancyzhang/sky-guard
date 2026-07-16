# game/graphics/hud.py
import pygame
import os
from game.settings import *

# Path to bundled fonts
_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "fonts")
_FONT_CJK_REGULAR = os.path.join(_FONT_DIR, "SourceHanSansSC-Regular.otf")
_FONT_CJK_BOLD = os.path.join(_FONT_DIR, "SourceHanSansSC-Bold.otf")
_FONT_DEJAVU_REGULAR = os.path.join(_FONT_DIR, "DejaVuSans.ttf")
_FONT_DEJAVU_BOLD = os.path.join(_FONT_DIR, "DejaVuSans-Bold.ttf")

# Safe content area
_MARGIN = 15
_CONTENT_W = SCREEN_WIDTH - _MARGIN * 2  # 450px usable


def _get_font(size, bold=False):
    """Load CJK-capable font (Source Han Sans SC) with multiple fallbacks.

    Tries fonts in order until one can render a test glyph.
    Falls back to DejaVu Sans, then system default.
    """
    candidates = [
        (_FONT_CJK_BOLD if bold else _FONT_CJK_REGULAR, "\u4e2d"),
        (_FONT_DEJAVU_BOLD if bold else _FONT_DEJAVU_REGULAR, "A"),
    ]
    for path, test_char in candidates:
        if os.path.isfile(path):
            try:
                font = pygame.font.Font(path, size)
                if font.render(test_char, True, (255, 255, 255)).get_width() > 0:
                    return font
            except pygame.error:
                pass
    return pygame.font.Font(None, size)


def _render_text(text, size, color, bold=False):
    """Render text with automatic multi-font fallback per character.

    Primary font is Source Han Sans SC (CJK + Latin). If any glyph is
    missing (width == 0), falls back to DejaVu Sans for that character.
    This ensures correct rendering on all platforms including macOS.
    """
    font = _get_font(size, bold)
    try:
        surf = font.render(text, True, color)
        has_missing = any(
            font.render(ch, True, color).get_width() == 0
            for ch in text if ord(ch) > 0x2000
        )
        if not has_missing:
            return surf
    except pygame.error:
        pass

    # Per-character fallback rendering
    latin_path = _FONT_DEJAVU_BOLD if bold else _FONT_DEJAVU_REGULAR
    font_latin = None
    if os.path.isfile(latin_path):
        try:
            font_latin = pygame.font.Font(latin_path, size)
        except pygame.error:
            pass

    char_surfs = []
    total_w = 0
    max_h = 0
    for ch in text:
        # Try CJK font first for non-Latin, otherwise Latin font
        primary = font_latin if ord(ch) <= 0x2000 else font
        cs = primary.render(ch, True, color) if primary else font.render(ch, True, color)
        if cs.get_width() == 0:
            cs = font.render(ch, True, color)  # fallback
        char_surfs.append(cs)
        total_w += cs.get_width()
        max_h = max(max_h, cs.get_height())

    surf = pygame.Surface((total_w, max_h), pygame.SRCALPHA)
    x = 0
    for cs in char_surfs:
        surf.blit(cs, (x, 0))
        x += cs.get_width()
    return surf


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

    # Menu items — 4 items (added NETWORK GAME)
    items = [_("start_game"), _("network_game"), _("help"), _("exit")]
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
    """Draw the game over screen with properly-sized text and high score."""
    from game.l10n import L10n
    _ = L10n._

    # Load high score (lazy import to avoid circular deps)
    highscore = 0
    try:
        from game.highscore import HighScore
        highscore = HighScore.load()
    except ImportError:
        pass

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

    # High score
    prompt_y_offset = 0
    if highscore > 0:
        hs_text = _("highest_score", highscore)
        hs_surf = font_medium.render(hs_text, True, YELLOW)
        hs_rect = hs_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 22))
        screen.blit(hs_surf, hs_rect)
        prompt_y_offset = 26

    # Prompt — split into two lines to avoid overflow
    prompt_line1 = font_small.render(_("restart_prompt_line1"), True, LIGHT_GRAY)
    prompt1_rect = prompt_line1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40 + prompt_y_offset))
    screen.blit(prompt_line1, prompt1_rect)

    prompt_line2 = font_small.render(_("restart_prompt_line2"), True, LIGHT_GRAY)
    prompt2_rect = prompt_line2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 66 + prompt_y_offset))
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


# ══════════════════════════════════════════════════════════════════════
# 网络模式界面
# ══════════════════════════════════════════════════════════════════════

def draw_network_menu_screen(screen, username, server_host, server_port, selected_field=0):
    """
    联网菜单：输入用户名、服务器地址和端口。
    selected_field: 0=用户名, 1=服务器地址, 2=端口
    """
    from game.l10n import L10n
    _ = L10n._

    screen.fill(BLACK)

    # Title
    title_font = _get_font(48, bold=True)
    title = title_font.render(_("network_title"), True, CYAN)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 5 - 20))
    screen.blit(title, title_rect)

    input_font = _get_font(26)
    label_font = _get_font(18)

    fields = [
        {"label": _("network_username"), "value": username, "y_label": SCREEN_HEIGHT // 2 - 100, "y_input": SCREEN_HEIGHT // 2 - 72},
        {"label": _("server_host"), "value": server_host, "y_label": SCREEN_HEIGHT // 2 - 20, "y_input": SCREEN_HEIGHT // 2 + 8},
        {"label": _("server_port"), "value": str(server_port), "y_label": SCREEN_HEIGHT // 2 + 60, "y_input": SCREEN_HEIGHT // 2 + 88},
    ]

    for i, field in enumerate(fields):
        is_selected = (i == selected_field)

        # Label
        label = label_font.render(field["label"], True, LIGHT_GRAY)
        screen.blit(label, (_MARGIN, field["y_label"]))

        # Input box
        color = YELLOW if is_selected else WHITE
        surf = input_font.render(field["value"] or (" " if is_selected else ""), True, color)

        bg_rect = surf.get_rect()
        bg_rect.topleft = (_MARGIN, field["y_input"])
        bg_rect.w = _CONTENT_W
        pygame.draw.rect(screen, (50, 50, 50) if is_selected else (25, 25, 25), bg_rect, border_radius=4)
        pygame.draw.rect(screen, color, bg_rect, 2 if is_selected else 1, border_radius=4)

        display_val = field["value"] if field["value"] else (" " if is_selected else "")
        val_surf = input_font.render(display_val, True, color)
        screen.blit(val_surf, (_MARGIN + 8, field["y_input"] + 2))

    # Hints
    hint_font = _get_font(17)
    hints = [
        _("network_connect_hint"),
        _("network_back_hint"),
    ]
    for i, hint_text in enumerate(hints):
        hint = hint_font.render(hint_text, True, DARK_GRAY)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50 + i * 20))
        screen.blit(hint, hint_rect)


def draw_lobby_screen(screen, username, player_id, online_count=0, room_id_input="", selected_option=0):
    """
    大厅界面：显示玩家信息、操作选项。
    selected_option: 0=创建房间, 1=加入房间, 2=自动匹配, 3=返回
    """
    from game.l10n import L10n
    _ = L10n._

    screen.fill(BLACK)

    # Player info
    info_font = _get_font(18)
    info = info_font.render(
        _("player_info", username, player_id or "---"), True, LIGHT_GRAY
    )
    screen.blit(info, (_MARGIN, _MARGIN))

    # Online count
    online_text = _("online_count", online_count)
    online_surf = info_font.render(online_text, True, GREEN)
    online_rect = online_surf.get_rect(topright=(SCREEN_WIDTH - _MARGIN, _MARGIN))
    screen.blit(online_surf, online_rect)

    # Section title
    title_font = _get_font(36, bold=True)
    title = title_font.render(_("lobby_title"), True, CYAN)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
    screen.blit(title, title_rect)

    # Options
    items = [
        _("lobby_create_room"),
        _("lobby_join_room"),
        _("lobby_matchmaking"),
        _("lobby_back"),
    ]
    item_font_big = _get_font(34, bold=True)
    item_font_small = _get_font(26)

    start_y = SCREEN_HEIGHT // 2 - 40
    for i, item in enumerate(items):
        if i == selected_option:
            color = YELLOW
            prefix = "> "
            fnt = item_font_big
        else:
            color = WHITE
            prefix = "  "
            fnt = item_font_small

        surf = fnt.render(prefix + item, True, color)
        rect = surf.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 55))
        screen.blit(surf, rect)

    # If selected "join room", show input field
    if selected_option == 1:
        input_font = _get_font(22)
        input_label = input_font.render(_("room_id_input"), True, LIGHT_GRAY)
        screen.blit(input_label, (_MARGIN, SCREEN_HEIGHT - 100))
        input_box = input_font.render(room_id_input or "______", True, YELLOW)
        screen.blit(input_box, (_MARGIN + 10, SCREEN_HEIGHT - 72))

    # Bottom hint
    hint_font = _get_font(16)
    hint = hint_font.render(_("lobby_hint"), True, DARK_GRAY)
    hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 16))
    screen.blit(hint, hint_rect)


def draw_room_screen(screen, room_data, username):
    """
    房间等待界面：显示房间信息、玩家列表。
    """
    from game.l10n import L10n
    _ = L10n._

    screen.fill(BLACK)

    # Title
    title_font = _get_font(36, bold=True)
    title = title_font.render(_("room_title"), True, CYAN)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
    screen.blit(title, title_rect)

    # Room ID
    room_id = (room_data or {}).get("room_id", "---")
    id_font = _get_font(28, bold=True)
    id_surf = id_font.render(f"ID: {room_id}", True, YELLOW)
    id_rect = id_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
    screen.blit(id_surf, id_rect)

    # Share hint
    hint_font = _get_font(18)
    hint = hint_font.render(_("room_share_hint"), True, LIGHT_GRAY)
    hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + 36))
    screen.blit(hint, hint_rect)

    # Players
    players = (room_data or {}).get("players", [])
    player_font = _get_font(24)
    player_y = SCREEN_HEIGHT // 2 + 20
    for p in players:
        p_name = p.get("username", "???")
        marker = _("room_you") if p_name == username else ""
        p_surf = player_font.render(f"  {p_name}  {marker}", True, GREEN)
        screen.blit(p_surf, (_MARGIN + 40, player_y))
        player_y += 36

    # Waiting indicator
    waiting_y = player_y + 20
    room = room_data or {}
    if room.get("guest") is None and room.get("player_count", 1) < 2:
        wait_text = _("room_waiting")
    else:
        wait_text = _("room_ready")
    wait_font = _get_font(22)
    wait_surf = wait_font.render(wait_text, True, LIGHT_GRAY)
    wait_rect = wait_surf.get_rect(center=(SCREEN_WIDTH // 2, waiting_y))
    screen.blit(wait_surf, wait_rect)

    # Back hint
    back_font = _get_font(18)
    back = back_font.render(_("room_leave_hint"), True, DARK_GRAY)
    back_rect = back.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
    screen.blit(back, back_rect)


def draw_matchmaking_screen(screen, elapsed):
    """匹配等待界面"""
    from game.l10n import L10n
    _ = L10n._

    screen.fill(BLACK)

    title_font = _get_font(48, bold=True)
    title = title_font.render(_("matchmaking_title"), True, CYAN)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
    screen.blit(title, title_rect)

    # Animated dots
    dots = "." * (int(elapsed * 2) % 4)
    status_font = _get_font(32)
    status = status_font.render(_("matchmaking_searching") + dots, True, YELLOW)
    status_rect = status.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(status, status_rect)

    # Timer
    timer_font = _get_font(22)
    timer_str = f"{int(elapsed)}s"
    timer = timer_font.render(timer_str, True, LIGHT_GRAY)
    timer_rect = timer.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
    screen.blit(timer, timer_rect)

    # Cancel hint
    hint_font = _get_font(18)
    hint = hint_font.render(_("matchmaking_cancel_hint"), True, DARK_GRAY)
    hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
    screen.blit(hint, hint_rect)


def draw_connecting_screen(screen, message=""):
    """连接中界面"""
    screen.fill(BLACK)

    title_font = _get_font(36, bold=True)
    title = title_font.render("Connecting...", True, CYAN)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
    screen.blit(title, title_rect)

    if message:
        msg_font = _get_font(22)
        msg = msg_font.render(message, True, LIGHT_GRAY)
        msg_rect = msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(msg, msg_rect)


def draw_network_game_hud(screen, score, lives, level, active_powerups,
                          opponent_name="", opponent_score=0, opponent_lives=0):
    """
    网络对战 HUD：在原有 HUD 基础上增加对手信息。
    """
    # 先画基础 HUD
    draw_hud(screen, score, lives, level, active_powerups)

    # CO-OP 标识（顶栏居中）
    coop_font = _get_font(16)
    coop_tag = coop_font.render("[ CO-OP ]", True, (100, 255, 200))
    coop_rect = coop_tag.get_rect(center=(SCREEN_WIDTH // 2, 12))
    screen.blit(coop_tag, coop_rect)

    # 对手信息（右下角）
    if opponent_name:
        font = _get_font(20)
        opp_text = f"[VS] {opponent_name}"
        opp_surf = font.render(opp_text, True, YELLOW)
        opp_rect = opp_surf.get_rect(bottomright=(SCREEN_WIDTH - _MARGIN, SCREEN_HEIGHT - _MARGIN))
        screen.blit(opp_surf, opp_rect)

        if opponent_score > 0:
            score_font = _get_font(18)
            opp_score = score_font.render(f"Score: {opponent_score}", True, LIGHT_GRAY)
            score_rect = opp_score.get_rect(
                bottomright=(SCREEN_WIDTH - _MARGIN, SCREEN_HEIGHT - _MARGIN - 24)
            )
            screen.blit(opp_score, score_rect)

        # Opponent lives
        if opponent_lives > 0:
            lives_font = _get_font(18)
            opp_lives = lives_font.render(
                f"{'♥' * opponent_lives}", True, (255, 100, 100)
            )
            lives_rect = opp_lives.get_rect(
                bottomright=(SCREEN_WIDTH - _MARGIN, SCREEN_HEIGHT - _MARGIN - 46)
            )
            screen.blit(opp_lives, lives_rect)

        # 合作模式不画分割线


def draw_network_game_over_screen(screen, won, your_score, opponent_score, opponent_name):
    """网络对战结果界面"""
    from game.l10n import L10n
    _ = L10n._

    screen.fill(BLACK)

    # Result title
    title_font = _get_font(56, bold=True)
    title_text = _("game_win") if won else _("game_lose")
    title_color = GREEN if won else RED
    title = title_font.render(title_text, True, title_color)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 - 20))
    screen.blit(title, title_rect)

    # Score comparison
    score_font = _get_font(26)
    you_text = score_font.render(f"{_('final_score', your_score)}", True, WHITE)
    you_rect = you_text.get_rect(center=(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2))
    screen.blit(you_text, you_rect)

    vs_text = score_font.render("VS", True, LIGHT_GRAY)
    vs_rect = vs_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(vs_text, vs_rect)

    opp_text = score_font.render(f"{opponent_name}: {opponent_score}", True, YELLOW)
    opp_rect = opp_text.get_rect(center=(SCREEN_WIDTH // 2 + 60, SCREEN_HEIGHT // 2))
    screen.blit(opp_text, opp_rect)

    # Prompt
    hint_font = _get_font(20)
    hint = hint_font.render(_("network_game_over_hint"), True, DARK_GRAY)
    hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
    screen.blit(hint, hint_rect)


def draw_network_countdown_screen(screen, count, opponent_name=""):
    """网络对战开始倒计时"""
    from game.l10n import L10n
    _ = L10n._

    screen.fill(BLACK)

    # Opponent name
    if opponent_name:
        name_font = _get_font(24)
        name_surf = name_font.render(f"VS  {opponent_name}", True, YELLOW)
        name_rect = name_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        screen.blit(name_surf, name_rect)

    # Big countdown number
    if count > 0:
        num_font = _get_font(120, bold=True)
        color = (255, 255, 100) if count > 1 else (255, 200, 50)
        num_surf = num_font.render(str(count), True, color)
        num_rect = num_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        # Glow effect
        glow_surf = num_font.render(str(count), True, (color[0]//3, color[1]//3, color[2]//3))
        for dx, dy in [(-3,-3),(3,-3),(-3,3),(3,3)]:
            screen.blit(glow_surf, (num_rect.x + dx, num_rect.y + dy))
        screen.blit(num_surf, num_rect)
    else:
        # GO!
        go_font = _get_font(80, bold=True)
        go_surf = go_font.render("GO!", True, GREEN)
        go_rect = go_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        screen.blit(go_surf, go_rect)


def draw_disconnected_overlay(screen):
    """在网络游戏画面上叠加显示断线提示"""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    from game.l10n import L10n
    _ = L10n._
    font = _get_font(36, bold=True)
    text = font.render(_("opponent_disconnected"), True, RED)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
    screen.blit(text, text_rect)

    hint_font = _get_font(20)
    hint = hint_font.render(_("opponent_disconnected_hint"), True, LIGHT_GRAY)
    hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
    screen.blit(hint, hint_rect)


def draw_coop_game_over_screen(screen, final_score, your_name, partner_name):
    """合作模式结算 — 双人共同成绩，无输赢对比"""
    from game.l10n import L10n
    _ = L10n._

    screen.fill(BLACK)

    # Title
    title_font = _get_font(48, bold=True)
    title = title_font.render("CO-OP COMPLETE!", True, (100, 255, 200))
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
    screen.blit(title, title_rect)

    # Both players
    name_font = _get_font(26)
    p1 = name_font.render(f"✈  {your_name}", True, CYAN)
    p1_rect = p1.get_rect(center=(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 - 30))
    screen.blit(p1, p1_rect)

    p2 = name_font.render(f"✈  {partner_name}", True, (180, 100, 255))
    p2_rect = p2.get_rect(center=(SCREEN_WIDTH // 2 + 60, SCREEN_HEIGHT // 2 - 30))
    screen.blit(p2, p2_rect)

    # Combined score
    score_font = _get_font(36, bold=True)
    score_label = score_font.render(_("final_score", final_score), True, YELLOW)
    score_rect = score_label.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
    screen.blit(score_label, score_rect)

    # Prompt
    hint_font = _get_font(20)
    hint = hint_font.render(_("network_game_over_hint"), True, DARK_GRAY)
    hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
    screen.blit(hint, hint_rect)