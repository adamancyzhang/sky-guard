# game/state.py

class GameState:
    """有限状态机管理游戏状态"""
    MENU = "menu"
    PLAYING = "playing"
    GAME_OVER = "game_over"

    def __init__(self):
        self.current = GameState.MENU
        self.transitioning = False
        self.transition_timer = 0

    def set(self, new_state):
        self.current = new_state

    def is_menu(self):
        return self.current == GameState.MENU

    def is_playing(self):
        return self.current == GameState.PLAYING

    def is_game_over(self):
        return self.current == GameState.GAME_OVER
