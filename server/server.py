#!/usr/bin/env python3
"""
Sky Guard 游戏服务器
WebSocket 双人匹配服务器，处理：
- 玩家注册（用户名 + 分配唯一 ID）
- 房间创建与管理（仅支持双人房间）
- 邀请好友加入（通过房间号）
- 自动匹配队列
- 游戏内数据转发
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

import websockets
from websockets.asyncio.server import ServerConnection, serve

from network.protocol import MessageType, DEFAULT_HOST, DEFAULT_PORT

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("server")


# ── 数据模型 ────────────────────────────────────────────────────────────

class Player:
    """已连接的玩家"""

    def __init__(self, player_id: str, username: str, ws: ServerConnection):
        self.player_id: str = player_id
        self.username: str = username
        self.ws: ServerConnection = ws
        self.room_id: Optional[str] = None   # 当前所在房间 ID
        self.in_matchmaking: bool = False    # 是否在匹配队列中
        self.last_ping: float = time.time()

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "username": self.username,
        }

    async def send(self, data: dict):
        """向此玩家发送 JSON 消息"""
        try:
            await self.ws.send(json.dumps(data, ensure_ascii=False))
        except websockets.exceptions.WebSocketException:
            pass


class Room:
    """双人游戏房间"""

    MAX_PLAYERS = 2

    def __init__(self, room_id: str, host: Player):
        self.room_id: str = room_id
        self.host: Player = host
        self.guest: Optional[Player] = None
        self.created_at: float = time.time()
        host.room_id = room_id

    @property
    def is_full(self) -> bool:
        return self.guest is not None

    @property
    def player_count(self) -> int:
        return 1 + (1 if self.guest else 0)

    @property
    def players(self) -> list[Player]:
        ps = [self.host]
        if self.guest:
            ps.append(self.guest)
        return ps

    def to_dict(self) -> dict:
        return {
            "room_id": self.room_id,
            "host": self.host.to_dict(),
            "guest": self.guest.to_dict() if self.guest else None,
            "player_count": self.player_count,
            "max_players": self.MAX_PLAYERS,
        }

    def add_player(self, player: Player) -> bool:
        """添加玩家到房间（仅限双人）"""
        if self.is_full:
            return False
        self.guest = player
        player.room_id = self.room_id
        return True

    def remove_player(self, player: Player) -> bool:
        """移除玩家，返回房间是否应该被销毁"""
        if player is self.host:
            # 房主离开 -> 房间关闭
            return True  # should close
        if player is self.guest:
            self.guest = None
            player.room_id = None
            return False  # 房主还在，等新玩家
        return False

    async def broadcast(self, data: dict, exclude: Optional[Player] = None):
        """向房间内所有玩家广播消息"""
        for p in self.players:
            if p is not exclude:
                await p.send(data)


# ── 服务器 ──────────────────────────────────────────────────────────────

class GameServer:
    """Sky Guard 游戏服务器"""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.players: dict[str, Player] = {}       # player_id → Player
        self.rooms: dict[str, Room] = {}           # room_id → Room
        self.matchmaking_queue: list[Player] = []  # 等待匹配的玩家队列
        self._id_counter: int = 0
        self._ws_connections: dict[ServerConnection, Player] = {}  # ws → Player

    def _next_id(self) -> str:
        self._id_counter += 1
        return f"P{self._id_counter:04d}_{uuid.uuid4().hex[:6]}"

    def _next_room_id(self) -> str:
        return uuid.uuid4().hex[:8].upper()

    # ── 玩家管理 ────────────────────────────────────────────────────────

    def get_player_by_ws(self, ws: ServerConnection) -> Optional[Player]:
        return self._ws_connections.get(ws)

    async def register_player(self, ws: ServerConnection, username: str) -> Player:
        """注册新玩家，分配 ID"""
        # 去重：同一 ws 再次注册
        existing = self.get_player_by_ws(ws)
        if existing:
            # 更新用户名
            existing.username = username
            return existing

        player_id = self._next_id()
        # 确保用户名不空
        username = username.strip() or f"Player_{player_id}"
        player = Player(player_id, username, ws)
        self.players[player_id] = player
        self._ws_connections[ws] = player
        log.info(f"玩家注册: {username} ({player_id})")
        return player

    async def disconnect_player(self, ws: ServerConnection):
        """处理玩家断开连接"""
        player = self._ws_connections.pop(ws, None)
        if player is None:
            return

        log.info(f"玩家断开: {player.username} ({player.player_id})")

        # 从匹配队列移除
        if player.in_matchmaking:
            self._remove_from_matchmaking(player)

        # 从房间移除
        if player.room_id and player.room_id in self.rooms:
            await self._handle_player_leave_room(player)

        self.players.pop(player.player_id, None)

    # ── 房间管理 ────────────────────────────────────────────────────────

    async def create_room(self, player: Player) -> Room:
        """玩家创建房间"""
        # 如果已在房间，先离开
        if player.room_id:
            await self._handle_player_leave_room(player)

        room_id = self._next_room_id()
        room = Room(room_id, player)
        self.rooms[room_id] = room
        log.info(f"房间创建: {room_id} (房主: {player.username})")
        await player.send({
            "type": MessageType.ROOM_CREATED,
            "room": room.to_dict(),
        })
        return room

    async def join_room(self, player: Player, room_id: str) -> bool:
        """玩家通过房间号加入房间"""
        room = self.rooms.get(room_id)
        if room is None:
            await player.send({
                "type": MessageType.ERROR,
                "message": f"房间 {room_id} 不存在",
            })
            return False

        if room.is_full:
            await player.send({
                "type": MessageType.ERROR,
                "message": "房间已满",
            })
            return False

        # 如果玩家已在房间，先离开
        if player.room_id:
            await self._handle_player_leave_room(player)

        # 如果玩家在匹配队列，移除
        if player.in_matchmaking:
            self._remove_from_matchmaking(player)

        room.add_player(player)
        log.info(f"玩家 {player.username} 加入房间 {room_id}")

        # 通知房主
        await room.host.send({
            "type": MessageType.PLAYER_JOINED,
            "player": player.to_dict(),
            "room": room.to_dict(),
        })

        # 通知加入者
        await player.send({
            "type": MessageType.ROOM_JOINED,
            "room": room.to_dict(),
        })

        # 双人满 -> 发游戏开始信号
        if room.is_full:
            await self._start_game(room)

        return True

    async def _handle_player_leave_room(self, player: Player):
        """内部：处理玩家离开房间"""
        room = self.rooms.get(player.room_id or "")
        if room is None:
            return

        should_close = room.remove_player(player)
        player.room_id = None

        if should_close:
            # 房间关闭
            for p in room.players:
                p.room_id = None
                await p.send({
                    "type": MessageType.ROOM_CLOSED,
                    "message": "房主已离开房间",
                })
            self.rooms.pop(room.room_id, None)
            log.info(f"房间关闭: {room.room_id}")
        else:
            # guest 离开，房主还在
            await room.host.send({
                "type": MessageType.PLAYER_LEFT,
                "player": player.to_dict(),
                "room": room.to_dict(),
            })

    async def leave_room(self, player: Player):
        """玩家主动离开房间"""
        if not player.room_id:
            await player.send({
                "type": MessageType.ERROR,
                "message": "你不在任何房间中",
            })
            return
        await self._handle_player_leave_room(player)

    # ── 匹配系统 ────────────────────────────────────────────────────────

    async def join_matchmaking(self, player: Player):
        """玩家加入匹配队列"""
        if player.in_matchmaking:
            await player.send({
                "type": MessageType.ERROR,
                "message": "你已在匹配队列中",
            })
            return

        # 如果在房间，先离开
        if player.room_id:
            await self._handle_player_leave_room(player)

        player.in_matchmaking = True
        self.matchmaking_queue.append(player)
        log.info(f"玩家加入匹配: {player.username} (队列长度: {len(self.matchmaking_queue)})")

        # 尝试匹配
        await self._try_match(player)

    async def leave_matchmaking(self, player: Player):
        """玩家离开匹配队列"""
        if not player.in_matchmaking:
            await player.send({
                "type": MessageType.ERROR,
                "message": "你不在匹配队列中",
            })
            return

        self._remove_from_matchmaking(player)
        await player.send({
            "type": MessageType.MATCHMAKING_CANCELLED,
        })

    def _remove_from_matchmaking(self, player: Player):
        """从匹配队列移除玩家"""
        player.in_matchmaking = False
        if player in self.matchmaking_queue:
            self.matchmaking_queue.remove(player)

    async def _try_match(self, player: Player):
        """尝试为玩家匹配对手"""
        if not player.in_matchmaking:
            return

        # 寻找队列中另一个也在匹配的玩家（且不是自己）
        opponent = None
        for p in self.matchmaking_queue:
            if p is not player and p.in_matchmaking:
                opponent = p
                break

        if opponent is None:
            return  # 暂时无人可匹配

        # 从队列中移除双方
        self._remove_from_matchmaking(player)
        self._remove_from_matchmaking(opponent)

        # 创建房间
        room_id = self._next_room_id()
        room = Room(room_id, player)
        room.add_player(opponent)
        self.rooms[room_id] = room

        log.info(f"匹配成功: {player.username} ↔ {opponent.username} (房间: {room_id})")

        # 通知双方
        for p in room.players:
            await p.send({
                "type": MessageType.MATCH_FOUND,
                "room": room.to_dict(),
                "opponent": opponent.to_dict() if p is player else player.to_dict(),
            })

        # 开始游戏
        await self._start_game(room)

    async def _start_game(self, room: Room):
        """通知房间内的玩家游戏开始"""
        for p in room.players:
            await p.send({
                "type": MessageType.GAME_START,
                "room": room.to_dict(),
            })
        log.info(f"游戏开始: 房间 {room.room_id} — {room.host.username} vs {room.guest.username}")

    # ── 游戏数据转发 ────────────────────────────────────────────────────

    async def forward_game_input(self, sender: Player, data: dict):
        """将玩家的游戏输入转发给房间内的对手"""
        if not sender.room_id or sender.room_id not in self.rooms:
            return
        room = self.rooms[sender.room_id]

        # 找到对手
        opponent = room.guest if sender is room.host else room.host
        if opponent:
            await opponent.send({
                "type": MessageType.OPPONENT_INPUT,
                "data": data,
                "from_player_id": sender.player_id,
            })

    # ── 心跳 ────────────────────────────────────────────────────────────

    async def handle_ping(self, player: Player):
        player.last_ping = time.time()
        await player.send({"type": MessageType.PONG, "server_time": time.time()})

    # ── 在线玩家列表 ────────────────────────────────────────────────────

    async def send_player_list(self, player: Player):
        """发送在线玩家列表"""
        players_list = [p.to_dict() for p in self.players.values()]
        await player.send({
            "type": MessageType.PLAYER_LIST,
            "players": players_list,
            "online_count": len(players_list),
        })

    # ── 消息分发 ────────────────────────────────────────────────────────

    async def handle_message(self, ws: ServerConnection, raw: str):
        """接收并分发客户端消息"""
        player = self.get_player_by_ws(ws)
        if player is None and raw:
            # 还没注册，只能发 register
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                return
            if msg.get("type") == MessageType.REGISTER:
                username = msg.get("username", "Anonymous")
                player = await self.register_player(ws, username)
                await player.send({
                    "type": MessageType.REGISTERED,
                    "player_id": player.player_id,
                    "username": player.username,
                })
            elif msg.get("type") == MessageType.PING:
                pass  # ignore pings before register
            else:
                await ws.send(json.dumps({
                    "type": MessageType.ERROR,
                    "message": "请先发送 register 消息进行注册",
                }))
            return

        if player is None or not raw.strip():
            return

        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            await player.send({
                "type": MessageType.ERROR,
                "message": "无效的 JSON 消息",
            })
            return

        msg_type = msg.get("type")
        handler = {
            MessageType.CREATE_ROOM: lambda: self.create_room(player),
            MessageType.JOIN_ROOM: lambda: self.join_room(player, msg.get("room_id", "")),
            MessageType.LEAVE_ROOM: lambda: self.leave_room(player),
            MessageType.JOIN_MATCHMAKING: lambda: self.join_matchmaking(player),
            MessageType.LEAVE_MATCHMAKING: lambda: self.leave_matchmaking(player),
            MessageType.GAME_INPUT: lambda: self.forward_game_input(player, msg.get("data", {})),
            MessageType.PING: lambda: self.handle_ping(player),
            MessageType.REGISTER: lambda: self._reregister(player, msg),
        }.get(msg_type)

        if handler:
            await handler()
        else:
            await player.send({
                "type": MessageType.ERROR,
                "message": f"未知消息类型: {msg_type}",
            })

    async def _reregister(self, player: Player, msg: dict):
        """已注册玩家更新用户名"""
        username = msg.get("username", "").strip()
        if username:
            old_name = player.username
            player.username = username
            log.info(f"玩家改名: {old_name} → {username}")
            await player.send({
                "type": MessageType.REGISTERED,
                "player_id": player.player_id,
                "username": player.username,
            })

    # ── 服务器生命周期 ──────────────────────────────────────────────────

    async def on_connect(self, ws: ServerConnection):
        """处理新 WebSocket 连接"""
        log.info(f"新连接: {ws.remote_address}")
        try:
            async for raw in ws:
                await self.handle_message(ws, raw)
        except websockets.exceptions.WebSocketException:
            pass
        finally:
            await self.disconnect_player(ws)

    async def run(self):
        """启动服务器"""
        log.info(f"Sky Guard 游戏服务器启动 → ws://{self.host}:{self.port}")
        log.info("=" * 50)
        async with serve(self.on_connect, self.host, self.port):
            await asyncio.get_running_loop().create_future()  # 永久运行


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Sky Guard 游戏服务器")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"监听地址 (默认: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"监听端口 (默认: {DEFAULT_PORT})")
    args = parser.parse_args()

    server = GameServer(host=args.host, port=args.port)
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        log.info("服务器已停止")


if __name__ == "__main__":
    main()
