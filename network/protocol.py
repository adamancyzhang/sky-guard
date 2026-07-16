# network/protocol.py
"""
WebSocket 消息协议定义。
所有消息均以 JSON 格式传输，每条消息包含 "type" 字段标识消息类型。
"""


class MessageType:
    """客户端↔服务器 消息类型常量"""

    # ── 客户端 → 服务器 ──────────────────────────────────
    REGISTER = "register"                # 首次连接注册用户名
    CREATE_ROOM = "create_room"          # 创建一个房间
    JOIN_ROOM = "join_room"             # 通过房间号加入房间
    LEAVE_ROOM = "leave_room"           # 离开当前房间
    JOIN_MATCHMAKING = "join_matchmaking"   # 加入匹配队列
    LEAVE_MATCHMAKING = "leave_matchmaking" # 离开匹配队列
    GAME_INPUT = "game_input"           # 发送游戏输入给对方
    PING = "ping"                        # 心跳

    # ── 服务器 → 客户端 ──────────────────────────────────
    REGISTERED = "registered"            # 注册成功，返回 ID 和用户名
    ROOM_CREATED = "room_created"        # 房间创建成功
    ROOM_JOINED = "room_joined"          # 加入房间成功
    PLAYER_JOINED = "player_joined"      # 有玩家加入你的房间
    PLAYER_LEFT = "player_left"          # 有玩家离开房间
    ROOM_CLOSED = "room_closed"          # 房间已关闭
    MATCH_FOUND = "match_found"          # 匹配成功，返回房间信息
    MATCHMAKING_CANCELLED = "matchmaking_cancelled"  # 取消匹配
    GAME_START = "game_start"            # 游戏开始信号
    OPPONENT_INPUT = "opponent_input"    # 转发对方的游戏输入
    PONG = "pong"                        # 心跳回复
    PLAYER_LIST = "player_list"          # 在线玩家列表
    ERROR = "error"                      # 错误消息
    ROOM_INFO = "room_info"              # 房间当前信息更新


class NetworkEvent:
    """网络事件的回调类型，用于 client 的事件系统"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    REGISTERED = "registered"
    ERROR = "error"
    ROOM_CREATED = "room_created"
    ROOM_JOINED = "room_joined"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    ROOM_CLOSED = "room_closed"
    MATCH_FOUND = "match_found"
    MATCHMAKING_CANCELLED = "matchmaking_cancelled"
    GAME_START = "game_start"
    OPPONENT_INPUT = "opponent_input"
    PLAYER_LIST = "player_list"
    ROOM_INFO = "room_info"


# 默认服务器地址
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
