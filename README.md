# SkyGuard — 像素飞机大战

一款使用 Python + Pygame 构建的像素风格纵版飞行射击游戏（Shoot 'em up），支持**单机模式**和**联网双人匹配对战**。

## 游戏截图

```
          ██
          ██
        ██████
       ████████
      ██████████
     ████████████
      ██████████
       ██    ██
       ██    ██         ← 玩家飞机（青蓝色）
    
     ████████████
    ██████████████
    ██████████████
    ██████████████
     ██  ████  ██
      ██ █  █ ██        ← 敌机（红色）
       ██    ██
```

*所有美术资源通过代码程序化生成，无外部图片依赖。*

## 玩法

| 操作 | 按键 |
|------|------|
| 移动 | 方向键 ↑↓←→ / WASD |
| 射击 | 空格 / Z |
| 开始/重开 | Enter |
| 退出 | Esc |
| 切换语言 | L |

消灭敌机获取分数，躲避碰撞。每 200 分游戏难度自动提升 —— 敌机更快、更多、出现新类型。每 1000 分出现 Boss。

## 敌机类型

| 类型 | 颜色 | 生命值 | 速度 | 分值 |
|------|------|--------|------|------|
| Basic | 红色 | 1 | 普通 | 10 |
| Fast | 紫色 | 1 | 快速 | 15 |
| Tank | 绿色 | 3 | 慢速 | 30 |

## 联网模式

支持双人通过网络匹配对战。双方各自在同一关卡中打 AI 敌人，比拼存活时间和得分。

### 完整流程

```
主菜单 → [联网对战]
  → 输入用户名 / 服务器地址 / 端口 (TAB 切换)
  → ENTER 连接 → 进入大厅
     大厅:
       [创建房间] → 获得房间号 → 分享给好友
       [加入房间] → 输入好友的房间号
       [快速匹配] → 自动配对
  → 房间满员 → 3... 2... 1... GO! (倒计时)
  → 对战 (HUD 显示双方得分和生命)
  → 游戏结束 → 胜负对比画面
```

### 启动服务器

需要先启动一台匹配服务器，玩家再连接上去：

```bash
# 默认监听 127.0.0.1:8765
uv run python run_server.py

# 开放局域网连接
uv run python run_server.py --host 0.0.0.0 --port 8765
```

服务器日志示例：
```
[12:30:00] INFO Sky Guard 游戏服务器启动 → ws://0.0.0.0:8765
[12:30:10] INFO 玩家注册: Alice (P0001_a4b3f2)
[12:30:15] INFO 房间创建: E1815E31 (房主: Alice)
[12:30:20] INFO 玩家 Bob 加入房间 E1815E31
[12:30:20] INFO 游戏开始: 房间 E1815E31 — Alice vs Bob
```

### 通讯协议

基于 WebSocket 的 JSON 消息协议，详见 `network/protocol.py`。核心消息类型：

| 方向 | 消息 | 说明 |
|------|------|------|
| C→S | `register` | 注册用户名 |
| S→C | `registered` | 返回 player_id |
| C→S | `create_room` | 创建房间 |
| C→S | `join_room` | 输入房间号加入 |
| C→S | `join_matchmaking` | 进入匹配队列 |
| S→C | `match_found` | 匹配成功 |
| S→C | `game_start` | 开始游戏 |
| C→S | `game_input` | 发送游戏状态给对手 |
| S→C | `opponent_input` | 接收对手状态 |
| C→S | `ping` / S→C `pong` | 心跳 |

## 运行

### 推荐方式（uv）

```bash
# 安装 uv（如未安装）
# curl -LsSf https://astral.sh/uv/install.sh | sh
# 或 brew install uv

# 创建虚拟环境并安装依赖（自动安装 pygame + websockets）
uv sync

# 运行游戏（单机模式）
uv run main.py

# 启动匹配服务器
uv run python run_server.py
```

### 传统方式（pip）

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install pygame websockets

# 运行游戏
python main.py

# 启动匹配服务器（另一个终端）
python run_server.py
```

### 仅单机模式（不安装 websockets）

`websockets` 是可选依赖。如果只想玩单机模式，可以不安装：

```bash
pip install pygame
python main.py
```

主菜单的「联网对战」选项会自动检测并提示安装 websockets。

## 项目结构

```
├── main.py                     # 入口：游戏循环与状态管理
├── run_server.py               # 匹配服务器启动入口
├── pyproject.toml              # 项目元数据与依赖声明
│
├── game/
│   ├── settings.py             # 游戏常量配置
│   ├── state.py                # 有限状态机（含联网状态）
│   ├── l10n.py                 # 中英双语本地化
│   ├── highscore.py            # 最高分持久化
│   ├── sprites/
│   │   ├── player.py           # 玩家飞机
│   │   ├── enemy.py            # 敌机（3种）
│   │   ├── boss.py             # Boss 敌人
│   │   ├── bullet.py           # 玩家子弹
│   │   ├── enemy_bullet.py     # 敌人子弹
│   │   ├── explosion.py        # 粒子爆炸特效
│   │   └── powerup.py          # 道具（护盾/速射/三连/炸弹/加速/生命）
│   ├── graphics/
│   │   ├── pixel_art.py        # 程序化像素画生成
│   │   ├── hud.py              # HUD 与全部界面绘制（含联网界面）
│   │   ├── background.py       # 多层视差滚动背景
│   │   └── screen_shake.py     # 屏幕震动特效
│   ├── systems/
│   │   ├── spawner.py          # 敌机生成与难度曲线
│   │   └── collision.py        # 碰撞检测
│   └── sounds/
│       └── sound_manager.py    # 8-bit 程序化音效
│
├── network/                    # ← 新增：联网模块
│   ├── __init__.py             # 延迟加载包装（websockets 可选）
│   ├── client.py               # WebSocket 异步客户端
│   └── protocol.py             # 消息协议定义
│
├── server/                     # ← 新增：匹配服务器
│   ├── __init__.py
│   └── server.py               # WebSocket 游戏服务器
│
├── tests/
│   ├── test_collision.py       # 碰撞检测测试
│   ├── test_boss.py            # Boss 测试
│   ├── test_highscore.py       # 高分测试
│   └── test_network.py         # ← 新增：联网端到端测试(6项)
│
└── assets/
    └── fonts/
        └── README.md           # 字体说明
```

## 特性

- 🎨 **纯代码像素画** — 所有精灵通过 0/1 矩阵生成，零外部美术资源
- 🔊 **8-bit 音效** — 程序化合成（tone / noise / sweep），无音频环境自动静音
- 🔥 **粒子爆炸系统** — 带重力的彩色粒子，支持淡出
- ⭐ **滚动星空背景** — 60 颗随机亮度的星星 + 5 种关卡主题
- 📈 **动态难度** — 5 级难度阶梯，随分数自动攀升
- ♥ **无敌闪烁保护** — 受伤后 1.5 秒无敌时间，带闪烁反馈
- 🌐 **联网双人匹配** — WebSocket 服务器 + 事件驱动客户端，支持创建房间、邀请好友、自动匹配
- 🏆 **网络对战** — 3-2-1 倒计时开局，实时显示对手得分/生命，断线检测，胜负对比

## 许可证

MIT
