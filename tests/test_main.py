"""CLI 入口测试。"""

import os
from unittest.mock import MagicMock, patch

import pytest
import typer

from claw_code.main import check_api_key, get_model, main


class TestGetModel:
    """测试 get_model 函数。"""

    def test_get_model_when_env_set_should_return_env_value(self) -> None:
        """环境变量设置时应返回环境变量值。"""
        with patch.dict(os.environ, {"ANTHROPIC_MODEL": "claude-opus-4-6"}):
            assert get_model() == "claude-opus-4-6"

    def test_get_model_when_env_not_set_should_return_default(self) -> None:
        """环境变量未设置时应返回默认值。"""
        with patch.dict(os.environ, {}, clear=True):
            # 移除 ANTHROPIC_MODEL
            os.environ.pop("ANTHROPIC_MODEL", None)
            assert get_model() == "claude-sonnet-4-6"


class TestCheckApiKey:
    """测试 check_api_key 函数。"""

    def test_check_api_key_when_set_should_not_exit(self) -> None:
        """API Key 设置时不应退出。"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            # 不应抛出异常
            check_api_key()

    def test_check_api_key_when_not_set_should_exit(self) -> None:
        """API Key 未设置时应退出。"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(typer.Exit):
                check_api_key()


class TestMain:
    """测试 main 函数。"""

    def test_main_when_exit_input_should_break_loop(self) -> None:
        """输入 exit 时应退出循环。"""
        with patch.dict(
            os.environ,
            {
                "ANTHROPIC_API_KEY": "test-key",
                "ANTHROPIC_MODEL": "claude-sonnet-4-6",
            },
        ):
            with patch("typer.prompt", side_effect=["exit"]):
                with patch("claw_code.main.Agent") as mock_agent:
                    mock_agent.return_value = MagicMock()
                    # main 应正常退出
                    main()

    def test_main_when_quit_input_should_break_loop(self) -> None:
        """输入 quit 时应退出循环。"""
        with patch.dict(
            os.environ,
            {
                "ANTHROPIC_API_KEY": "test-key",
                "ANTHROPIC_MODEL": "claude-sonnet-4-6",
            },
        ):
            with patch("typer.prompt", side_effect=["quit"]):
                with patch("claw_code.main.Agent") as mock_agent:
                    mock_agent.return_value = MagicMock()
                    main()
