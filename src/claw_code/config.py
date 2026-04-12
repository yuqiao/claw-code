"""配置管理模块。"""

from dataclasses import dataclass


@dataclass
class Config:
    """Agent 配置。

    定义 Agent 运行的各项配置参数。
    """

    model_name: str = "gpt-4"
    max_iterations: int = 10
    timeout: int = 120
