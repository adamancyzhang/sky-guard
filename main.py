# main.py
import math
import random
import sys
import time

import pygame

from game.graphics.hud import (
    draw_boss_health_bar,
    draw_boss_warning,
    draw_connecting_screen,
    draw_coop_game_over_screen,
    draw_disconnected_overlay,
    draw_fade_overlay,
    draw_game_over_screen,
    draw_game_over_stats,
    draw_help_screen,
    draw_hit_flash,
    draw_hud,
    draw_laser_sweeps,
    draw_lobby_screen,
    draw_matchmaking_screen,
    draw_menu_screen,
    draw_network_countdown_screen,
    draw_network_game_hud,
    draw_network_menu_screen,
    draw_pause_screen,
    draw_room_screen,
)
from game.graphics.screen_shake import ScreenShake
from game.settings import *
from game.sounds.music_manager import MusicManager
from game.sounds.sound_manager import SoundManager
from game.sprites.boss import Boss
from game.sprites.bullet import Bullet
from game.sprites.enemy_bullet import EnemyBullet, HomingMissile
from game.sprites.explosion import Explosion
from game.sprites.player import Player
from game.sprites.sub_weapon_projectile import SubWeaponProjectile
from game.state import GameState
from game.systems.collision import (
    apply_gravity_bomb,
    check_bullet_enemy_collisions,
    check_enemy_bullet_player_collisions,
    check_player_enemy_collisions,
    check_player_item_collisions,
    check_player_powerup_collisions,
    check_sub_weapon_collisions,
)
from game.systems.spawner import Spawner
from network import get_client, has_network_support
from network.protocol import DEFAULT_HOST, DEFAULT_PORT, NetworkEvent


