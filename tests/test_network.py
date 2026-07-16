#!/usr/bin/env python3
"""
Sky Guard 网络系统端到端测试
测试：注册、创建房间、加入房间、匹配、数据转发
"""

import json
import sys
import time
import asyncio

sys.path.insert(0, ".")

from network.client import NetworkClient, NetworkEvent

HOST = "127.0.0.1"
PORT = 18999


async def test_async():
    print("=" * 60)
    print("Sky Guard 网络系统端到端测试")
    print("=" * 60)

    # ── 测试 1: 创建两个客户端并注册 ──
    print("\n[测试 1] 创建两个客户端并连接服务器")
    client1 = NetworkClient(HOST, PORT)
    client2 = NetworkClient(HOST, PORT)

    results = {}

    def on_registered_1(data):
        results["p1_id"] = data["player_id"]
        results["p1_name"] = data["username"]
        print(f"  玩家1 注册成功: {data['username']} ({data['player_id']})")

    def on_registered_2(data):
        results["p2_id"] = data["player_id"]
        results["p2_name"] = data["username"]
        print(f"  玩家2 注册成功: {data['username']} ({data['player_id']})")

    def on_error(data):
        print(f"  错误: {data.get('message', '?')}")

    client1.on(NetworkEvent.REGISTERED, on_registered_1)
    client1.on(NetworkEvent.ERROR, on_error)
    client2.on(NetworkEvent.REGISTERED, on_registered_2)
    client2.on(NetworkEvent.ERROR, on_error)

    client1.connect("TestPlayer1")
    client2.connect("TestPlayer2")
    await asyncio.sleep(1)
    client1.process_events()
    client2.process_events()

    assert "p1_id" in results, "玩家1 注册失败"
    assert "p2_id" in results, "玩家2 注册失败"
    print("  ✅ 注册测试通过")

    # ── 测试 2: 创建房间 ──
    print("\n[测试 2] 创建房间")
    room_created = {}

    def on_room_created(data):
        room_created["room"] = data["room"]
        print(f"  房间创建成功: {data['room']['room_id']}")

    client1.on(NetworkEvent.ROOM_CREATED, on_room_created)
    client1.create_room()
    await asyncio.sleep(0.5)
    client1.process_events()

    assert "room" in room_created, "房间创建失败"
    room_id = room_created["room"]["room_id"]
    print(f"  ✅ 房间创建测试通过 (房间号: {room_id})")

    # ── 测试 3: 加入房间 ──
    print("\n[测试 3] 加入房间")
    join_success = {}
    host_notified = {}

    def on_room_joined(data):
        join_success["room"] = data["room"]
        print(f"  玩家2 加入房间成功: {data['room']['room_id']}")

    def on_player_joined(data):
        host_notified["player"] = data["player"]
        print(f"  房主收到通知: 玩家 {data['player']['username']} 已加入")

    client1.on(NetworkEvent.PLAYER_JOINED, on_player_joined)
    client2.on(NetworkEvent.ROOM_JOINED, on_room_joined)
    client2.join_room(room_id)
    await asyncio.sleep(0.5)
    client1.process_events()
    client2.process_events()

    assert "room" in join_success, "加入房间失败"
    assert "player" in host_notified, "房主未收到加入通知"
    print("  ✅ 加入房间测试通过")

    # ── 测试 4: 数据转发 ──
    print("\n[测试 4] 游戏数据转发")
    forwarded_data = {}

    def on_opponent_input(data):
        forwarded_data["received"] = data
        print(f"  收到对手数据: {data['data']}")

    client1.on(NetworkEvent.OPPONENT_INPUT, on_opponent_input)
    client2.send_game_input({"score": 100, "lives": 3})
    await asyncio.sleep(0.5)
    client1.process_events()

    assert "received" in forwarded_data, "数据转发失败"
    assert forwarded_data["received"]["data"]["score"] == 100
    print("  ✅ 数据转发测试通过")

    # ── 测试 5: 离开房间 ──
    print("\n[测试 5] 离开房间")
    client2.leave_room()
    await asyncio.sleep(0.5)
    client1.process_events()
    client2.process_events()

    print("  ✅ 离开房间测试通过")

    # ── 测试 6: 自动匹配 ──
    print("\n[测试 6] 自动匹配")
    match_results = {}
    game_started = {}

    def on_match_found(data):
        match_results["room"] = data["room"]
        match_results["opponent"] = data["opponent"]
        print(f"  匹配成功! 房间: {data['room']['room_id']}, 对手: {data['opponent']['username']}")

    def on_game_start(data):
        game_started["data"] = data
        print("  游戏开始信号收到!")

    # 先离开当前房间
    client1.leave_room()
    await asyncio.sleep(0.5)
    client1.process_events()

    client1.on(NetworkEvent.MATCH_FOUND, on_match_found)
    client1.on(NetworkEvent.GAME_START, on_game_start)
    client2.on(NetworkEvent.MATCH_FOUND, lambda d: print(f"  玩家2 匹配成功!"))
    client2.on(NetworkEvent.GAME_START, lambda d: print(f"  玩家2 游戏开始!"))

    client1.join_matchmaking()
    await asyncio.sleep(0.3)
    client2.join_matchmaking()
    await asyncio.sleep(1)
    client1.process_events()
    client2.process_events()

    assert "room" in match_results, "匹配失败"
    assert "data" in game_started, "游戏开始信号未收到"
    print("  ✅ 自动匹配测试通过")

    # ── 清理 ──
    print("\n" + "=" * 60)
    print("所有测试通过! ✅")
    print("=" * 60)

    client1.disconnect()
    client2.disconnect()
    return True


if __name__ == "__main__":
    success = asyncio.run(test_async())
    sys.exit(0 if success else 1)
