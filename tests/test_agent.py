"""Agent 单元测试。"""

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage
from pydantic import BaseModel

from claw_code.agent import Agent


class SimpleInput(BaseModel):
    """简单测试输入。"""

    text: str


class TestAgentInit:
    """测试 Agent 初始化。"""

    def test_agent_init_when_model_and_tools_should_bind_tools(self) -> None:
        """Agent 初始化应绑定工具到模型。"""
        from langchain_core.tools import StructuredTool

        mock_model = MagicMock()
        mock_model.bind_tools = MagicMock(return_value=mock_model)

        tool = StructuredTool(
            name="test_tool",
            description="测试工具",
            func=lambda x: x,
            args_schema=SimpleInput,
        )

        agent = Agent(model=mock_model, tools=[tool])

        mock_model.bind_tools.assert_called_once_with([tool])
        assert agent.tools_by_name == {"test_tool": tool}


class TestAgentRun:
    """测试 Agent run 方法。"""

    def test_agent_run_when_no_tool_calls_should_return_content(self) -> None:
        """无工具调用时应直接返回内容。"""
        mock_model = MagicMock()
        mock_model.bind_tools = MagicMock(return_value=mock_model)
        mock_model.invoke = MagicMock(
            return_value=AIMessage(content="直接回答", tool_calls=[])
        )

        agent = Agent(model=mock_model, tools=[])
        result = agent.run("你好")

        assert result == "直接回答"

    def test_agent_run_when_single_tool_call_should_execute_and_continue(
        self,
    ) -> None:
        """有工具调用时应执行并继续循环。"""
        mock_model = MagicMock()
        mock_model.bind_tools = MagicMock(return_value=mock_model)

        # 第一次调用返回工具调用，第二次返回最终答案
        tool_call = {"name": "bash", "args": {"command": "ls"}, "id": "call_1"}
        mock_model.invoke = MagicMock(
            side_effect=[
                AIMessage(content="", tool_calls=[tool_call]),
                AIMessage(content="列出完成", tool_calls=[]),
            ]
        )

        # Mock 工具执行
        mock_tool = MagicMock()
        mock_tool.invoke = MagicMock(return_value="file1.txt\nfile2.txt")

        agent = Agent(model=mock_model, tools=[mock_tool])
        agent.tools_by_name = {"bash": mock_tool}

        result = agent.run("列出文件")

        assert result == "列出完成"
        assert mock_tool.invoke.called

    def test_agent_run_when_max_iterations_should_raise_error(self) -> None:
        """达到最大迭代次数应抛出 RuntimeError。"""
        mock_model = MagicMock()
        mock_model.bind_tools = MagicMock(return_value=mock_model)

        # 模拟无限工具调用
        tool_call = {"name": "bash", "args": {"command": "ls"}, "id": "call_1"}
        infinite_response = AIMessage(content="", tool_calls=[tool_call])
        mock_model.invoke = MagicMock(return_value=infinite_response)

        mock_tool = MagicMock()
        mock_tool.name = "bash"
        mock_tool.invoke = MagicMock(return_value="output")

        agent = Agent(model=mock_model, tools=[mock_tool], max_iterations=3)

        # 达到 max_iterations 后应抛出 RuntimeError
        with pytest.raises(RuntimeError, match="达到最大迭代次数"):
            agent.run("无限循环测试")

        # 验证确实执行了 max_iterations 次
        assert mock_model.invoke.call_count == 3