class Game:
    def __init__(self):
        pygame.init()
        # Detect screen size for initial window size
        info = pygame.display.Info()
        max_w, max_h = int(info.current_w * 0.9), int(info.current_h * 0.9)
        scale_w = max_w // SCREEN_WIDTH
        scale_h = max_h // SCREEN_HEIGHT
        self.scale_factor = max(1, min(scale_w, scale_h))
        self.display_width = SCREEN_WIDTH * self.scale_factor
        self.display_height = SCREEN_HEIGHT * self.scale_factor

        self.screen = pygame.display.set_mode(
            (self.display_width, self.display_height),
            pygame.RESIZABLE,
        )
        pygame.display.set_caption(WINDOW_TITLE)
        self.virtual_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.state = GameState()
        self.running = True
        self.menu_selection = 0  # 0 = START GAME, 1 = NETWORK GAME, 2 = HELP, 3 = EXIT
        self.pause_selection = 0  # 0 = RESUME, 1 = QUIT TO MENU
        # ── 帧计数器 & HUD 动效状态 ──
        self._frame_count = 0

        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.player_group = pygame.sprite.GroupSingle()
        self.bullets_group = pygame.sprite.Group()
        self.enemies_group = pygame.sprite.Group()
        self.explosions_group = pygame.sprite.Group()
        self.powerups_group = pygame.sprite.Group()
        self.enemy_bullets_group = pygame.sprite.Group()
        self.boss_group = pygame.sprite.GroupSingle()
        self.sub_weapons_group = pygame.sprite.Group()
        self.items_group = pygame.sprite.Group()

        # Game systems
        self.player = Player()
        self.spawner = Spawner()
        self.sound_manager = SoundManager()
        self._wpn_switch_cooldown = 0  # weapon switch cooldown

        # Background
        from game.graphics.background import LevelBackgroundManager
        self.background = LevelBackgroundManager()
        self.screen_shake = ScreenShake()

        # ── 粒子系统 ──
        from game.graphics.particles import ParticleManager
        self.particles = ParticleManager()

        # ── BGM ──
        from game.sounds.music_manager import MusicManager
        self.music_manager = MusicManager(
            volume=0.5,
            muted=False,
        )

        # ── 从 settings.json 恢复音量和静音状态 ──
        from game.settings_manager import load as load_settings
        settings = load_settings()
        self.music_manager.set_volume(settings.get("music_volume", 0.5))
        self.music_manager.set_muted(settings.get("muted", False))
        self.sound_manager.set_volume(settings.get("sfx_volume", 0.7))

        # ── 网络模块 ────────────────────────────────────────────────────
        self.net_client: NetworkClient | None = None
        # 联网菜单状态
        self.server_host = DEFAULT_HOST
        self.server_port = DEFAULT_PORT
        self.net_username_buffer = ""
        self.net_menu_selected_field = 0  # 0=用户名, 1=主机, 2=端口
        self.net_host_buffer = ""
        self.net_port_buffer = ""
        self._init_net_buffers()

        # 大厅状态
        self.lobby_selection = 0
        self.room_id_buffer = ""
        self.current_room = None
        self.opponent_username = ""
        self.opponent_score = 0
        self.opponent_lives = 0
        self.opponent_disconnected = False
        # ── 合作模式字段 ──
        self.partner_state = {"x": 0, "y": 0, "target_x": 0, "target_y": 0, "lives": 0, "score": 0}
        self.shared_score = 0
        self.shared_lives = 0
        self.coop_seed = 0
        self.is_host = False
        self.enemy_kill_queue = []  # 待移除的敌机 EID
        self.partner_bullets = []  # 伙伴子弹视觉列表 [(x, y, dy, life), ...]
        self.coop_frame_counter = 0
        # ── ──
        self.countdown_number = 0
        self.countdown_timer = 0.0
        self.matchmaking_start_time = 0
        self.network_error_msg = ""
        self.online_count = 0

        # ── Boss 入场警告 ──
        self.boss_warning_timer = 0
        self.boss_warning_active = False

        # ── 画面过渡 ──
        self.fade_alpha = 0
        self.fade_state = None  # None | "fade_in" | "fade_out" | "hold"
        self.fade_target = None  # state to switch to after fade
        self.fade_hold_timer = 0

        # ── 战斗统计 ──
        self.game_stats = {
            "kills": 0,
            "bosses_defeated": 0,
            "items_used": 0,
            "max_combo": 0,
            "start_time": 0,
        }

        # ── 红闪 ──
        self.hit_flash_timer = 0

        # ── 激光扫描 ──
        self.laser_sweeps = []  # list of active laser beams

        # 注册网络事件
        self._register_network_callbacks()

    def _init_net_buffers(self):
        self.net_host_buffer = str(self.server_host)
        self.net_port_buffer = str(self.server_port)

    def _register_network_callbacks(self):
        """注册网络事件回调"""
        # 会在每次状态切换时重新注册，以避免残留引用

    def _on_connected(self, data):
        self.network_error_msg = ""
        self.state.set(GameState.LOBBY)
        if self.net_client:
            self.net_client.request_player_list()

    def _on_disconnected(self, data):
        if self.state.current in (GameState.CONNECTING, GameState.LOBBY,
                                   GameState.MATCHMAKING, GameState.ROOM):
            self.state.set(GameState.NETWORK_MENU)
            self.network_error_msg = "连接已断开"

    def _on_registered(self, data):
        # Registered successfully — already handled in process_events flow
        pass

    def _on_error(self, data):
        self.network_error_msg = data.get("message", "未知错误")

    def _on_room_created(self, data):
        self.current_room = data.get("room", {})
        self.is_host = True
        self.state.set(GameState.ROOM)

    def _on_room_joined(self, data):
        self.current_room = data.get("room", {})
        self.is_host = False
        self.state.set(GameState.ROOM)

    def _on_player_joined(self, data):
        self.current_room = data.get("room", {})
        # Auto-update room display

    def _on_player_left(self, data):
        self.current_room = data.get("room", {})
        if self.state.current == GameState.NETWORK_PLAYING:
            # 对手在游戏中断线
            self.opponent_disconnected = True
        elif self.state.current == GameState.NETWORK_COUNTDOWN:
            # 对手在倒计时中断线，取消对局
            self.opponent_disconnected = True
            self.state.set(GameState.LOBBY)

    def _on_room_closed(self, data):
        self.current_room = None
        self.state.set(GameState.LOBBY)
        self.network_error_msg = data.get("message", "房间已关闭")

    def _on_match_found(self, data):
        self.current_room = data.get("room", {})
        self.opponent_username = data.get("opponent", {}).get("username", "对手")
        # 匹配时 room 的 host 是匹配发起方
        room = data.get("room", {})
        host_id = room.get("host", {}).get("player_id", "")
        self.is_host = (self.net_client is not None and
                        self.net_client.player_id == host_id)

    def _on_game_start(self, data):
        # 获取合作种子，初始化随机序列使双方敌机一致
        self.coop_seed = data.get("seed", 0)
        self.state.set(GameState.NETWORK_COUNTDOWN)
        self.countdown_number = 3
        self.countdown_timer = time.time()
        self.opponent_disconnected = False
        self.enemy_kill_queue.clear()
        self.shared_score = 0
        self.shared_lives = 6  # 双方各 3 条命，共享生命池
        self._reset_game_state()

    def _on_opponent_input(self, data):
        # Handle opponent game input
        input_data = data.get("data", {})
        if "score" in input_data:
            self.opponent_score = input_data["score"]
        if "lives" in input_data:
            self.opponent_lives = input_data["lives"]

    def _on_partner_state(self, data):
        """接收伙伴的实时位置/状态（平滑插值）"""
        state = data.get("state", {})
        # Store target position for smooth lerp
        self.partner_state["target_x"] = state.get("x", self.partner_state.get("x", 0))
        self.partner_state["target_y"] = state.get("y", self.partner_state.get("y", 0))
        self.partner_state["lives"] = state.get("lives", 0)
        self.partner_state["score"] = state.get("score", 0)

    def _on_enemy_killed(self, data):
        """伙伴击杀了一个敌机 — 从本地移除相同 EID 的敌机，同步道具"""
        from game.sprites.powerup import PowerUp
        eid = data.get("enemy_id")
        pts = data.get("score", 0)
        self.shared_score += pts
        if eid is not None:
            self.enemy_kill_queue.append(eid)
        # 伙伴击杀掉落了道具 — 在本地也生成一个
        ptype = data.get("powerup")
        if ptype:
            PowerUp(self.partner_state.get("x", SCREEN_WIDTH // 2),
                    self.partner_state.get("y", 0), ptype, self.powerups_group)

    def _on_partner_bullet(self, data):
        """伙伴发射了子弹 — 在本地渲染"""
        bx = data.get("x", 0)
        by = data.get("y", 0)
        is_triple = data.get("is_triple", False)
        self.partner_bullets.append([bx, by, 0, 100])
        if is_triple:
            self.partner_bullets.append([bx - 12, by, 0, 100])
            self.partner_bullets.append([bx + 12, by, 0, 100])

    def _on_enemy_snapshot(self, data):
        """接收 host 的敌机位置快照 — 平滑跟随"""
        if not self.is_host:
            snap = {e["eid"]: e for e in data.get("enemies", []) if "eid" in e}
            for enemy in self.enemies_group:
                eid = getattr(enemy, "eid", None)
                if eid in snap:
                    s = snap[eid]
                    enemy.rect.x += (s["x"] - enemy.rect.x) * 0.25
                    enemy.rect.y += (s["y"] - enemy.rect.y) * 0.25

    def _on_player_list(self, data):
        # Store online count for lobby display
        self.online_count = data.get("online_count", data.get("players", [data]))
        # If online_count is in the data directly:
        if isinstance(self.online_count, list):
            self.online_count = len(self.online_count)
        else:
            self.online_count = max(1, self.online_count)

    def _setup_net_client(self, username: str):
        """创建并连接网络客户端"""
        if self.net_client:
            self.net_client.disconnect()

        self.net_client = get_client(self.server_host, self.server_port)
        # 注册事件
        self.net_client.on(NetworkEvent.CONNECTED, self._on_connected)
        self.net_client.on(NetworkEvent.DISCONNECTED, self._on_disconnected)
        self.net_client.on(NetworkEvent.REGISTERED, self._on_registered)
        self.net_client.on(NetworkEvent.ERROR, self._on_error)
        self.net_client.on(NetworkEvent.ROOM_CREATED, self._on_room_created)
        self.net_client.on(NetworkEvent.ROOM_JOINED, self._on_room_joined)
        self.net_client.on(NetworkEvent.PLAYER_JOINED, self._on_player_joined)
        self.net_client.on(NetworkEvent.PLAYER_LEFT, self._on_player_left)
        self.net_client.on(NetworkEvent.ROOM_CLOSED, self._on_room_closed)
        self.net_client.on(NetworkEvent.MATCH_FOUND, self._on_match_found)
        self.net_client.on(NetworkEvent.GAME_START, self._on_game_start)
        self.net_client.on(NetworkEvent.OPPONENT_INPUT, self._on_opponent_input)
        self.net_client.on(NetworkEvent.PARTNER_STATE, self._on_partner_state)
        self.net_client.on(NetworkEvent.ENEMY_KILLED, self._on_enemy_killed)
        self.net_client.on(NetworkEvent.PARTNER_BULLET, self._on_partner_bullet)
        self.net_client.on(NetworkEvent.ENEMY_SNAPSHOT, self._on_enemy_snapshot)
        self.net_client.on(NetworkEvent.PLAYER_LIST, self._on_player_list)

        self.net_client.connect(username)

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            # Process network events (must be called every frame)
            self._process_network_events()
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
        self._cleanup_network()
        pygame.quit()
        sys.exit()

    def _process_network_events(self):
        """处理所有待处理的网络事件"""
        if self.net_client:
            self.net_client.process_events()

    def _cleanup_network(self):
        if self.net_client:
            self.net_client.disconnect()

    # ── 事件处理 ────────────────────────────────────────────────────────

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self._handle_resize(event.w, event.h)
            elif event.type == pygame.KEYDOWN:
                # ── 全局键：M 静音、[/] 音量（在任何状态下生效）──
                if event.key == pygame.K_m:
                    self.music_manager.toggle_mute()
                    from game.settings_manager import save
                    save({"muted": self.music_manager.muted})
                elif event.key == pygame.K_LEFTBRACKET:
                    vol = max(0.0, self.music_manager.volume - 0.1)
                    self.music_manager.set_volume(vol)
                    self.sound_manager.set_volume(vol)
                    from game.settings_manager import save
                    save({"music_volume": vol, "sfx_volume": vol})
                elif event.key == pygame.K_RIGHTBRACKET:
                    vol = min(1.0, self.music_manager.volume + 0.1)
                    self.music_manager.set_volume(vol)
                    self.sound_manager.set_volume(vol)
                    from game.settings_manager import save
                    save({"music_volume": vol, "sfx_volume": vol})
                elif self.state.is_menu():
                    self._handle_menu_key(event)
                elif self.state.current == GameState.HELP:
                    self._handle_help_key(event)
                elif self.state.current == GameState.NETWORK_MENU:
                    self._handle_network_menu_key(event)
                elif self.state.current == GameState.CONNECTING:
                    if event.key == pygame.K_ESCAPE:
                        self._cleanup_network()
                        self.state.set(GameState.NETWORK_MENU)
                elif self.state.current == GameState.LOBBY:
                    self._handle_lobby_key(event)
                elif self.state.current == GameState.ROOM:
                    self._handle_room_key(event)
                elif self.state.current == GameState.MATCHMAKING:
                    self._handle_matchmaking_key(event)
                elif self.state.current == GameState.NETWORK_COUNTDOWN:
                    # 倒计时期间不接受操作
                    pass
                elif self.state.current == GameState.GAME_OVER:
                    self._handle_game_over_key(event)
                elif self.state.current == GameState.NETWORK_GAME_OVER:
                    self._handle_network_game_over_key(event)
                elif self.state.current == GameState.NETWORK_PLAYING:
                    self._handle_network_playing_key(event)
                elif self.state.is_playing() or self.state.is_paused():
                    self._handle_single_playing_key(event)

    def _handle_menu_key(self, event):
        menu_count = 4  # START, NETWORK, HELP, EXIT
        if event.key == pygame.K_UP or event.key == pygame.K_w:
            self.menu_selection = (self.menu_selection - 1) % menu_count
            self.sound_manager.play("shoot")
        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
            self.menu_selection = (self.menu_selection + 1) % menu_count
            self.sound_manager.play("shoot")
        elif event.key == pygame.K_l:
            from game.l10n import L10n
            L10n.toggle()
            self.sound_manager.play("shoot")
        elif event.key == pygame.K_RETURN:
            if self.menu_selection == 0:
                self._start_game()
            elif self.menu_selection == 1:
                self._enter_network_menu()
            elif self.menu_selection == 2:
                self.state.set(GameState.HELP)
            else:
                self.running = False

    def _enter_network_menu(self):
        if not has_network_support():
            self.network_error_msg = "缺少依赖: pip install websockets"
            return
        self.state.set(GameState.NETWORK_MENU)
        self._init_net_buffers()
        self.net_username_buffer = ""
        self.net_menu_selected_field = 0
        self.network_error_msg = ""

    def _handle_help_key(self, event):
        if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
            self.state.set(GameState.MENU)

    def _handle_game_over_key(self, event):
        if event.key == pygame.K_RETURN:
            self._start_game()
        elif event.key == pygame.K_ESCAPE:
            self.running = False

    def _handle_single_playing_key(self, event):
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
            if self.state.is_paused():
                # Resume
                self.state.set(GameState.PLAYING)
                self.pause_selection = 0
            else:
                # Pause
                self.state.set(GameState.PAUSED)
                self.pause_selection = 0
        elif self.state.is_paused():
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.pause_selection = (self.pause_selection - 1) % 2
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.pause_selection = (self.pause_selection + 1) % 2
            elif event.key == pygame.K_RETURN:
                if self.pause_selection == 0:
                    # Resume
                    self.state.set(GameState.PLAYING)
                    self.pause_selection = 0
                else:
                    # Quit to menu with fade
                    self.fade_alpha = 0
                    self.fade_state = "fade_out"
                    self.fade_target = GameState.MENU
                    self._cleanup_game_state()

    def _handle_network_playing_key(self, event):
        if self.opponent_disconnected:
            if event.key == pygame.K_RETURN:
                # 对手已断线，返回大厅
                self.opponent_disconnected = False
                if self.net_client:
                    self.net_client.leave_room()
                self.current_room = None
                self.state.set(GameState.LOBBY)
            return
        if event.key == pygame.K_ESCAPE:
            # 退出网络对战，回到大厅
            self.state.set(GameState.LOBBY)
            if self.net_client:
                self.net_client.leave_room()

    def _handle_network_game_over_key(self, event):
        """网络对战结束后的按键处理"""
        if event.key == pygame.K_RETURN:
            # 返回大厅
            if self.net_client:
                self.net_client.leave_room()
            self.current_room = None
            self.state.set(GameState.LOBBY)
        elif event.key == pygame.K_ESCAPE:
            self.running = False

    # ── 联网菜单键盘处理 ──────────────────────────────────────────────

    def _handle_network_menu_key(self, event):
        if event.key == pygame.K_ESCAPE:
            self.state.set(GameState.MENU)
            return

        if event.key == pygame.K_TAB:
            self.net_menu_selected_field = (self.net_menu_selected_field + 1) % 3
            return

        if event.key == pygame.K_RETURN:
            # 解析并连接
            username = self.net_username_buffer.strip()
            if not username:
                self.network_error_msg = "请输入用户名"
                return
            try:
                self.server_host = self.net_host_buffer.strip() or DEFAULT_HOST
                self.server_port = int(self.net_port_buffer.strip() or str(DEFAULT_PORT))
            except ValueError:
                self.network_error_msg = "端口号格式错误"
                return

            self.state.set(GameState.CONNECTING)
            self._setup_net_client(username)
            return

        # 文本输入
        if event.key == pygame.K_BACKSPACE:
            if self.net_menu_selected_field == 0:
                self.net_username_buffer = self.net_username_buffer[:-1]
            elif self.net_menu_selected_field == 1:
                self.net_host_buffer = self.net_host_buffer[:-1]
            else:
                self.net_port_buffer = self.net_port_buffer[:-1]
        elif event.unicode and event.unicode.isprintable():
            if self.net_menu_selected_field == 0:
                # Username: allow most printable chars, limit length
                if len(self.net_username_buffer) < 20:
                    self.net_username_buffer += event.unicode
            elif self.net_menu_selected_field == 1:
                # Host: allow most chars
                self.net_host_buffer += event.unicode
            else:
                # Port: digits only
                if event.unicode.isdigit() and len(self.net_port_buffer) < 6:
                        self.net_port_buffer += event.unicode

    # ── 大厅键盘处理 ──────────────────────────────────────────────────

    def _handle_lobby_key(self, event):
        if event.key == pygame.K_UP or event.key == pygame.K_w:
            self.lobby_selection = (self.lobby_selection - 1) % 4
            self.sound_manager.play("shoot")
        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
            self.lobby_selection = (self.lobby_selection + 1) % 4
            self.sound_manager.play("shoot")
        elif event.key == pygame.K_RETURN:
            if self.lobby_selection == 0:
                # 创建房间
                if self.net_client:
                    self.net_client.create_room()
            elif self.lobby_selection == 1:
                # 加入房间 — 如果 room_id_buffer 为空，跳过
                if self.room_id_buffer.strip() and self.net_client:
                    self.net_client.join_room(self.room_id_buffer.strip())
            elif self.lobby_selection == 2:
                # 快速匹配
                if self.net_client:
                    self.matchmaking_start_time = time.time()
                    self.net_client.join_matchmaking()
                    self.state.set(GameState.MATCHMAKING)
            else:
                # 返回主菜单
                self._cleanup_network()
                self.state.set(GameState.MENU)
        elif event.key == pygame.K_ESCAPE:
            self._cleanup_network()
            self.state.set(GameState.MENU)
        elif self.lobby_selection == 1:
            # 加入房间模式 — 文本输入
            if event.key == pygame.K_BACKSPACE:
                self.room_id_buffer = self.room_id_buffer[:-1]
            elif event.unicode and event.unicode.isprintable():
                self.room_id_buffer += event.unicode

    # ── 房间键盘处理 ──────────────────────────────────────────────────

    def _handle_room_key(self, event):
        if event.key == pygame.K_ESCAPE:
            if self.net_client:
                self.net_client.leave_room()
            self.current_room = None
            self.state.set(GameState.LOBBY)

    # ── 匹配键盘处理 ──────────────────────────────────────────────────

    def _handle_matchmaking_key(self, event):
        if event.key == pygame.K_ESCAPE:
            if self.net_client:
                self.net_client.leave_matchmaking()
            self.state.set(GameState.LOBBY)

    # ── 游戏控制 ──────────────────────────────────────────────────────

    def _start_game(self):
        """Reset and start a new single-player game with fade-in."""
        self.state.set(GameState.PLAYING)
        self.pause_selection = 0
        self._reset_game_state()
        self.fade_alpha = 255
        self.fade_state = "fade_in"
        self.fade_target = None

    def _start_network_game(self):
        """Start a network game (co-op mode)."""
        self.state.set(GameState.NETWORK_PLAYING)
        self._reset_game_state()
        self.opponent_score = 0
        self.coop_frame_counter = 0
        self.enemy_kill_queue.clear()
        # 合作模式：P1 左 1/4，P2 右 3/4
        offset = SCREEN_WIDTH // 4
        self.player.rect.centerx = offset if self.is_host else SCREEN_WIDTH - offset
        # 使用合作种子初始化随机序列
        if self.coop_seed:
            random.seed(self.coop_seed)

    def _reset_game_state(self):
        """Reset all sprite groups and game state for a new game."""
        self.bullets_group.empty()
        self.enemies_group.empty()
        self.explosions_group.empty()
        self.powerups_group.empty()
        self.enemy_bullets_group.empty()
        self.boss_group.empty()
        self.sub_weapons_group.empty()
        self.items_group.empty()
        self.player.reset()
        self.spawner.reset()
        self.spawner.on_level_up = self._on_level_up
        self.background.switch_to_level(0)
        self.background.set_boss_mode(False)
        self.boss_warning_active = False
        self.boss_warning_timer = 0
        self.laser_sweeps = []
        self.hit_flash_timer = 0
        self.game_stats["kills"] = 0
        self.game_stats["bosses_defeated"] = 0
        self.game_stats["items_used"] = 0
        self.game_stats["max_combo"] = 0
        self.game_stats["start_time"] = time.time()

    def _cleanup_game_state(self):
        """Clean up game state when quitting to menu (pause)."""
        self.bullets_group.empty()
        self.enemies_group.empty()
        self.explosions_group.empty()
        self.powerups_group.empty()
        self.enemy_bullets_group.empty()
        self.boss_group.empty()
        self.sub_weapons_group.empty()
        self.items_group.empty()
        self.player.reset()
        self.spawner.reset()
        self.spawner.on_level_up = self._on_level_up
        self.background.switch_to_level(0)
        self.background.set_boss_mode(False)

    def _on_level_up(self, level):
        """Called when spawner detects level change."""
        self.background.switch_to_level(level)

    # ── 帧更新 ────────────────────────────────────────────────────────

    def update(self):
        self._frame_count += 1

        # ── BGM 切换 ──
        if self.state.current == GameState.MENU or self.state.current == GameState.HELP:
            self.music_manager.play(MusicManager.TRACK_MENU)
        elif self.state.current in (GameState.PLAYING, GameState.NETWORK_PLAYING,
                                     GameState.PAUSED):
            if self.boss_group.sprite and self.boss_group.sprite.alive():
                self.music_manager.play(MusicManager.TRACK_BOSS)
            else:
                self.music_manager.play(MusicManager.TRACK_PLAY)
        else:
            self.music_manager.stop()

        # ── 画面过渡更新（在暂停/游戏结束等所有状态下运行）──
        if self.fade_state == "fade_out":
            self.fade_alpha += FADE_OUT_SPEED
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                if self.fade_target is not None:
                    self.state.set(self.fade_target)
                    self.fade_target = None
                self.fade_state = "hold"
                self.fade_hold_timer = FADE_PAUSE_FRAMES
        elif self.fade_state == "hold":
            self.fade_hold_timer -= 1
            if self.fade_hold_timer <= 0:
                self.fade_state = "fade_in"
        elif self.fade_state == "fade_in":
            self.fade_alpha = max(0, self.fade_alpha - FADE_IN_SPEED)
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.fade_state = None

        # ── 暂停状态：跳过所有游戏逻辑 ──
        if self.state.is_paused():
            return

        # ── 网络倒计时 ──
        if self.state.current == GameState.NETWORK_COUNTDOWN:
            elapsed = time.time() - self.countdown_timer
            new_count = 3 - int(elapsed)
            if new_count != self.countdown_number:
                self.countdown_number = max(0, new_count)
            if elapsed >= 3.5:  # 3 秒倒计时 + 0.5 秒显示 GO!
                self._start_network_game()
            return

        if self.state.is_playing():
            is_coop = (self.state.current == GameState.NETWORK_PLAYING)
            self.background.update()
            self._handle_shooting()
            self.player.update(pygame.key.get_pressed())
            self.bullets_group.update()

            # ── 引擎尾迹 ──
            if self.player.alive() and self._frame_count % ENGINE_TRAIL_RATE == 0:
                from game.graphics.particles import spawn_engine_trail
                spawn_engine_trail(
                    self.particles,
                    self.player.rect.centerx,
                    self.player.rect.bottom,
                )

            # 为追踪弹设置敌人引用
            for bullet in self.bullets_group:
                if bullet.weapon_type == "homing":
                    bullet.set_enemies_ref(self.enemies_group)

            # 时间减速效果: 减慢敌人和敌弹速度
            time_slow_active = self.player.has_time_slow()
            if time_slow_active:
                for enemy in self.enemies_group:
                    enemy.speed_multiplier = 0.5
            else:
                for enemy in self.enemies_group:
                    enemy.speed_multiplier = 1.0

            self.enemies_group.update()
            self.explosions_group.update()
            self.powerups_group.update()

            # 子武器更新
            self.sub_weapons_group.update()

            # 道具更新
            self.items_group.update()

            # Option 更新
            self.player.update_options()
            self.spawner.update(self.enemies_group,
                               self.shared_score if is_coop else self.player.score)

            # Enemy shooting
            for enemy in self.enemies_group:
                if enemy.should_shoot(0):
                    bullet = EnemyBullet(
                        enemy.rect.centerx, enemy.rect.centery,
                        self.player.rect.centerx, self.player.rect.centery,
                    )
                    self.enemy_bullets_group.add(bullet)

            # Apply time slow to enemy bullets
            bullet_slow = 0.5 if self.player.has_time_slow() else 1.0
            for ebullet in self.enemy_bullets_group:
                ebullet.speed_multiplier = bullet_slow

            self.enemy_bullets_group.update()

            # Boss spawn check — 带入场警告
            if self.spawner.check_boss_spawn(
                self.shared_score if is_coop else self.player.score,
            ):
                self.boss_warning_active = True
                self.boss_warning_timer = BOSS_WARNING_FRAMES
                self.sound_manager.play("game_over")
                self.screen_shake.shake(6.0)

            # Boss 警告计时
            if self.boss_warning_active:
                self.boss_warning_timer -= 1
                if self.boss_warning_timer <= 0:
                    self.boss_warning_active = False
                    boss = Boss()
                    self.boss_group.add(boss)
                    self.enemies_group.empty()
                    self.background.set_boss_mode(True)
                    self.sound_manager.play("game_over")

            # Boss update + shooting
            if self.boss_group.sprite and self.boss_group.sprite.alive():
                self.boss_group.update()
                boss = self.boss_group.sprite
                if boss.should_shoot():
                    vectors, metadata = boss.get_bullet_vectors(
                        self.player.rect.centerx, self.player.rect.centery
                    )
                    # Regular bullet vectors
                    for vx, vy in vectors:
                        bullet = EnemyBullet(
                            boss.rect.centerx, boss.rect.centery,
                            self.player.rect.centerx, self.player.rect.centery,
                        )
                        bullet.vx = vx
                        bullet.vy = vy
                        self.enemy_bullets_group.add(bullet)
                    # Laser sweep
                    if "laser_sweep" in metadata:
                        sweep = metadata["laser_sweep"]
                        self.laser_sweeps.append(sweep)
                    # Homing missiles
                    if "homing_missile" in metadata:
                        hm_cfg = metadata["homing_missile"]
                        for vx, vy in vectors:
                            missile = HomingMissile(
                                boss.rect.centerx, boss.rect.centery,
                                vx, vy,
                                lambda: self.player,
                                damage=hm_cfg["damage"],
                            )
                            self.enemy_bullets_group.add(missile)

            # Boss 召唤小兵
            if self.boss_group.sprite and self.boss_group.sprite.can_summon():
                boss = self.boss_group.sprite
                if boss.should_summon():
                    for x, y in boss.get_summon_positions():
                        from game.sprites.enemy import Enemy
                        minion = Enemy(BOSS_SUMMON_MINION_TYPE, x=int(x))
                        minion.rect.y = y
                        minion.rect.x = x
                        self.enemies_group.add(minion)

            # Laser sweep 更新
            self._update_laser_sweeps(self.player)

            # Collision detection — pass powerups_group for drops
            killed_info = []
            score = check_bullet_enemy_collisions(
                self.bullets_group, self.enemies_group, self.explosions_group, self.powerups_group,
                items_group=self.items_group,
                killed_info_out=killed_info if is_coop else None,
                player=self.player,  # 连击系统 + 道具分数倍率
            )
            # 子武器碰撞
            sub_score = check_sub_weapon_collisions(
                self.sub_weapons_group, self.enemies_group, self.explosions_group,
            )
            score += sub_score
            if score > 0:
                self.player.score += score
                self.shared_score += score
                self.sound_manager.play("explosion")
                self.screen_shake.shake(3.0)

                # ── 击杀粒子 + 得分弹出 ──
                if killed_info:
                    from game.graphics.particles import (
                        spawn_enemy_death,
                        spawn_score_popup,
                    )
                    for eid, pts, ptype in killed_info:
                        if self.explosions_group:
                            last_exp = list(self.explosions_group)[-1]
                            ex, ey = last_exp.rect.centerx, last_exp.rect.centery
                        else:
                            ex, ey = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
                        spawn_enemy_death(self.particles, ex, ey,
                                          color=SPARK_COLOR_ENEMY)
                        spawn_score_popup(self.particles, ex, ey,
                                          f"+{pts}", color=(255, 255, 100))

                # 合作模式：逐个通知伙伴我方杀敌（附带单个敌机分值+道具）
                if is_coop and self.net_client and killed_info:
                    for eid, pts, ptype in killed_info:
                        self.net_client.send_enemy_killed(eid, pts, ptype)

            # 战斗统计：击杀 + 最大连击
            self.game_stats["kills"] += len(killed_info)
            self.game_stats["max_combo"] = max(self.game_stats["max_combo"], self.player.combo_count)

            # Power-up collection
            collected_type = check_player_powerup_collisions(self.player, self.powerups_group)
            if collected_type:
                if collected_type == "bomb":
                    # Bomb clears all enemies
                    for enemy in self.enemies_group:
                        Explosion(enemy.rect.centerx, enemy.rect.centery, self.explosions_group)
                    self.enemies_group.empty()
                    self.sound_manager.play("explosion")
                elif collected_type == "power":
                    self.player.apply_powerup("power")
                    self.sound_manager.play("level_up")
                elif collected_type == "option":
                    self.player.apply_powerup("option")
                    self.sound_manager.play("level_up")
                else:
                    self.player.apply_powerup(collected_type)
                    self.sound_manager.play("level_up")

            # ── 道具拾取粒子 ──
            if collected_type and hasattr(self, 'particles'):
                from game.graphics.particles import spawn_pickup_ring
                spawn_pickup_ring(self.particles, self.player.rect.centerx,
                                  self.player.rect.centery)

            # ── 道具拾取碰撞 ──
            collected_item = check_player_item_collisions(self.player, self.items_group)
            if collected_item:
                self.sound_manager.play("level_up")
                if hasattr(self, 'particles'):
                    from game.graphics.particles import spawn_pickup_ring
                    spawn_pickup_ring(self.particles, self.player.rect.centerx,
                                      self.player.rect.centery)

            hit = check_player_enemy_collisions(
                self.player, self.enemies_group, self.explosions_group
            )
            if hit:
                self.sound_manager.play("hit")
                self.screen_shake.shake(SHAKE_HIT_INTENSITY)
                self.hit_flash_timer = HIT_FLASH_FRAMES
                if self.state.current == GameState.NETWORK_PLAYING:
                    # 合作模式：从共享生命池扣减
                    self.shared_lives -= 1
                    if self.shared_lives > 0:
                        self.player.lives = max(self.player.lives, 1)
                        self.player.invincible_timer = PLAYER_INVINCIBLE_FRAMES
                if self.player.lives <= 0:
                    self._on_player_death()

            # Enemy bullet hits player
            enemy_bullet_hit = check_enemy_bullet_player_collisions(
                self.player, self.enemy_bullets_group, self.explosions_group
            )
            if enemy_bullet_hit:
                self.sound_manager.play("hit")
                self.screen_shake.shake(SHAKE_HIT_INTENSITY)
                self.hit_flash_timer = HIT_FLASH_FRAMES
                if self.state.current == GameState.NETWORK_PLAYING:
                    # 合作模式：从共享生命池扣减
                    self.shared_lives -= 1
                    if self.shared_lives > 0:
                        self.player.lives = max(self.player.lives, 1)
                        self.player.invincible_timer = PLAYER_INVINCIBLE_FRAMES
                if self.player.lives <= 0:
                    self._on_player_death()

            # Bullet-Boss collision
            if self.boss_group.sprite and self.boss_group.sprite.alive():
                boss = self.boss_group.sprite
                boss_hit_by = pygame.sprite.spritecollide(boss, self.bullets_group, False)
                for bullet in boss_hit_by:
                    bullet_damage = getattr(bullet, 'damage', 1)
                    # ── Boss 受击粒子 ──
                    from game.graphics.particles import spawn_boss_hit
                    spawn_boss_hit(self.particles,
                                   bullet.rect.centerx, bullet.rect.centery)
                    destroyed = boss.take_damage(bullet_damage)
                    if not getattr(bullet, 'piercing', False):
                        bullet.kill()
                    if destroyed:
                        self.player.score += boss.score_value
                        self.game_stats["bosses_defeated"] += 1
                        self.game_stats["kills"] += 1  # count boss as a kill
                        # Multi-stage shake on boss defeat
                        for intensity in SHAKE_BOSS_DEFEAT:
                            self.screen_shake.shake(intensity)
                        for _ in range(5):
                            Explosion(
                                boss.rect.centerx + random.randint(-30, 30),
                                boss.rect.centery + random.randint(-30, 30),
                                self.explosions_group,
                            )
                        boss.kill()
                        self.spawner.boss_active = False
                        self.background.set_boss_mode(False)
                        self.sound_manager.play("explosion")
                        self.sound_manager.play("level_up")
                        self.screen_shake.shake(10.0)
                    break

            self.screen_shake.update()
            # ── 粒子系统更新 ──
            self.particles.update()
            # 网络对战：检测对手断线 → 暂停游戏显示断线提示
            if self.state.current == GameState.NETWORK_PLAYING and self.opponent_disconnected:
                # 游戏暂停，等待用户按 ENTER
                pass

        # 画面过渡更新（在所有状态下运行）
        if self.fade_state == "fade_out":
            self.fade_alpha += FADE_OUT_SPEED
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                if self.fade_target is not None:
                    self.state.set(self.fade_target)
                    self.fade_target = None
                self.fade_state = "hold"
                self.fade_hold_timer = FADE_PAUSE_FRAMES
        elif self.fade_state == "hold":
            self.fade_hold_timer -= 1
            if self.fade_hold_timer <= 0:
                self.fade_state = "fade_in"
        elif self.fade_state == "fade_in":
            self.fade_alpha -= FADE_IN_SPEED
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.fade_state = None

        # 网络对战：合作模式同步（在 playing 状态外运行）
        if self.state.current == GameState.NETWORK_PLAYING and self.net_client:
            self.coop_frame_counter += 1
            if self.coop_frame_counter % 3 == 0:
                self.net_client.send_player_state(
                    self.player.rect.centerx,
                    self.player.rect.centery,
                    self.shared_lives,
                    self.shared_score,
                )

            if self.enemy_kill_queue:
                to_kill = set(self.enemy_kill_queue)
                self.enemy_kill_queue.clear()
                for enemy in list(self.enemies_group):
                    if getattr(enemy, 'eid', None) in to_kill:
                        Explosion(enemy.rect.centerx, enemy.rect.centery,
                                  self.explosions_group)
                        enemy.kill()

            tx = self.partner_state.get("target_x", 0)
            ty = self.partner_state.get("target_y", 0)
            cx = self.partner_state.get("x", 0)
            cy = self.partner_state.get("y", 0)
            self.partner_state["x"] = cx + (tx - cx) * 0.35
            self.partner_state["y"] = cy + (ty - cy) * 0.35

            self._update_partner_bullets()

            if self.is_host and self.coop_frame_counter % 6 == 0:
                enemy_list = []
                for e in self.enemies_group:
                    eid = getattr(e, "eid", None)
                    if eid is not None:
                        enemy_list.append({"eid": eid, "x": e.rect.x, "y": e.rect.y})
                if enemy_list:
                    self.net_client.send_enemy_snapshot(enemy_list)

        # 合作模式：共享生命池逻辑
        if self.state.current == GameState.NETWORK_PLAYING and self.shared_lives <= 0:
                self._on_player_death()

        # 网络对战：检测对手断线
        if self.state.current == GameState.NETWORK_PLAYING and self.opponent_disconnected:
            pass

    def _update_partner_bullets(self):
        """更新伙伴子弹位置（和玩家子弹一样射到顶）"""
        alive = []
        for b in self.partner_bullets:
            b[1] += BULLET_SPEED
            b[3] -= 1
            if b[3] > 0 and b[1] > -20:
                alive.append(b)
        self.partner_bullets = alive

    def _get_partner_sprite(self):
        """创建伙伴飞船精灵（淡紫色tint，区别于自己的青蓝色）"""
        from game.graphics.pixel_art import create_player_ship
        if not hasattr(self, '_partner_img') or self._partner_img is None:
            ship = create_player_ship(scale=3)
            # Tint to purple
            pxarray = pygame.PixelArray(ship)
            for y in range(ship.get_height()):
                for x in range(ship.get_width()):
                    c = ship.unmap_rgb(pxarray[x, y])
                    if c.a > 0 and (c.r > 0 or c.g > 0 or c.b > 0):
                        pxarray[x, y] = (min(255, c.r + 80), c.g // 2, min(255, c.b + 60), c.a)
            del pxarray
            self._partner_img = ship
        return self._partner_img

    def _update_laser_sweeps(self, player):
        """Update active laser sweeps and check collision with player."""
        alive = []
        for sweep in self.laser_sweeps:
            x = sweep["start_x"]
            y = sweep["y"]
            speed = sweep["speed"]
            direction = sweep["direction"]
            aim_frames = sweep.get("aim_frames", 20)

            if aim_frames > 0:
                # Still aiming: store for draw but don't move yet
                sweep["aim_frames"] = aim_frames - 1
                sweep["current_x"] = x
                alive.append(sweep)
            else:
                # Beam moving
                x += direction * speed
                sweep["current_x"] = x
                # Check collision with player
                if (player and player.alive() and not player.invincible and
                        abs(player.rect.centery - y) < 20 and
                        abs(player.rect.centerx - x) < BOSS_LASER_WIDTH + 10):
                    # Hit player
                    pass  # collision handled by enemy_bullet group already
                # Remove if off-screen
                if 0 < x < SCREEN_WIDTH:
                    alive.append(sweep)
        self.laser_sweeps = alive

    def _on_player_death(self):
        """Handle player death with fade transition."""
        from game.highscore import HighScore
        if self.state.current == GameState.PLAYING:
            HighScore.save_if_beaten(self.player.score)
            self.game_stats["start_time"] = time.time()  # freeze elapsed time
            self.fade_state = "fade_out"
            self.fade_target = GameState.GAME_OVER
        elif self.state.current == GameState.NETWORK_PLAYING:
            self.state.set(GameState.NETWORK_GAME_OVER)
        self.sound_manager.play("game_over")

    def _handle_resize(self, new_w, new_h):
        """Maintain 2:3 aspect ratio on window resize."""
        scale_w = new_w // SCREEN_WIDTH
        scale_h = new_h // SCREEN_HEIGHT
        self.scale_factor = max(1, min(scale_w, scale_h))
        self.display_width = SCREEN_WIDTH * self.scale_factor
        self.display_height = SCREEN_HEIGHT * self.scale_factor
        self.screen = pygame.display.set_mode(
            (self.display_width, self.display_height),
            pygame.RESIZABLE,
        )

    def _handle_shooting(self):
        """Enhanced shooting logic: continuous fire (Space), charge (Shift), sub-weapon (X), items (Ctrl)."""
        keys = pygame.key.get_pressed()
        space_held = keys[pygame.K_SPACE] or keys[pygame.K_z]
        shift_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        x_held = keys[pygame.K_x]
        ctrl_held = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]

        # ── 使用道具 (Ctrl) ──
        if ctrl_held and self.player.has_item() and self.player.inventory_cooldown == 0:
            result = self.player.use_item()
            if result is not None:
                item_type, _ = result
                effect = self.player.activate_item_effect(item_type)
                self.game_stats["items_used"] += 1
                self._apply_item_effect(effect)

        # ── 武器切换 (Q/E) ──
        if keys[pygame.K_q] and self._wpn_switch_cooldown <= 0:
            self.player.switch_weapon(-1)
            self._wpn_switch_cooldown = 15
        elif keys[pygame.K_e] and self._wpn_switch_cooldown <= 0:
            self.player.switch_weapon(1)
            self._wpn_switch_cooldown = 15
        elif self._wpn_switch_cooldown > 0:
            self._wpn_switch_cooldown -= 1

        # ── 子武器 (X) ──
        if x_held and self.player.can_fire_sub_weapon():
            sub_type, sub_config = self.player.fire_sub_weapon()
            self._fire_sub_weapon(sub_type, sub_config)

        # ── 主武器（空格）— 长按持续自动射击 ──
        self.player.is_firing = False
        if space_held:
            if self.player.can_shoot():
                self._fire_primary()
            self.player.is_firing = True

        # ── 蓄力射击（Shift）— 按住蓄力，松开释放 ──
        if shift_held:
            if not self.player.is_charging:
                self.player.start_charge()
            self.player.continue_charge()
        else:
            if self.player.is_charging:
                released, tier = self.player.release_charge()
                if released:
                    self._fire_charge(tier)

    def _fire_primary(self):
        """Fire primary weapon based on current weapon type + level."""
        if not self.player.can_shoot():
            return

        config = self.player.get_weapon_config()
        wt = self.player.active_weapon

        # Calculate cooldown
        cooldown = int(PLAYER_SHOOT_COOLDOWN * config["cooldown_mult"])
        if self.player.has_powerup("rapid"):
            cooldown = max(3, cooldown // 2)
        if self.player.has_combo_buff():
            cooldown = max(2, int(cooldown * 0.7))

        self.player.shoot()
        self.player.shoot_cooldown = cooldown
        self.player.is_firing = True

        # ── 枪口火花 ──
        from game.graphics.particles import spawn_muzzle_flash
        spawn_muzzle_flash(self.particles, self.player.rect.centerx, self.player.rect.top)

        count = config["count"]
        spread = config["spread_angle"]

        # Create bullet(s)
        for i in range(count):
            if count == 1:
                offset_x = 0
            else:
                angle_offset = -spread / 2 + (spread / (count - 1)) * i
                offset_x = math.tan(math.radians(angle_offset)) * 15

            bullet = Bullet(
                self.player.rect.centerx + int(offset_x),
                self.player.rect.top,
                wt, self.player.get_weapon_level(),
                vx=offset_x * 0.08 if offset_x != 0 else 0,
            )
            self.bullets_group.add(bullet)

        # ● 连击奖励：额外发射一发大子弹
        if self.player.has_combo_buff():
            bonus = Bullet(
                self.player.rect.centerx, self.player.rect.top,
                wt, self.player.get_weapon_level(),
                is_combo_bonus=True
            )
            self.bullets_group.add(bonus)

        # ● Option 辅助机同步射击
        for opt in self.player.options:
            ox, oy = opt.get_shoot_position()
            obullet = Bullet(ox, oy, wt, self.player.get_weapon_level())
            self.bullets_group.add(obullet)

        self.sound_manager.play("shoot")

        # Network coop sync
        if self.state.current == GameState.NETWORK_PLAYING and self.net_client:
            is_triple = count >= 3
            self.net_client.send_bullet_spawned(
                self.player.rect.centerx, self.player.rect.top, is_triple,
            )

    def _fire_charge(self, tier):
        """Fire a charged shot."""
        if tier < 1 or tier > len(CHARGE_TIERS):
            return

        tier_config = CHARGE_TIERS[tier - 1]
        wt = self.player.active_weapon
        wpn_config = self.player.get_weapon_config()

        damage = wpn_config["damage"] * tier_config["damage_mult"]
        speed = BULLET_SPEED * tier_config["speed_mult"]

        bullet = Bullet(
            self.player.rect.centerx,
            self.player.rect.top,
            wt, self.player.get_weapon_level(),
            is_charged=True,
            charge_tier=tier,
            custom_damage=damage,
            custom_speed=speed,
            piercing=tier_config.get("piercing", False),
        )
        self.bullets_group.add(bullet)

        # 蓄力射击也触发 Option
        for opt in self.player.options:
            ox, oy = opt.get_shoot_position()
            obullet = Bullet(
                ox, oy, wt, self.player.get_weapon_level(),
                is_charged=True,
                charge_tier=tier,
                custom_damage=damage * 0.5,
                custom_speed=speed,
            )
            self.bullets_group.add(obullet)

        self.sound_manager.play("shoot")

    def _fire_sub_weapon(self, sub_type, config):
        """Fire sub-weapon projectile."""
        proj = SubWeaponProjectile(
            self.player.rect.centerx,
            self.player.rect.top,
            sub_type, config,
            enemies_group=self.enemies_group,
        )
        self.sub_weapons_group.add(proj)
        self.sound_manager.play("shoot")

    # ── 道具系统效果处理 ────────────────────────────────────────────────

    def _apply_item_effect(self, effect):
        """Apply the effect of a consumed item."""
        effect.get("type")

        if effect.get("clear_enemies"):
            # Full screen bomb: clear all enemies and enemy bullets
            for enemy in self.enemies_group:
                Explosion(enemy.rect.centerx, enemy.rect.centery, self.explosions_group)
            self.enemies_group.empty()
            self.enemy_bullets_group.empty()
            self.sound_manager.play("explosion")

        if effect.get("clear_bullets"):
            self.enemy_bullets_group.empty()

        if effect.get("pull_enemies"):
            # Gravity bomb: pull + damage
            damage_score = apply_gravity_bomb(
                self.enemies_group, self.explosions_group,
            )
            self.player.score += damage_score
            self.shared_score += damage_score
            self.sound_manager.play("explosion")

        if effect.get("healed"):
            self.sound_manager.play("level_up")

        # time_slow, reflect_shield, score_boost — handled by player._update_item_timers

    # ── 绘制 ────────────────────────────────────────────────────────────

    def draw(self):
        # Clear virtual surface
        self.virtual_surf.fill(BLACK)

        current = self.state.current

        if current == GameState.MENU:
            # Ensure menu particles exist
            self.background.init_menu_particles()
            self.background.update_menu_particles()
            draw_menu_screen(self.virtual_surf, self.menu_selection,
                             particles=None, frame_count=self._frame_count)
            self.background.draw_menu_particles(self.virtual_surf)

        elif current == GameState.HELP:
            draw_help_screen(self.virtual_surf)

        elif current == GameState.NETWORK_MENU:
            draw_network_menu_screen(
                self.virtual_surf,
                self.net_username_buffer,
                self.net_host_buffer,
                self.net_port_buffer,
                self.net_menu_selected_field,
            )
            if self.network_error_msg:
                err_font = pygame.font.Font(None, 22)
                err_surf = err_font.render(self.network_error_msg, True, RED)
                err_rect = err_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
                self.virtual_surf.blit(err_surf, err_rect)

        elif current == GameState.CONNECTING:
            draw_connecting_screen(self.virtual_surf, self.network_error_msg)

        elif current == GameState.LOBBY:
            draw_lobby_screen(
                self.virtual_surf,
                self.net_client.username if self.net_client else "???",
                self.net_client.player_id if self.net_client else "",
                self.online_count,
                self.room_id_buffer,
                self.lobby_selection,
            )
            if self.network_error_msg:
                err_font = pygame.font.Font(None, 20)
                err_surf = err_font.render(self.network_error_msg, True, RED)
                self.virtual_surf.blit(err_surf, (15, SCREEN_HEIGHT - 50))

        elif current == GameState.ROOM:
            username = self.net_client.username if self.net_client else ""
            draw_room_screen(self.virtual_surf, self.current_room or {}, username)

        elif current == GameState.MATCHMAKING:
            elapsed = time.time() - self.matchmaking_start_time
            draw_matchmaking_screen(self.virtual_surf, elapsed)

        elif current == GameState.NETWORK_COUNTDOWN:
            draw_network_countdown_screen(
                self.virtual_surf,
                self.countdown_number,
                self.opponent_username,
            )

        elif current == GameState.GAME_OVER:
            self.background.draw(self.virtual_surf)
            draw_game_over_screen(self.virtual_surf, self.player.score)
            draw_game_over_stats(self.virtual_surf, self.game_stats)

        elif current == GameState.NETWORK_GAME_OVER:
            pname = self.net_client.username if self.net_client else "我"
            draw_coop_game_over_screen(
                self.virtual_surf,
                self.shared_score,
                pname,
                self.opponent_username,
            )

        elif current == GameState.NETWORK_PLAYING:
            self.background.draw(self.virtual_surf)
            self.enemies_group.draw(self.virtual_surf)
            self.bullets_group.draw(self.virtual_surf)
            self.sub_weapons_group.draw(self.virtual_surf)
            self.powerups_group.draw(self.virtual_surf)
            self.items_group.draw(self.virtual_surf)
            self.enemy_bullets_group.draw(self.virtual_surf)
            self.boss_group.draw(self.virtual_surf)

            # 绘制伙伴飞船（淡紫色tint）+ 名字标签
            px, py = self.partner_state.get("x", 0), self.partner_state.get("y", 0)
            if px > 0 and py > 0:
                partner_img = self._get_partner_sprite()
                pr = partner_img.get_rect(center=(px, py))
                self.virtual_surf.blit(partner_img, pr)
                # 名字标签
                name_font = pygame.font.Font(None, 16)
                name_surf = name_font.render(self.opponent_username, True, (180, 140, 255))
                name_rect = name_surf.get_rect(center=(px, py - 28))
                self.virtual_surf.blit(name_surf, name_rect)

            # 绘制伙伴子弹（淡紫色弹道）
            for bx, by, _, _ in self.partner_bullets:
                pygame.draw.rect(self.virtual_surf, (200, 130, 255),
                                 (bx - 2, by - 6, 4, 12))

            self.player_group.add(self.player)
            self.player_group.draw(self.virtual_surf)
            for explosion in self.explosions_group:
                explosion.draw(self.virtual_surf)
            draw_network_game_hud(
                self.virtual_surf,
                self.shared_score,
                self.shared_lives,
                self.spawner.current_level,
                self.player.active_powerups,
                opponent_name=self.opponent_username,
                opponent_score=self.partner_state.get("score", 0),
                opponent_lives=self.partner_state.get("lives", 0),
            )

            # 对手断线叠加层
            if self.opponent_disconnected:
                draw_disconnected_overlay(self.virtual_surf)

        elif current == GameState.PLAYING or current == GameState.PAUSED:
            self.background.draw(self.virtual_surf)
            self.enemies_group.draw(self.virtual_surf)
            self.bullets_group.draw(self.virtual_surf)
            self.sub_weapons_group.draw(self.virtual_surf)
            self.powerups_group.draw(self.virtual_surf)
            self.items_group.draw(self.virtual_surf)
            self.enemy_bullets_group.draw(self.virtual_surf)
            self.boss_group.draw(self.virtual_surf)
            # Homing missile trails (drawn behind missiles)
            for ebullet in self.enemy_bullets_group:
                if hasattr(ebullet, 'get_trail'):
                    pts = ebullet.get_trail()
                    for i in range(len(pts) - 1):
                        alpha = int(100 * (i / len(pts)))
                        pygame.draw.line(self.virtual_surf, (255, 150, 50, alpha),
                                         pts[i], pts[i + 1], 2)
            self.player_group.add(self.player)
            self.player_group.draw(self.virtual_surf)
            # Option 辅助机渲染
            for opt in self.player.options:
                self.virtual_surf.blit(opt.image, opt.rect)
            for explosion in self.explosions_group:
                explosion.draw(self.virtual_surf)
            draw_hud(
                self.virtual_surf,
                self.player.score,
                self.player.lives,
                self.spawner.current_level,
                self.player.active_powerups,
                player=self.player,
                muted=self.music_manager.muted,
                particles=self.particles,
            )
            # ── 浮动得分文字 ──
            from game.graphics.hud import draw_combo_popup, draw_score_popups
            draw_score_popups(self.virtual_surf, self.particles)
            # ── 连击弹出 ──
            if self.player.combo_tier > 0 and self.player.combo_buff_timer > 0:
                draw_combo_popup(self.virtual_surf, self.player.combo_tier,
                                 COMBO_POPUP_LIFETIME - self.player.combo_buff_timer)
            # Boss 血条
            if self.boss_group.sprite:
                draw_boss_health_bar(self.virtual_surf, self.boss_group.sprite)
            # Boss 入场警告
            if self.boss_warning_active:
                draw_boss_warning(self.virtual_surf, self.boss_warning_timer)
            # 激光扫描
            draw_laser_sweeps(self.virtual_surf, self.laser_sweeps)
            # 红闪
            draw_hit_flash(self.virtual_surf, self.hit_flash_timer)
            if current == GameState.PAUSED:
                draw_pause_screen(self.virtual_surf, self.pause_selection)

        # 画面过渡叠加层（在所有状态绘制完成后）
        draw_fade_overlay(self.virtual_surf, self.fade_alpha)

        # Scale virtual surface to display window — apply screen shake offset
        shake_dx, shake_dy = self.screen_shake.get_offset()
        if shake_dx != 0 or shake_dy != 0:
            shake_surf = pygame.Surface(
                (SCREEN_WIDTH + abs(shake_dx) * 2, SCREEN_HEIGHT + abs(shake_dy) * 2),
                pygame.SRCALPHA,
            )
            shake_surf.blit(self.virtual_surf, (shake_dx, shake_dy))
            # Crop to viewport
            crop = shake_surf.subsurface(
                (max(0, -shake_dx), max(0, -shake_dy), SCREEN_WIDTH, SCREEN_HEIGHT)
            )
            scaled = pygame.transform.scale(crop, (self.display_width, self.display_height))
        else:
            scaled = pygame.transform.scale(self.virtual_surf, (self.display_width, self.display_height))
        self.screen.blit(scaled, (0, 0))


if __name__ == "__main__":
    Game().run()