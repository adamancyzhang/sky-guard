#!/usr/bin/env python3
"""
Sky Guard 游戏服务器启动器

用法：
    python run_server.py             # 默认 127.0.0.1:8765
    python run_server.py --host 0.0.0.0 --port 9000
    python run_server.py --host 0.0.0.0  # 允许局域网/外网连接
"""

import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.server import main

if __name__ == "__main__":
    main()
