"""路径沙箱验证模块。

防止工具访问工作区外的路径。
"""

import os
from pathlib import Path

# 工作区根路径（启动时的当前工作目录）
WORKSPACE_ROOT = Path(os.getcwd()).resolve()


def _is_safe_path(path: str) -> bool:
    """检查路径是否在工作区内。

    Args:
        path: 要检查的路径字符串。

    Returns:
        True 如果路径在工作区内，False 如果尝试逃逸。
    """
    if not path or not path.strip():
        return False

    try:
        # 解析为绝对路径
        target_path = Path(path).resolve()

        # 检查是否在工作区内
        # 使用 relative_to 检查，如果失败则不在工作区内
        target_path.relative_to(WORKSPACE_ROOT)
        return True
    except ValueError:
        # 不在工作区内
        return False
    except Exception:
        # 其他错误（如无效路径）
        return False


def get_safe_path(path: str) -> Path:
    """获取验证后的安全路径。

    Args:
        path: 原始路径字符串。

    Returns:
        验证后的 Path 对象。

    Raises:
        ValueError: 路径不在工作区内。
    """
    if not _is_safe_path(path):
        raise ValueError(
            f"路径 '{path}' 不在工作区内，禁止访问。工作区：{WORKSPACE_ROOT}"
        )
    return Path(path).resolve()


def get_workspace_root() -> Path:
    """获取工作区根路径。

    Returns:
        工作区根路径 Path 对象。
    """
    return WORKSPACE_ROOT