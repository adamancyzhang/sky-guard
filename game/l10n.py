# game/l10n.py
"""Simple localization module — Chinese (zh) and English (en)."""

_STRINGS = {
    "en": {
        "title": "SKY GUARD",
        "subtitle": "~ PIXEL SHOOTER ~",
        "start_game": "START GAME",
        "help": "HELP",
        "exit": "EXIT",
        "home": "HOME",
        "game_over": "GAME OVER",
        "final_score": "FINAL SCORE: {}",
        "score": "SCORE: {}",
        "level": "LEVEL: {}",
        "lives": "LIVES: ",
        "restart_prompt": "PRESS ENTER TO RESTART  |  ESC TO QUIT",
        "menu_hint": "UP / DOWN to select  |  ENTER to confirm",
        "lang_toggle": "[Switch to 中文]",
        "controls_title": "=== CONTROLS ===",
        "controls_move": "Arrow Keys / WASD  -  Move",
        "controls_shoot": "Space / Z  -  Shoot",
        "controls_pause": "ESC  -  Quit game / Back",
        "items_title": "=== POWER-UPS ===",
        "item_shield": "Shield  -  Invincible for 5s (blue aura)",
        "item_rapid": "Rapid Fire  -  Double fire rate for 8s",
        "item_triple": "Triple Shot  -  3-way spread for 8s",
        "item_bomb": "Bomb  -  Destroy all enemies on screen",
        "item_speed": "Speed Boost  -  Faster move for 8s",
        "item_life": "Life  -  +1 extra life",
        "help_back": "Press ENTER or ESC to return",
        "help_title": "HOW TO PLAY",
    },
    "zh": {
        "title": "天穹守卫",
        "subtitle": "~ 像素射击 ~",
        "start_game": "开始游戏",
        "help": "帮助",
        "exit": "退出",
        "home": "主页",
        "game_over": "游戏结束",
        "final_score": "最终得分：{}",
        "score": "得分：{}",
        "level": "等级：{}",
        "lives": "生命：",
        "restart_prompt": "按 ENTER 重新开始  |  按 ESC 退出",
        "menu_hint": "↑/↓ 选择  |  ENTER 确认",
        "lang_toggle": "[English]",
        "controls_title": "=== 操作说明 ===",
        "controls_move": "方向键 / WASD  —  移动",
        "controls_shoot": "空格 / Z  —  射击",
        "controls_pause": "ESC  —  退出 / 返回",
        "items_title": "=== 道具说明 ===",
        "item_shield": "护盾  —  5秒无敌（蓝色光环）",
        "item_rapid": "速射  —  8秒双倍射速",
        "item_triple": "三连射  —  8秒三向散射",
        "item_bomb": "炸弹  —  消灭全屏敌人",
        "item_speed": "加速  —  8秒加速移动",
        "item_life": "生命  —  增加一条命",
        "help_back": "按 ENTER 或 ESC 返回",
        "help_title": "操作说明",
    },
}


class L10n:
    """Simple localization accessor."""
    _lang = "en"

    @classmethod
    def set_lang(cls, lang):
        if lang in _STRINGS:
            cls._lang = lang

    @classmethod
    def toggle(cls):
        cls._lang = "zh" if cls._lang == "en" else "en"

    @classmethod
    def lang(cls):
        return cls._lang

    @classmethod
    def _(cls, key, *args):
        """Get a localized string, optionally formatting."""
        val = _STRINGS[cls._lang].get(key, f"!{key}!")
        if args:
            return val.format(*args)
        return val