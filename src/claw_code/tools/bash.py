"""Bash 工具实现。

提供在安全白名单限制下执行 Bash 命令的能力。
"""

import subprocess

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

# 安全命令白名单（第一阶段基础防护）
SAFE_COMMANDS = {
    "ls",
    "cat",
    "pwd",
    "echo",
    "grep",
    "find",
    "head",
    "tail",
    "wc",
    "sort",
    "uniq",
    "diff",
    "tree",
    "mkdir",
    "touch",
}


class BashInput(BaseModel):
    """Bash 命令输入参数。"""

    command: str


def _validate_command(command: str) -> bool:
    """检查命令是否在白名单中。

    Args:
        command: 要检查的命令字符串。

    Returns:
        True 如果命令安全，False 如果不安全。
    """
    if not command or not command.strip():
        return False
    # 提取命令名（第一个词）
    cmd_name = command.strip().split()[0]
    return cmd_name in SAFE_COMMANDS


def execute_bash(command: str, timeout: int = 30) -> str:
    """执行 Bash 命令并返回结果。

    Args:
        command: 要执行的 Bash 命令。
        timeout: 命令执行超时时间（秒）。

    Returns:
        命令输出（stdout）或错误信息（stderr）。

    Raises:
        ValueError: 命令不在白名单中。
    """
    if not _validate_command(command):
        raise ValueError(f"命令 '{command}' 不在安全白名单中")

    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    # 返回 stdout，如果为空则返回 stderr
    if result.stdout:
        return result.stdout
    if result.stderr:
        return result.stderr
    return ""


# 创建 LangChain StructuredTool 实例
bash_tool = StructuredTool(
    name="bash",
    description=(
        "执行安全的 Bash 命令（仅限白名单：ls, cat, pwd, echo, grep, "
        "find, head, tail, wc, sort, uniq, diff, tree, mkdir, touch）"
    ),
    func=execute_bash,
    args_schema=BashInput,
)
