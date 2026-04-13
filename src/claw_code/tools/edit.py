"""Edit 工具实现。

编辑文件内容（替换指定字符串），受路径沙箱保护。
"""

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from claw_code.tools.sandbox import get_safe_path


class EditInput(BaseModel):
    """Edit 命令输入参数。"""

    file_path: str
    old_string: str
    new_string: str


def execute_edit(file_path: str, old_string: str, new_string: str) -> str:
    """编辑文件内容，替换指定字符串。

    Args:
        file_path: 要编辑的文件路径。
        old_string: 要替换的字符串。
        new_string: 替换后的新字符串。

    Returns:
        操作结果消息。

    Raises:
        ValueError: 路径不在工作区内。
    """
    safe_path = get_safe_path(file_path)

    if not safe_path.exists():
        return f"错误：文件 '{file_path}' 不存在"

    if not safe_path.is_file():
        return f"错误：'{file_path}' 不是文件"

    try:
        content = safe_path.read_text(encoding="utf-8")

        if old_string not in content:
            return f"错误：未找到要替换的字符串"

        # 替换（仅替换第一次出现）
        new_content = content.replace(old_string, new_string, 1)

        safe_path.write_text(new_content, encoding="utf-8")
        return f"成功编辑 '{file_path}'，替换了 1 处"
    except Exception as e:
        return f"编辑错误：{e}"


# 创建 LangChain StructuredTool 实例
edit_tool = StructuredTool(
    name="edit",
    description="编辑文件内容（仅限工作区内，替换指定字符串）",
    func=execute_edit,
    args_schema=EditInput,
)