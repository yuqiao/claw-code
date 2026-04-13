"""Agent 核心实现模块。

使用 LangChain create_agent + middleware 架构。
"""

from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, TodoListMiddleware, wrap_tool_call
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import BaseTool

# 系统提示词
SYSTEM_PROMPT = """你是一个智能编码助手。

你可以使用以下工具：
- bash: 执行安全的命令（ls, cat, pwd, echo, grep, find, head, tail, wc, sort, uniq, diff, tree, mkdir, touch）
- read: 读取文件内容（仅限工作区内）
- write: 写入文件内容（自动创建父目录）
- edit: 编辑文件内容（替换指定字符串）
- write_todos: 创建和管理任务列表

任务管理原则：
- 复杂任务（3+ 步骤）使用 write_todos 创建任务列表
- 同一时间只能有一个 in_progress 任务
- 开始任务前先标记为 in_progress
- 完成后立即标记为 completed
- 简单任务直接执行，不用 write_todos

完成任务后，总结你做了什么并给出最终答案。"""


class ToolErrorHandler(AgentMiddleware):
    """工具错误处理 middleware。

    捕获工具执行错误，返回友好的错误消息给模型。
    """

    @wrap_tool_call
    def handle_tool_error(
        self, request: Any, handler: Any
    ) -> ToolMessage | AIMessage:
        """处理工具调用，捕获错误返回友好消息。

        Args:
            request: 工具调用请求。
            handler: 工具执行 handler。

        Returns:
            ToolMessage 或 AIMessage。
        """
        try:
            return handler(request)
        except Exception as e:
            return ToolMessage(
                content=f"工具执行错误：{e}。请检查输入并重试。",
                tool_call_id=request.tool_call["id"],
            )


class Agent:
    """智能编码助手 Agent。

    使用 create_agent 架构，支持 middleware 扩展。
    """

    def __init__(
        self,
        model: BaseChatModel,
        tools: list[BaseTool],
        max_iterations: int = 10,
        enable_todo: bool = True,
    ) -> None:
        """初始化 Agent。

        Args:
            model: LangChain 聊天模型实例。
            tools: 可用工具列表。
            max_iterations: 最大迭代次数（用于 remaining_steps 计算）。
            enable_todo: 是否启用 Todo 功能（默认 True）。
        """
        # 构建 middleware 列表
        middleware: list[Any] = [ToolErrorHandler()]

        if enable_todo:
            middleware.append(TodoListMiddleware())

        # 创建 agent graph，使用 middleware 处理错误和任务管理
        self.graph = create_agent(
            model=model,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            middleware=middleware,
        )
        self.max_iterations = max_iterations
        self.enable_todo = enable_todo

    def run(self, user_input: str) -> str:
        """执行 Agent 主流程。

        Args:
            user_input: 用户输入的指令。

        Returns:
            Agent 执行结果（最终 AIMessage 内容，包含进度显示）。

        Raises:
            RuntimeError: 达到最大迭代次数仍未完成任务。
        """
        # 调用 graph，返回 state
        result = self.graph.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config={"recursion_limit": self.max_iterations + 2},
        )

        # 提取最终 AIMessage 内容
        final_content = self._extract_ai_content(result)

        # 如果启用了 todo，显示当前进度
        if self.enable_todo:
            todos = result.get("todos", [])
            if todos:
                pending = [t for t in todos if t["status"] == "pending"]
                in_progress = [t for t in todos if t["status"] == "in_progress"]

                # 如果还有未完成的任务，显示进度
                if pending or in_progress:
                    progress = self._format_todos_progress(todos)
                    return final_content + progress

        return final_content

    def _extract_ai_content(self, result: dict[str, Any]) -> str:
        """从结果中提取 AIMessage 内容。

        Args:
            result: graph.invoke 返回的 state。

        Returns:
            AIMessage 的 text 内容。
        """
        messages = result.get("messages", [])
        if not messages:
            return ""

        # 找到最后一条 AIMessage（非工具调用）
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                content = msg.content
                if content is None:
                    return ""

                # 处理列表类型内容（包含 thinking 和 text）
                if isinstance(content, list):
                    # 提取 type='text' 的内容
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            return item.get("text", "")
                    # 如果没有 text 类型，返回整个列表的字符串
                    return str(content)

                if isinstance(content, str):
                    return content
                return str(content)

        # 如果所有 AIMessage 都有 tool_calls，说明未完成
        raise RuntimeError("Agent 未完成任务，可能达到迭代限制")

    def _format_todos_progress(self, todos: list[dict[str, str]]) -> str:
        """格式化 todos 进度显示。

        Args:
            todos: 任务列表。

        Returns:
            格式化的进度字符串。
        """
        status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}
        progress = "\n\n当前进度：\n"
        for todo in todos:
            icon = status_icon.get(todo["status"], "❓")
            progress += f"{icon} {todo['content']}\n"
        return progress