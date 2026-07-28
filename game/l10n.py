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
        "highest_score": "HIGH SCORE: {}",
        "score": "SCORE: {}",
        "level": "LEVEL: {}",
        "lives": "LIVES: ",
        "restart_prompt": "PRESS ENTER TO RESTART  |  ESC TO QUIT",
        "restart_prompt_line1": "PRESS ENTER TO RESTART",
        "restart_prompt_line2": "ESC TO QUIT",
        "menu_hint": "UP / DOWN to select  |  ENTER to confirm",
        "lang_toggle": "[Switch to 中文]",
        "controls_title": "=== CONTROLS ===",
        "controls_move": "Arrow Keys / WASD  -  Move",
        "controls_shoot": "Space / Z  -  Continuous fire",
        "controls_weapon": "Q/E  -  Switch weapon",
        "controls_charge": "Shift  -  Charge shot (hold)",
        "controls_sub": "X  -  Sub-weapon",
        "controls_pause": "Esc/P  -  Pause / Resume",
        "items_title": "=== ITEMS ===",
        "powerups_title": "=== POWER-UPS ===",
        "item_shield": "Shield  -  Invincible for 5s (blue aura)",
        "item_rapid": "Rapid Fire  -  Double fire rate for 8s",
        "item_triple": "Triple Shot  -  3-way spread for 8s",
        "item_bomb": "Bomb  -  Destroy all enemies on screen",
        "item_speed": "Speed Boost  -  Faster move for 8s",
        "item_life": "Life  -  +1 extra life",
        "help_back": "Press ENTER or ESC to return",
        "help_title": "HOW TO PLAY",

        # ── Network mode (en) ──
        "network_game": "NETWORK GAME",
        "network_title": "NETWORK",
        "network_username": "Username:",
        "server_host": "Server Address:",
        "server_port": "Port:",
        "network_connect_hint": "ENTER to connect  |  TAB to switch fields",
        "network_back_hint": "ESC to go back",
        "player_info": "{} ({})",
        "online_count": "Online: {}",
        "lobby_title": "GAME LOBBY",
        "lobby_create_room": "CREATE ROOM",
        "lobby_join_room": "JOIN ROOM",
        "lobby_matchmaking": "QUICK MATCH",
        "lobby_back": "BACK TO MENU",
        "room_id_input": "Room ID: ",
        "lobby_hint": "↑/↓ select  |  ENTER confirm  |  ESC back",
        "room_title": "GAME ROOM",
        "room_share_hint": "Share Room ID with a friend!",
        "room_you": "(You)",
        "room_waiting": "Waiting for opponent...",
        "room_ready": "Ready! Game starting...",
        "room_leave_hint": "ESC to leave room",
        "matchmaking_title": "MATCHMAKING",
        "matchmaking_searching": "Searching for opponent",
        "matchmaking_cancel_hint": "ESC to cancel",
        "game_win": "YOU WIN!",
        "game_lose": "YOU LOSE!",
        "network_game_over_hint": "ENTER to return to lobby  |  ESC to quit",
        "opponent_disconnected": "Opponent disconnected!",
        "opponent_disconnected_hint": "ENTER to return to lobby",
        "countdown_ready": "Ready!",

        # ── Weapon System (en) ──
        "weapon_normal": "Normal",
        "weapon_spread": "Spread",
        "weapon_laser": "Laser",
        "weapon_homing": "Homing",
        "sub_missile": "MIS",
        "sub_bomb": "BOM",
        "sub_mine": "MIN",
        "item_power": "Power Up  -  +1 weapon level",
        "item_option": "Option  -  +1 floating satellite",

        # ── Item System (en) ──
        "controls_item": "Ctrl  -  Use stored item",
        "item_full_bomb": "Full Screen Bomb  -  Clear all enemies & bullets",
        "item_time_slow": "Time Slow  -  Slow enemies by 50% for 5s",
        "item_reflect_shield": "Reflect Shield  -  Reflect enemy bullets for 3s",
        "item_repair": "Repair  -  Restore 1 life",
        "item_score_boost": "Score Boost  -  2x score for 10s",
        "item_gravity_bomb": "Gravity Bomb  -  Pull + damage all enemies",

        # ── Pause System (en) ──
        "pause_title": "PAUSED",
        "pause_resume": "RESUME",
        "pause_quit": "QUIT TO MENU",
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
        "highest_score": "最高分：{}",
        "score": "得分：{}",
        "level": "等级：{}",
        "lives": "生命：",
        "restart_prompt": "按 ENTER 重新开始  |  按 ESC 退出",
        "restart_prompt_line1": "按 ENTER 重新开始",
        "restart_prompt_line2": "按 ESC 退出",
        "menu_hint": "↑/↓ 选择  |  ENTER 确认",
        "lang_toggle": "[English]",
        "controls_title": "=== 操作说明 ===",
        "controls_move": "方向键 / WASD  —  移动",
        "controls_shoot": "空格 / Z  —  持续射击",
        "controls_weapon": "Q/E  —  切换武器",
        "controls_charge": "Shift  —  蓄力射击",
        "controls_sub": "X  —  子武器",
        "controls_pause": "Esc/P  —  暂停 / 继续",
        "items_title": "=== 道具系统 ===",
        "powerups_title": "=== 道具说明 ===",
        "item_shield": "护盾  —  5秒无敌（蓝色光环）",
        "item_rapid": "速射  —  8秒双倍射速",
        "item_triple": "三连射  —  8秒三向散射",
        "item_bomb": "炸弹  —  消灭全屏敌人",
        "item_speed": "加速  —  8秒加速移动",
        "item_life": "生命  —  增加一条命",
        "help_back": "按 ENTER 或 ESC 返回",
        "help_title": "操作说明",

        # ── 网络模式 (zh) ──
        "network_game": "联网对战",
        "network_title": "联网模式",
        "network_username": "用户名：",
        "server_host": "服务器地址：",
        "server_port": "端口：",
        "network_connect_hint": "ENTER 连接  |  TAB 切换输入框",
        "network_back_hint": "ESC 返回",
        "player_info": "{} ({})",
        "online_count": "在线：{} 人",
        "lobby_title": "游戏大厅",
        "lobby_create_room": "创建房间",
        "lobby_join_room": "加入房间",
        "lobby_matchmaking": "快速匹配",
        "lobby_back": "返回菜单",
        "room_id_input": "房间号：",
        "lobby_hint": "↑/↓ 选择  |  ENTER 确认  |  ESC 返回",
        "room_title": "游戏房间",
        "room_share_hint": "把房间号分享给好友！",
        "room_you": "(你)",
        "room_waiting": "等待对手加入...",
        "room_ready": "已就绪！游戏即将开始...",
        "room_leave_hint": "ESC 离开房间",
        "matchmaking_title": "匹配中",
        "matchmaking_searching": "正在搜索对手",
        "matchmaking_cancel_hint": "ESC 取消匹配",
        "game_win": "你赢了！",
        "game_lose": "你输了！",
        "network_game_over_hint": "ENTER 返回大厅  |  ESC 退出",
        "opponent_disconnected": "对手已断开连接！",
        "opponent_disconnected_hint": "ENTER 返回大厅",
        "countdown_ready": "准备！",

        # ── 武器系统 (zh) ──
        "weapon_normal": "标准",
        "weapon_spread": "散弹",
        "weapon_laser": "激光",
        "weapon_homing": "追踪",
        "sub_missile": "导",
        "sub_bomb": "炸",
        "sub_mine": "雷",
        "item_power": "火力升级  —  武器等级+1",
        "item_option": "辅助机  —  增加一个浮游炮",

        # ── 道具系统 (zh) ──
        "controls_item": "Ctrl  —  使用道具",
        "item_full_bomb": "全屏炸弹  —  消灭全部敌人及子弹",
        "item_time_slow": "时间减速  —  5秒内敌人减速50%",
        "item_reflect_shield": "反射护盾  —  3秒内反弹敌弹",
        "item_repair": "修复  —  恢复1条生命",
        "item_score_boost": "分数增益  —  10秒内得分×2",
        "item_gravity_bomb": "重力炸弹  —  吸引+伤害全部敌人",

        # ── 暂停系统 (zh) ──
        "pause_title": "已暂停",
        "pause_resume": "继续游戏",
        "pause_quit": "返回主菜单",
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