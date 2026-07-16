# main.py
import pygame
import random
import sys
import time
from typing import Optional
from game.settings import *
from game.state import GameState
from game.sprites.player import Player
from game.sprites.bullet import Bullet
from game.sprites.explosion import Explosion
from game.sprites.enemy_bullet import EnemyBullet
from game.sprites.boss import Boss
from game.systems.spawner import Spawner
from game.systems.collision import (
    check_bullet_enemy_collisions,
    check_player_enemy_collisions,
    check_player_powerup_collisions,
    check_enemy_bullet_player_collisions,
)
from game.graphics.hud import (
    draw_hud,
    draw_menu_screen,
    draw_game_over_screen,
    draw_help_screen,
    draw_network_menu_screen,
    draw_lobby_screen,
    draw_room_screen,
    draw_matchmaking_screen,
    draw_connecting_screen,
    draw_network_game_hud,
    draw_network_game_over_screen,
    draw_network_countdown_screen,
    draw_disconnected_overlay,
)
from game.graphics.screen_shake import ScreenShake
from game.sounds.sound_manager import SoundManager
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

        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.player_group = pygame.sprite.GroupSingle()
        self.bullets_group = pygame.sprite.Group()
        self.enemies_group = pygame.sprite.Group()
        self.explosions_group = pygame.sprite.Group()
        self.powerups_group = pygame.sprite.Group()
        self.enemy_bullets_group = pygame.sprite.Group()
        self.boss_group = pygame.sprite.GroupSingle()

        # Game systems
        self.player = Player()
        self.spawner = Spawner()
        self.sound_manager = SoundManager()

        # Background
        from game.graphics.background import LevelBackgroundManager
        self.background = LevelBackgroundManager()
        self.screen_shake = ScreenShake()

        # ── 网络模块 ────────────────────────────────────────────────────
        self.net_client: Optional["NetworkClient"] = None
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
        self.countdown_number = 0
        self.countdown_timer = 0.0
        self.matchmaking_start_time = 0
        self.network_error_msg = ""
        self.online_count = 0

        # 注册网络事件
        self._register_network_callbacks()

    def _init_net_buffers(self):
        self.net_host_buffer = str(self.server_host)
        self.net_port_buffer = str(self.server_port)

    def _register_network_callbacks(self):
        """注册网络事件回调"""
        # 会在每次状态切换时重新注册，以避免残留引用
        pass

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
        self.state.set(GameState.ROOM)

    def _on_room_joined(self, data):
        self.current_room = data.get("room", {})
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

    def _on_game_start(self, data):
        # 先进入倒计时，3 秒后开始游戏
        self.state.set(GameState.NETWORK_COUNTDOWN)
        self.countdown_number = 3
        self.countdown_timer = time.time()
        self.opponent_disconnected = False
        self._reset_game_state()

    def _on_opponent_input(self, data):
        # Handle opponent game input
        input_data = data.get("data", {})
        if "score" in input_data:
            self.opponent_score = input_data["score"]
        if "lives" in input_data:
            self.opponent_lives = input_data["lives"]

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
        self.net_client.on(NetworkEvent.PLAYER_LIST, self._on_player_list)

        self.net_client.connect(username)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
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
                if self.state.is_menu():
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
                elif self.state.is_playing():
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
        if event.key == pygame.K_ESCAPE:
            self.running = False

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
                if event.unicode.isdigit():
                    if len(self.net_port_buffer) < 6:
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
        """Reset and start a new single-player game."""
        self.state.set(GameState.PLAYING)
        self._reset_game_state()

    def _start_network_game(self):
        """Start a network game."""
        self.state.set(GameState.NETWORK_PLAYING)
        self._reset_game_state()
        self.opponent_score = 0

    def _reset_game_state(self):
        """Reset all sprite groups and game state for a new game."""
        self.bullets_group.empty()
        self.enemies_group.empty()
        self.explosions_group.empty()
        self.powerups_group.empty()
        self.enemy_bullets_group.empty()
        self.boss_group.empty()
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
            self.background.update()
            self._handle_shooting()
            self.player.update(pygame.key.get_pressed())
            self.bullets_group.update()
            self.enemies_group.update()
            self.explosions_group.update()
            self.powerups_group.update()
            self.spawner.update(self.enemies_group, self.player.score)

            # Enemy shooting
            for enemy in self.enemies_group:
                if enemy.should_shoot(0):
                    bullet = EnemyBullet(
                        enemy.rect.centerx, enemy.rect.centery,
                        self.player.rect.centerx, self.player.rect.centery,
                    )
                    self.enemy_bullets_group.add(bullet)
            self.enemy_bullets_group.update()

            # Boss spawn check
            if self.spawner.check_boss_spawn(self.player.score):
                boss = Boss()
                self.boss_group.add(boss)
                # Clear regular enemies for dramatic effect
                self.enemies_group.empty()
                self.background.set_boss_mode(True)
                self.sound_manager.play("game_over")
                self.screen_shake.shake(8.0)

            # Boss update + shooting
            if self.boss_group.sprite and self.boss_group.sprite.is_alive():
                self.boss_group.update()
                boss = self.boss_group.sprite
                if boss.should_shoot():
                    vectors = boss.get_bullet_vectors(
                        self.player.rect.centerx, self.player.rect.centery
                    )
                    for vx, vy in vectors:
                        bullet = EnemyBullet(
                            boss.rect.centerx, boss.rect.centery,
                            self.player.rect.centerx, self.player.rect.centery,
                        )
                        bullet.vx = vx
                        bullet.vy = vy
                        self.enemy_bullets_group.add(bullet)

            # Collision detection — pass powerups_group for drops
            score = check_bullet_enemy_collisions(
                self.bullets_group, self.enemies_group, self.explosions_group, self.powerups_group
            )
            if score > 0:
                self.player.score += score
                self.sound_manager.play("explosion")
                self.screen_shake.shake(3.0)

            # Power-up collection
            collected_type = check_player_powerup_collisions(self.player, self.powerups_group)
            if collected_type:
                if collected_type == "bomb":
                    # Bomb clears all enemies
                    for enemy in self.enemies_group:
                        Explosion(enemy.rect.centerx, enemy.rect.centery, self.explosions_group)
                    self.enemies_group.empty()
                    self.sound_manager.play("explosion")
                else:
                    self.player.apply_powerup(collected_type)
                    self.sound_manager.play("level_up")

            hit = check_player_enemy_collisions(
                self.player, self.enemies_group, self.explosions_group
            )
            if hit:
                self.sound_manager.play("hit")
                self.screen_shake.shake(6.0)
                if self.player.lives <= 0:
                    self._on_player_death()

            # Enemy bullet hits player
            enemy_bullet_hit = check_enemy_bullet_player_collisions(
                self.player, self.enemy_bullets_group, self.explosions_group
            )
            if enemy_bullet_hit:
                self.sound_manager.play("hit")
                self.screen_shake.shake(5.0)
                if self.player.lives <= 0:
                    self._on_player_death()

            # Bullet-Boss collision
            if self.boss_group.sprite and self.boss_group.sprite.is_alive():
                boss = self.boss_group.sprite
                boss_hit_by = pygame.sprite.spritecollide(boss, self.bullets_group, False)
                for bullet in boss_hit_by:
                    destroyed = boss.take_damage()
                    bullet.kill()
                    if destroyed:
                        self.player.score += boss.score_value
                        # Big explosion
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

            # 网络对战：发送分数给对手
            if self.state.current == GameState.NETWORK_PLAYING and self.net_client:
                self.net_client.send_game_input({
                    "score": self.player.score,
                    "lives": self.player.lives,
                })

            # 网络对战：检测对手断线 → 暂停游戏显示断线提示
            if self.state.current == GameState.NETWORK_PLAYING and self.opponent_disconnected:
                # 游戏暂停，等待用户按 ENTER
                pass

    def _on_player_death(self):
        """Handle player death."""
        from game.highscore import HighScore
        if self.state.current == GameState.PLAYING:
            HighScore.save_if_beaten(self.player.score)
            self.state.set(GameState.GAME_OVER)
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
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_SPACE] or keys[pygame.K_z]) and self.player.can_shoot():
            cooldown = PLAYER_SHOOT_COOLDOWN
            if self.player.has_powerup("rapid"):
                cooldown = max(3, PLAYER_SHOOT_COOLDOWN // 2)

            self.player.shoot()
            self.player.shoot_cooldown = cooldown

            bullet = Bullet(self.player.rect.centerx, self.player.rect.top)
            self.bullets_group.add(bullet)

            if self.player.has_powerup("triple"):
                bullet_left = Bullet(self.player.rect.centerx - 12, self.player.rect.top)
                bullet_right = Bullet(self.player.rect.centerx + 12, self.player.rect.top)
                self.bullets_group.add(bullet_left, bullet_right)

            self.sound_manager.play("shoot")

    # ── 绘制 ────────────────────────────────────────────────────────────

    def draw(self):
        # Clear virtual surface
        self.virtual_surf.fill(BLACK)

        current = self.state.current

        if current == GameState.MENU:
            # 4-item menu: START, NETWORK GAME, HELP, EXIT
            draw_menu_screen(self.virtual_surf, self.menu_selection)

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

        elif current == GameState.NETWORK_GAME_OVER:
            won = self.player.score >= self.opponent_score if self.opponent_score > 0 else True
            draw_network_game_over_screen(
                self.virtual_surf,
                won,
                self.player.score,
                self.opponent_score,
                self.opponent_username,
            )

        elif current == GameState.NETWORK_PLAYING:
            self.background.draw(self.virtual_surf)
            self.enemies_group.draw(self.virtual_surf)
            self.bullets_group.draw(self.virtual_surf)
            self.powerups_group.draw(self.virtual_surf)
            self.enemy_bullets_group.draw(self.virtual_surf)
            self.boss_group.draw(self.virtual_surf)
            self.player_group.add(self.player)
            self.player_group.draw(self.virtual_surf)
            for explosion in self.explosions_group:
                explosion.draw(self.virtual_surf)
            draw_network_game_hud(
                self.virtual_surf,
                self.player.score,
                self.player.lives,
                self.spawner.current_level,
                self.player.active_powerups,
                opponent_name=self.opponent_username,
                opponent_score=self.opponent_score,
                opponent_lives=self.opponent_lives,
            )

            # 对手断线叠加层
            if self.opponent_disconnected:
                draw_disconnected_overlay(self.virtual_surf)

        elif current == GameState.PLAYING:
            self.background.draw(self.virtual_surf)
            self.enemies_group.draw(self.virtual_surf)
            self.bullets_group.draw(self.virtual_surf)
            self.powerups_group.draw(self.virtual_surf)
            self.enemy_bullets_group.draw(self.virtual_surf)
            self.boss_group.draw(self.virtual_surf)
            self.player_group.add(self.player)
            self.player_group.draw(self.virtual_surf)
            for explosion in self.explosions_group:
                explosion.draw(self.virtual_surf)
            draw_hud(
                self.virtual_surf,
                self.player.score,
                self.player.lives,
                self.spawner.current_level,
                self.player.active_powerups,
            )

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