"""CLI 入口模块。

提供交互式 agent loop，类似 Claude Code 的 REPL 体验。
支持 --verify 参数执行一轮验证测试。
"""

import os
from typing import Annotated

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from claw_code.agent import Agent
from claw_code.tools import bash_tool, read_tool, write_tool, edit_tool

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


def create_model() -> "ChatAnthropic":
    """创建 ChatAnthropic 模型实例。

    Returns:
        ChatAnthropic 模型实例。
    """
    from langchain_anthropic import ChatAnthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    assert api_key is not None  # check_api_key 已验证

    base_url = os.getenv("ANTHROPIC_BASE_URL")
    if base_url:
        return ChatAnthropic(  # type: ignore[call-arg]
            model=get_model(),
            anthropic_api_key=api_key,
            anthropic_api_url=base_url,
        )
    else:
        return ChatAnthropic(  # type: ignore[call-arg]
            model=get_model(),
            anthropic_api_key=api_key,
        )


def run_verify(max_iterations: int = 3) -> None:
    """执行一轮验证测试。

    Args:
        max_iterations: 最大迭代次数。
    """
    console.print("[bold green]claw-code 验证测试[/bold green]")
    console.print(f"[green]✓ API Key 已配置[/green]")
    console.print(f"[green]✓ 模型: {get_model()}[/green]")

    base_url = os.getenv("ANTHROPIC_BASE_URL")
    if base_url:
        console.print(f"[green]✓ Base URL: {base_url}[/green]")

    # 初始化 Agent
    model = create_model()
    agent = Agent(
        model,
        tools=[bash_tool, read_tool, write_tool, edit_tool],
        max_iterations=max_iterations,
    )
    console.print("[green]✓ Agent 已初始化[/green]")

    # 运行一轮测试
    console.print("\n[yellow]测试任务: 列出当前目录文件[/yellow]")
    try:
        result = agent.run("列出当前目录的文件")
        console.print("\n[bold blue]Agent 响应:[/bold blue]")
        console.print(Markdown(result))
        console.print("\n[green]✓ CLI 验证成功[/green]")
    except Exception as e:
        console.print(f"\n[red]✗ 错误: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def main(
    max_iterations: Annotated[
        int, typer.Option("--max-iter", help="最大迭代次数")
    ] = 10,
    verify: Annotated[
        bool, typer.Option("--verify", help="执行一轮验证测试后退出")
    ] = False,
) -> None:
    """启动 claw-code 交互式 agent loop。"""
    check_api_key()

    # 验证模式：执行一轮测试后退出
    if verify:
        run_verify(max_iterations)
        return

    # 初始化 Agent
    model = create_model()
    agent = Agent(
        model,
        tools=[bash_tool, read_tool, write_tool, edit_tool],
        max_iterations=max_iterations,
    )

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
