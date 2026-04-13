"""Write 工具实现。

写入文件内容，受路径沙箱保护。
"""

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from claw_code.tools.sandbox import get_safe_path


class WriteInput(BaseModel):
    """Write 命令输入参数。"""

    file_path: str
    content: str


def execute_write(file_path: str, content: str) -> str:
    """写入文件内容。

    Args:
        file_path: 要写入的文件路径。
        content: 要写入的内容。

    Returns:
        操作结果消息。

    Raises:
        ValueError: 路径不在工作区内。
    """
    safe_path = get_safe_path(file_path)

    # 确保父目录存在
    safe_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        safe_path.write_text(content, encoding="utf-8")
        return f"成功写入 '{file_path}'，共 {len(content)} 字符"
    except Exception as e:
        return f"写入错误：{e}"


# 创建 LangChain StructuredTool 实例
write_tool = StructuredTool(
    name="write",
    description="写入文件内容（仅限工作区内，会创建父目录）",
    func=execute_write,
    args_schema=WriteInput,
)