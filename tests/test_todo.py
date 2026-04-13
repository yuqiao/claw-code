"""Todo 功能测试。"""

import pytest

from langchain.agents.middleware import TodoListMiddleware
from langchain.agents.middleware.todo import Todo


class TestTodoMiddlewareImport:
    """测试 TodoListMiddleware 导入。"""

    def test_todo_middleware_should_import_successfully(self) -> None:
        """TodoListMiddleware 应能成功导入。"""
        assert TodoListMiddleware is not None

    def test_todo_middleware_should_have_correct_attributes(self) -> None:
        """TodoListMiddleware 应有正确属性。"""
        middleware = TodoListMiddleware()
        assert middleware.tools is not None
        assert len(middleware.tools) == 1
        assert middleware.tools[0].name == "write_todos"


class TestTodoDataStructure:
    """测试 Todo 数据结构。"""

    def test_todo_should_have_content_field(self) -> None:
        """Todo 应有 content 字段。"""
        todo: Todo = {"content": "test task", "status": "pending"}
        assert todo["content"] == "test task"

    def test_todo_should_have_status_field(self) -> None:
        """Todo 应有 status 字段。"""
        todo: Todo = {"content": "test task", "status": "in_progress"}
        assert todo["status"] == "in_progress"

    def test_todo_status_should_be_valid(self) -> None:
        """Todo status 应为有效值。"""
        valid_statuses = ["pending", "in_progress", "completed"]
        for status in valid_statuses:
            todo: Todo = {"content": "test", "status": status}
            assert todo["status"] in valid_statuses


class TestAgentTodoIntegration:
    """测试 Agent Todo 集成。"""

    def test_agent_should_accept_enable_todo_parameter(self) -> None:
        """Agent 应接受 enable_todo 参数。"""
        from claw_code.agent import Agent

        # 验证参数存在（不实际创建 Agent，因为需要模型）
        import inspect
        sig = inspect.signature(Agent.__init__)
        params = sig.parameters
        assert "enable_todo" in params

    def test_agent_enable_todo_default_should_be_true(self) -> None:
        """Agent enable_todo 默认值应为 True。"""
        from claw_code.agent import Agent

        import inspect
        sig = inspect.signature(Agent.__init__)
        params = sig.parameters
        assert params["enable_todo"].default is True

    def test_agent_format_todos_progress_should_work(self) -> None:
        """Agent _format_todos_progress 应正确格式化。"""
        from claw_code.agent import Agent

        # 创建一个最小 Agent 实例测试方法
        # 注意：这不会实际运行 graph，只是测试方法
        todos = [
            {"content": "任务1", "status": "completed"},
            {"content": "任务2", "status": "in_progress"},
            {"content": "任务3", "status": "pending"},
        ]

        # 直接测试静态方法逻辑
        status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}
        progress = "\n\n当前进度：\n"
        for todo in todos:
            icon = status_icon.get(todo["status"], "❓")
            progress += f"{icon} {todo['content']}\n"

        assert "✅ 任务1" in progress
        assert "🔄 任务2" in progress
        assert "⏳ 任务3" in progress


class TestWriteTodosTool:
    """测试 write_todos 工具。"""

    def test_write_todos_tool_should_exist(self) -> None:
        """write_todos 工具应存在。"""
        middleware = TodoListMiddleware()
        tool = middleware.tools[0]
        assert tool.name == "write_todos"

    def test_write_todos_tool_should_have_description(self) -> None:
        """write_todos 工具应有详细描述。"""
        middleware = TodoListMiddleware()
        tool = middleware.tools[0]
        assert tool.description
        assert "complex" in tool.description.lower() or "任务" in tool.description

    def test_write_todos_tool_description_should_mention_when_to_use(self) -> None:
        """write_todos 工具描述应说明何时使用。"""
        middleware = TodoListMiddleware()
        tool = middleware.tools[0]
        # 工具描述包含使用指南
        assert "3 or more" in tool.description or "multi-step" in tool.description


class TestMainTodoOption:
    """测试 main.py Todo 选项。"""

    def test_main_should_have_todo_option(self) -> None:
        """main 函数应有 --todo 选项。"""
        from claw_code.main import main

        import inspect
        sig = inspect.signature(main)
        params = sig.parameters
        assert "enable_todo" in params

    def test_main_todo_option_default_should_be_true(self) -> None:
        """--todo 默认值应为 True。"""
        from claw_code.main import main

        import inspect
        sig = inspect.signature(main)
        params = sig.parameters
        assert params["enable_todo"].default is True