"""pytest 配置和共享 fixtures。"""

import pytest

from claw_code.config import Config
from claw_code.tools.bash import bash_tool


@pytest.fixture
def config() -> Config:
    """提供默认配置 fixture。"""
    return Config()


@pytest.fixture
def tool() -> bash_tool:
    """提供 Bash 工具 fixture。"""
    return bash_tool
