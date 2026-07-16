# network/client.py
"""
Sky Guard 网络客户端
异步 WebSocket 客户端，提供事件驱动的网络通信。
设计为与 Pygame 游戏循环集成（非阻塞）。
"""

import asyncio
import json
import logging
import threading
import time
from enum import Enum
from typing import Callable, Optional

# websockets 是可选依赖 — 未安装时联网功能不可用，但单人模式不受影响
_HAS_WEBSOCKETS = False
try:
    import websockets
    from websockets.asyncio.client import connect
    _HAS_WEBSOCKETS = True
except ImportError:
    websockets = None  # type: ignore
    connect = None  # type: ignore

from .protocol import MessageType, NetworkEvent, DEFAULT_HOST, DEFAULT_PORT

log = logging.getLogger("network.client")


class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"


class NetworkClient:
    """
    网络客户端。
    在独立线程中运行 asyncio 事件循环，通过事件队列与主线程通信。
    """

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.server_url = f"ws://{host}:{port}"

        # 玩家信息
        self.player_id: Optional[str] = None
        self.username: Optional[str] = None

        # 连接状态
        self.status = ConnectionStatus.DISCONNECTED

        # 事件回调表 {event_name: [callback_fn, ...]}
        self._listeners: dict[str, list[Callable]] = {}

        # 待处理的事件队列（线程安全，主线程消费）
        self._event_queue: list[tuple[str, dict]] = []
        self._queue_lock = threading.Lock()

        # 内部
        self._ws = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._reconnect_timer: Optional[threading.Timer] = None
        self._max_reconnect_attempts = 5
        self._reconnect_attempt = 0
        self._reconnect_delay = 1.0  # seconds, doubles each attempt

    # ── 事件系统 ────────────────────────────────────────────────────────

    def on(self, event: str, callback: Callable):
        """注册事件监听"""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
        return self  # 支持链式调用

    def off(self, event: str, callback: Optional[Callable] = None):
        """注销事件监听。不传 callback 则移除该事件全部监听。"""
        if event not in self._listeners:
            return
        if callback is None:
            self._listeners[event].clear()
        else:
            self._listeners[event] = [cb for cb in self._listeners[event] if cb is not callback]

    def _emit(self, event: str, data: dict = None):
        """将事件放入队列，主线程在 process_events() 中消费"""
        with self._queue_lock:
            self._event_queue.append((event, data or {}))

    def process_events(self):
        """
        在主线程（Pygame 循环）中调用，处理所有待处理事件。
        建议每帧调用一次。
        """
        events_to_process = []
        with self._queue_lock:
            events_to_process = self._event_queue[:]
            self._event_queue.clear()

        for event, data in events_to_process:
            listeners = self._listeners.get(event, [])
            for callback in listeners:
                try:
                    callback(data)
                except Exception as e:
                    log.error(f"事件回调异常 [{event}]: {e}")

    # ── 连接管理 ────────────────────────────────────────────────────────

    def connect(self, username: str):
        """启动连接到服务器（非阻塞）"""
        if self.status != ConnectionStatus.DISCONNECTED:
            log.warning(f"连接已存在，状态: {self.status}")
            return

        self.username = username
        self.status = ConnectionStatus.CONNECTING
        self._reconnect_attempt = 0
        self._running = True

        # 启动 asyncio 事件循环线程
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def disconnect(self):
        """断开连接"""
        self._running = False
        self._cancel_reconnect()

        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._disconnect_internal(), self._loop)

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

        self.status = ConnectionStatus.DISCONNECTED
        self.player_id = None

    async def _disconnect_internal(self):
        """内部异步断开"""
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

    def _cancel_reconnect(self):
        if self._reconnect_timer and self._reconnect_timer.is_alive():
            self._reconnect_timer.cancel()
            self._reconnect_timer = None

    async def _try_reconnect(self):
        """尝试重新连接"""
        self._reconnect_attempt += 1
        if self._reconnect_attempt > self._max_reconnect_attempts:
            log.error("重连次数达到上限，停止重连")
            self._running = False
            self._emit(NetworkEvent.DISCONNECTED, {"reason": "max_reconnect_attempts"})
            return

        delay = self._reconnect_delay * (2 ** (self._reconnect_attempt - 1))
        log.info(f"将在 {delay:.1f}s 后尝试重连 (第 {self._reconnect_attempt} 次)...")
        await asyncio.sleep(delay)

        if not self._running:
            return

        self.status = ConnectionStatus.CONNECTING
        try:
            await self._connect_internal()
        except Exception:
            # 重连失败，继续尝试
            self._emit(NetworkEvent.ERROR, {"message": f"重连失败 ({self._reconnect_attempt})"})
            asyncio.create_task(self._try_reconnect())

    def _schedule_reconnect(self):
        """在事件循环中安排重连"""
        if self._running and not self._reconnect_timer:
            asyncio.create_task(self._try_reconnect())

    def _run_loop(self):
        """运行 asyncio 事件循环（在独立线程中）"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._connect_internal())
        except Exception as e:
            log.error(f"事件循环异常: {e}")
        finally:
            self._loop.close()
            self._loop = None

    async def _connect_internal(self):
        """内部异步连接逻辑"""
        try:
            self._ws = await connect(
                self.server_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5,
                max_size=10 * 1024 * 1024,  # 10MB
            )
            self.status = ConnectionStatus.CONNECTED
            self._reconnect_attempt = 0
            self._emit(NetworkEvent.CONNECTED, {})

            # 发送注册消息
            await self._send({
                "type": MessageType.REGISTER,
                "username": self.username,
            })

            # 开始接收消息
            await self._receive_loop()

        except (websockets.exceptions.WebSocketException, OSError) as e:
            log.error(f"连接失败: {e}")
            self.status = ConnectionStatus.DISCONNECTED
            self._emit(NetworkEvent.ERROR, {"message": f"连接失败: {e}"})
            # 自动重连
            if self._running:
                self._schedule_reconnect()

    async def _receive_loop(self):
        """接收消息循环"""
        try:
            async for raw in self._ws:
                try:
                    msg = json.loads(raw)
                    await self._handle_server_message(msg)
                except json.JSONDecodeError:
                    log.warning(f"收到无效 JSON: {raw[:100]}")
        except websockets.exceptions.ConnectionClosed:
            log.info("连接已关闭")
        except Exception as e:
            log.error(f"接收消息异常: {e}")
        finally:
            self._ws = None
            old_status = self.status
            self.status = ConnectionStatus.DISCONNECTED

            if old_status != ConnectionStatus.DISCONNECTING:
                self._emit(NetworkEvent.DISCONNECTED, {"reason": "connection_lost"})
                # 自动重连
                if self._running:
                    self._schedule_reconnect()

    async def _handle_server_message(self, msg: dict):
        """处理服务器消息"""
        msg_type = msg.get("type")

        if msg_type == MessageType.REGISTERED:
            self.player_id = msg.get("player_id")
            self.username = msg.get("username")
            self._emit(NetworkEvent.REGISTERED, msg)

        elif msg_type == MessageType.ROOM_CREATED:
            self._emit(NetworkEvent.ROOM_CREATED, msg)

        elif msg_type == MessageType.ROOM_JOINED:
            self._emit(NetworkEvent.ROOM_JOINED, msg)

        elif msg_type == MessageType.PLAYER_JOINED:
            self._emit(NetworkEvent.PLAYER_JOINED, msg)

        elif msg_type == MessageType.PLAYER_LEFT:
            self._emit(NetworkEvent.PLAYER_LEFT, msg)

        elif msg_type == MessageType.ROOM_CLOSED:
            self._emit(NetworkEvent.ROOM_CLOSED, msg)

        elif msg_type == MessageType.MATCH_FOUND:
            self._emit(NetworkEvent.MATCH_FOUND, msg)

        elif msg_type == MessageType.MATCHMAKING_CANCELLED:
            self._emit(NetworkEvent.MATCHMAKING_CANCELLED, msg)

        elif msg_type == MessageType.GAME_START:
            self._emit(NetworkEvent.GAME_START, msg)

        elif msg_type == MessageType.OPPONENT_INPUT:
            self._emit(NetworkEvent.OPPONENT_INPUT, msg)

        elif msg_type == MessageType.PARTNER_STATE:
            self._emit(NetworkEvent.PARTNER_STATE, msg)

        elif msg_type == MessageType.ENEMY_KILLED:
            self._emit(NetworkEvent.ENEMY_KILLED, msg)

        elif msg_type == MessageType.PARTNER_BULLET:
            self._emit(NetworkEvent.PARTNER_BULLET, msg)

        elif msg_type == MessageType.GAME_SEED:
            self._emit(NetworkEvent.GAME_SEED, msg)

        elif msg_type == MessageType.COOP_START:
            self._emit(NetworkEvent.COOP_START, msg)

        elif msg_type == MessageType.PLAYER_LIST:
            self._emit(NetworkEvent.PLAYER_LIST, msg)

        elif msg_type == MessageType.ROOM_INFO:
            self._emit(NetworkEvent.ROOM_INFO, msg)

        elif msg_type == MessageType.ERROR:
            self._emit(NetworkEvent.ERROR, msg)

        elif msg_type == MessageType.PONG:
            pass  # 心跳响应，无需处理

        else:
            log.warning(f"未知消息类型: {msg_type}")

    # ── 发送消息 ────────────────────────────────────────────────────────

    async def _send(self, data: dict):
        """异步发送 JSON 消息"""
        if not self._ws:
            log.warning("发送失败：未连接")
            return
        try:
            await self._ws.send(json.dumps(data, ensure_ascii=False))
        except websockets.exceptions.WebSocketException as e:
            log.error(f"发送消息失败: {e}")

    def send(self, data: dict):
        """从主线程发送消息到服务器（线程安全）"""
        if self._loop and not self._loop.is_closed() and self._ws:
            asyncio.run_coroutine_threadsafe(self._send(data), self._loop)

    # ── 高层 API ────────────────────────────────────────────────────────

    def create_room(self):
        """创建房间"""
        self.send({"type": MessageType.CREATE_ROOM})

    def join_room(self, room_id: str):
        """通过房间号加入房间"""
        self.send({"type": MessageType.JOIN_ROOM, "room_id": room_id})

    def leave_room(self):
        """离开当前房间"""
        self.send({"type": MessageType.LEAVE_ROOM})

    def join_matchmaking(self):
        """加入匹配队列"""
        self.send({"type": MessageType.JOIN_MATCHMAKING})

    def leave_matchmaking(self):
        """离开匹配队列"""
        self.send({"type": MessageType.LEAVE_MATCHMAKING})

    def send_game_input(self, data: dict):
        """发送游戏输入数据给对手"""
        self.send({"type": MessageType.GAME_INPUT, "data": data})

    def send_player_state(self, x: float, y: float, lives: int, score: int):
        """高频发送玩家位置/状态（合作模式用）"""
        self.send({
            "type": MessageType.PLAYER_STATE,
            "state": {"x": x, "y": y, "lives": lives, "score": score},
        })

    def send_enemy_killed(self, enemy_id: int, score: int = 0, powerup_type: str = None):
        """发送敌机击杀事件（附带道具信息用于伙伴端渲染）"""
        msg = {
            "type": MessageType.ENEMY_KILLED,
            "enemy_id": enemy_id,
            "score": score,
        }
        if powerup_type:
            msg["powerup"] = powerup_type
        self.send(msg)

    def send_bullet_spawned(self, x: float, y: float, is_triple: bool = False):
        """发送射击事件（伙伴端渲染子弹）"""
        self.send({
            "type": MessageType.PARTNER_BULLET,
            "x": x,
            "y": y,
            "is_triple": is_triple,
        })

    def request_player_list(self):
        """请求在线玩家列表"""
        self.send({"type": MessageType.PLAYER_LIST})

    def ping(self):
        """发送心跳"""
        self.send({"type": MessageType.PING})


class NetworkClientFactory:
    """便捷工厂方法"""

    @staticmethod
    def create_and_connect(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                           username: str = "Player") -> NetworkClient:
        client = NetworkClient(host, port)
        client.connect(username)
        return client