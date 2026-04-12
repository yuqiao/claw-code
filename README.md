# claw-code

构建一个主要为了辅助编码的 agent。

## 项目结构

```
claw-code/
├── src/claw_code/       # 源代码（src layout）
│   ├── agent.py         # Agent 核心实现
│   ├── main.py          # CLI 入口
│   ├── config.py        # 配置管理
│   └── tools/           # 工具模块
│       └── bash.py      # Bash 工具
├── tests/               # 测试代码
├── pyproject.toml       # 项目配置
├── .env.example         # 环境变量示例
└── README.md
```

## 安装

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 ANTHROPIC_API_KEY
```

## 环境变量配置

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | 是 |
| `ANTHROPIC_MODEL` | 模型名称（默认 claude-sonnet-4-6） | 否 |
| `ANTHROPIC_BASE_URL` | API 基础 URL（用于代理） | 否 |

## CLI 使用

```bash
# 启动交互式 agent loop
claw-code

# 指定最大迭代次数
claw-code --max-iter 5
```

交互式命令：
- 输入任务后 agent 会思考并执行
- 输入 `exit` 或 `quit` 退出
- `Ctrl+C` 中断当前任务，继续循环

## Python API 使用

```python
from claw_code import Agent, bash_tool
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-sonnet-4-6")
agent = Agent(model, tools=[bash_tool])
result = agent.run("帮我列出当前目录的文件")
```

## 开发

```bash
# 运行测试
pytest

# 代码格式化
black .
ruff check .

# 类型检查
mypy .
```

---

agent主线: `用户输入 -> 模型思考 -> 调工具 -> 拿结果 -> 继续思考 -> 完成`

按阶段实现: 
1. ✅ 先实现一个能工作的agent, 并增加bash工具.
2. ✅ 使用 typer 构建 CLI 命令入口，实现 agent loop.
3. 再补安全、扩展、记忆和恢复。
4. 再把临时清单升级成持久化任务系统。
5. 最后再进入多 agent、隔离执行和外部工具平台。

# 技术栈

- python 3.10+
- langchain
- langchain-anthropic
- typer（CLI）