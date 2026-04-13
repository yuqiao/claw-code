"""Read 工具实现。

读取文件内容，受路径沙箱保护。
"""

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from claw_code.tools.sandbox import get_safe_path


class ReadInput(BaseModel):
    """Read 命令输入参数。"""

    file_path: str


def execute_read(file_path: str) -> str:
    """读取文件内容并返回。

    Args:
        file_path: 要读取的文件路径。

    Returns:
        文件内容字符串。

    Raises:
        ValueError: 路径不在工作区内。
    """
    safe_path = get_safe_path(file_path)

    if not safe_path.exists():
        return f"错误：文件 '{file_path}' 不存在"

    if not safe_path.is_file():
        return f"错误：'{file_path}' 不是文件"

    try:
        return safe_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"读取错误：{e}"


# 创建 LangChain StructuredTool 实例
read_tool = StructuredTool(
    name="read",
    description="读取文件内容（仅限工作区内）",
    func=execute_read,
    args_schema=ReadInput,
)