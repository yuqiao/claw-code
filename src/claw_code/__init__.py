"""claw-code - 辅助编码的 Agent。

基于 LangChain 构建的智能编码助手。
"""

__version__ = "0.1.0"

from claw_code.agent import Agent
from claw_code.tools.bash import bash_tool

__all__ = ["Agent", "bash_tool", "__version__"]
