# network/__init__.py
"""
Sky Guard 网络模块。
websockets 为可选依赖 — 未安装时联网功能不可用，单人模式不受影响。
"""

from .protocol import MessageType, NetworkEvent

# 延迟导入 client，避免 websockets 未安装时崩溃
_NetworkClient = None

def get_client(*args, **kwargs):
    """获取 NetworkClient 实例（延迟加载）。"""
    global _NetworkClient
    if _NetworkClient is None:
        from .client import NetworkClient as _Client
        _NetworkClient = _Client
    return _NetworkClient(*args, **kwargs)

def has_network_support() -> bool:
    """检查系统是否支持联网模式。"""
    from .client import _HAS_WEBSOCKETS
    return _HAS_WEBSOCKETS

NetworkClient = None  # 不直接导出，使用 get_client()

__all__ = ["MessageType", "NetworkEvent", "get_client", "has_network_support"]