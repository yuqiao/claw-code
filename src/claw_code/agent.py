"""Agent 核心实现模块。

实现思考 -> 调工具 -> 拿结果 -> 继续思考循环。
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

# 系统提示词
SYSTEM_PROMPT = """你是一个智能编码助手。
你可以使用 bash 工具执行安全的命令来帮助用户完成任务。
可用的命令包括：ls, cat, pwd, echo, grep, find, head, tail, wc, sort,
uniq, diff, tree, mkdir, touch。
在执行命令时要谨慎，确保命令安全后再执行。
完成任务后，总结你做了什么并给出最终答案。"""


class Agent:
    """智能编码助手 Agent。

    主线流程：用户输入 -> 模型思考 -> 调工具 -> 拿结果 -> 继续思考 -> 完成
    """

    def __init__(
        self,
        model: BaseChatModel,
        tools: list[BaseTool],
        max_iterations: int = 10,
    ) -> None:
        """初始化 Agent。

        Args:
            model: LangChain 聊天模型实例。
            tools: 可用工具列表。
            max_iterations: 最大迭代次数（防止无限循环）。
        """
        self.model = model.bind_tools(tools)
        self.tools_by_name = {t.name: t for t in tools}
        self.max_iterations = max_iterations

    def run(self, user_input: str) -> str:
        """执行 Agent 主流程。

        Args:
            user_input: 用户输入的指令。

        Returns:
            Agent 执行结果。

        Raises:
            RuntimeError: 达到最大迭代次数仍未完成任务。
        """
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_input),
        ]

        for _ in range(self.max_iterations):
            response = self.model.invoke(messages)
            messages.append(response)

            # 无工具调用，返回最终答案
            if not response.tool_calls:
                content = response.content
                if content is None:
                    return ""
                if isinstance(content, str):
                    return content
                # 处理 list 类型内容
                return str(content)

            # 执行所有工具调用
            for tool_call in response.tool_calls:
                tool = self.tools_by_name.get(tool_call["name"])
                if tool is None:
                    tool_result = f"错误：未知工具 '{tool_call['name']}'"
                else:
                    try:
                        tool_result = tool.invoke(tool_call["args"])
                    except Exception as e:
                        tool_result = f"工具执行错误：{e}"

                messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call["id"],
                    )
                )

        # 达到最大迭代次数
        raise RuntimeError(f"达到最大迭代次数 {self.max_iterations}，任务未完成")
