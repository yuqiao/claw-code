"""CLI 入口模块。

提供交互式 agent loop，类似 Claude Code 的 REPL 体验。
"""

import os
from typing import Annotated

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from claw_code.agent import Agent
from claw_code.tools.bash import bash_tool

# 加载环境变量
load_dotenv()

app = typer.Typer()
console = Console()


def get_model() -> str:
    """获取模型名称，优先使用环境变量。

    Returns:
        模型名称字符串。
    """
    return os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")


def check_api_key() -> None:
    """检查 API Key 是否配置。

    Raises:
        typer.Exit: API Key 未配置时退出程序。
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]错误: 未配置 ANTHROPIC_API_KEY[/red]")
        console.print("请设置环境变量或在 .env 文件中配置")
        raise typer.Exit(1)


@app.command()
def main(
    max_iterations: Annotated[
        int, typer.Option("--max-iter", help="最大迭代次数")
    ] = 10,
) -> None:
    """启动 claw-code 交互式 agent loop。"""
    check_api_key()

    # 初始化 Agent（使用 Anthropic API）
    from langchain_anthropic import ChatAnthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    assert api_key is not None  # check_api_key 已验证

    base_url = os.getenv("ANTHROPIC_BASE_URL")
    if base_url:
        model = ChatAnthropic(  # type: ignore[call-arg]
            model=get_model(),
            anthropic_api_key=api_key,
            anthropic_base_url=base_url,
        )
    else:
        model = ChatAnthropic(  # type: ignore[call-arg]
            model=get_model(),
            anthropic_api_key=api_key,
        )

    agent = Agent(model, tools=[bash_tool], max_iterations=max_iterations)

    console.print("[bold green]claw-code[/bold green] - 智能编码助手")
    console.print(f"模型: {get_model()}")
    console.print("输入 'exit' 或 'quit' 退出，Ctrl+C 中断当前任务")

    while True:
        try:
            user_input = typer.prompt("\n> ", default="", show_default=False)
            if not user_input.strip():
                continue
            if user_input.lower() in ("exit", "quit"):
                console.print("[yellow]再见！[/yellow]")
                break

            # 执行 Agent
            result = agent.run(user_input)
            console.print(Markdown(result))

        except KeyboardInterrupt:
            console.print("\n[yellow]任务已中断[/yellow]")
            continue
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")


if __name__ == "__main__":
    app()
