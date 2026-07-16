# game/state.py

class GameState:
    """Finite state machine for game state management."""
    MENU = "menu"
    PLAYING = "playing"
    GAME_OVER = "game_over"
    HELP = "help"

    # ── 网络对战新增状态 ──
    NETWORK_MENU = "network_menu"        # 联网主菜单（输入服务器地址）
    CONNECTING = "connecting"            # 正在连接服务器
    LOBBY = "lobby"                      # 大厅（创建/加入房间、匹配）
    MATCHMAKING = "matchmaking"          # 正在匹配
    ROOM = "room"                        # 在房间中等待对手
    NETWORK_COUNTDOWN = "network_countdown"  # 对局开始倒计时
    NETWORK_PLAYING = "network_playing"  # 网络对战中
    NETWORK_GAME_OVER = "network_game_over"  # 网络对战结果

    def __init__(self):
        self.current = GameState.MENU
        self.transitioning = False
        self.transition_timer = 0

    def set(self, new_state):
        self.current = new_state

    def is_menu(self):
        return self.current == GameState.MENU

    def is_playing(self):
        """Return True for any gameplay state (single-player or network)"""
        return self.current in (GameState.PLAYING, GameState.NETWORK_PLAYING)

    def is_game_over(self):
        return self.current == GameState.GAME_OVER

    def is_help(self):
        return self.current == GameState.HELP

    def is_network_state(self):
        """Return True if in any network-related state"""
        return self.current in (
            GameState.NETWORK_MENU,
            GameState.CONNECTING,
            GameState.LOBBY,
            GameState.MATCHMAKING,
            GameState.ROOM,
            GameState.NETWORK_PLAYING,
        )