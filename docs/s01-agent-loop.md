# 阶段1: agent loop 主循环实现

**把“模型 + 工具”连接成一个能持续推进任务的主循环。**

## 先解释几个名词

### 什么是 loop

`loop` 就是循环。

这里的意思不是“程序死循环”，而是：

> 只要任务还没做完，系统就继续重复同一套步骤。

### 什么是 turn

`turn` 可以理解成“一轮”。

最小版本里，一轮通常包含：

1. 把当前消息发给模型
2. 读取模型回复
3. 如果模型调用了工具，就执行工具
4. 把工具结果写回消息历史

然后才进入下一轮。

### 什么是 tool_result

`tool_result` 就是工具执行结果。

它不是随便打印在终端上的日志，而是：

> 要重新写回对话历史、让模型下一轮真的能看见的结果块。

### 什么是 state

`state` 是“当前运行状态”。

第一次看到这个词时，你可以先把它理解成：

> 主循环继续往下走时，需要一直带着走的那份数据。

最小版本里，最重要的状态就是：

- `messages`
- 当前是第几轮
- 这一轮结束后为什么还要继续

## 最小心智模型

先把整个 agent 想成下面这条回路：

```text
user message
   |
   v
LLM
   |
   +-- 普通回答 ----------> 结束
   |
   +-- tool_use ----------> 执行工具
                              |
                              v
                         tool_result
                              |
                              v
                         写回 messages
                              |
                              v
                         下一轮继续
```

这条图里最关键的，不是“有一个 while True”。

真正关键的是这句：

**工具结果必须重新进入消息历史，成为下一轮推理的输入。**


## 技术栈要求
- 使用create_agent, 可参考库:  .venv/lib/python3.13/site-packages/langchain/ , 例子代码如下:

``` python 
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage


@wrap_tool_call
def handle_tool_errors(request, handler):
    """使用自定义消息处理工具执行错误。"""
    try:
        return handler(request)
    except Exception as e:
        # 向模型返回自定义错误消息
        return ToolMessage(
            content=f"工具错误：请检查您的输入并重试。({str(e)})",
            tool_call_id=request.tool_call["id"]
        )

agent = create_agent(
    model="openai:gpt-4o",
    tools=[search, get_weather],
    middleware=[handle_tool_errors]
)

```
