# SkyGuard — 像素飞机大战

一款使用 Python + Pygame 构建的像素风格纵版飞行射击游戏（Shoot 'em up）。

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

- **移动**: 方向键 ↑↓←→ / WASD
- **射击**: 空格 / Z
- **开始/重开**: Enter
- **退出**: Esc

消灭敌机获取分数，躲避碰撞。每 200 分游戏难度自动提升 —— 敌机更快、更多、出现新类型。

## 敌机类型

| 类型 | 颜色 | 生命值 | 速度 | 分值 |
|------|------|--------|------|------|
| Basic | 红色 | 1 | 普通 | 10 |
| Fast | 紫色 | 1 | 快速 | 15 |
| Tank | 绿色 | 3 | 慢速 | 30 |

## 运行

### 推荐方式（uv）

```bash
# 安装 uv（如未安装）
# curl -LsSf https://astral.sh/uv/install.sh | sh
# 或 brew install uv

# 创建虚拟环境并安装依赖
uv sync

# 运行游戏
uv run main.py
```

### 传统方式（pip）

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install pygame

# 运行游戏
python main.py
```

### Debian/Ubuntu

```bash
sudo apt install python3-pygame
python3 main.py
```

## 项目结构

```
├── main.py                     # 入口：游戏循环与状态管理
├── game/
│   ├── settings.py             # 游戏常量配置
│   ├── state.py                # 有限状态机（菜单/游戏/结束）
│   ├── sprites/
│   │   ├── player.py           # 玩家飞机
│   │   ├── enemy.py            # 敌机（3种）
│   │   ├── bullet.py           # 子弹
│   │   └── explosion.py        # 粒子爆炸特效
│   ├── graphics/
│   │   ├── pixel_art.py        # 程序化像素画生成
│   │   └── hud.py              # HUD 与界面绘制
│   ├── systems/
│   │   ├── spawner.py          # 敌机生成与难度曲线
│   │   └── collision.py        # 碰撞检测
│   └── sounds/
│       └── sound_manager.py    # 8-bit 程序化音效
└── tests/
    └── test_collision.py       # 碰撞检测测试
```

## 特性

- 🎨 **纯代码像素画** — 所有精灵通过 0/1 矩阵生成，零外部美术资源
- 🔊 **8-bit 音效** — 程序化合成（tone / noise / sweep），无音频环境自动静音
- 🔥 **粒子爆炸系统** — 带重力的彩色粒子，支持淡出
- ⭐ **滚动星空背景** — 60 颗随机亮度的星星
- 📈 **动态难度** — 5 级难度阶梯，随分数自动攀升
- ♥ **无敌闪烁保护** — 受伤后 1.5 秒无敌时间，带闪烁反馈

## 许可证

MIT