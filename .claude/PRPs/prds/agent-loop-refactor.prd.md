# Agent Loop 重构 - create_agent + middleware

## Problem Statement

开发者当前使用手动实现的 while loop + bind_tools 方式构建 agent，缺少扩展性和记忆支持，每次调用都重置消息历史，无法在多轮对话中保持上下文。重复造轮子而非利用 LangChain 已有的 agent 框架。

## Evidence

- docs/s01-agent-loop.md 明确指出应使用 create_agent + middleware 模式
- 当前 agent.py 93 行代码手动实现 loop，无扩展机制
- LangChain 库已包含完整的 middleware 系统（wrap_tool_call, before_model 等）

## Proposed Solution

使用 LangChain 的 `create_agent` + middleware 模式重构 agent loop，替代当前手动实现。通过 middleware 实现工具错误处理，保持 API 接口一致性，为后续扩展（记忆持久化、更多工具）打下基础。

## Key Hypothesis

We believe **create_agent + middleware 架构** will **提供扩展性和更好的错误处理** for **开发者**.
We'll know we're right when **CLI 验证成功执行 bash 工具列出目录文件**。

## What We're NOT Building

- 记忆持久化（checkpointer） - 先实现基础功能，后续扩展
- 多工具支持 - 仅保留 bash 工具
- 流式输出 - 先实现基本功能
- 结构化输出（response_format） - MVP 不需要

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| CLI 可用性 | 执行 `claw-code --verify` 成功 | 命令执行返回正确结果 |
| bash 工具执行 | 成功列出目录文件 | 输出包含文件列表 |
| 错误处理 | middleware 捕获工具错误 | 错误时返回友好消息而非崩溃 |

## Open Questions

- [x] 返回值格式适配：如何从 CompiledStateGraph 输出中提取最终消息
- [x] API 字符串语法：阿里云模型名称是否需要特殊处理

---

## Users & Context

**Primary User**
- **Who**: claw-code 项目开发者
- **Current behavior**: 使用手动 loop，每次调用重置上下文
- **Trigger**: 发现 LangChain 有更好的 agent 模式
- **Success state**: CLI 正常工作，代码更简洁，可扩展

**Job to Be Done**
When **需要扩展 agent 功能**，I want to **使用成熟的框架而非手动实现**，so I can **快速添加新功能而不修改核心代码**。

**Non-Users**
需要复杂多 agent 系统的用户 - 这是后续阶段

---

## Solution Detail

### Core Capabilities (MoSCoW)

| Priority | Capability | Rationale |
|----------|------------|-----------|
| Must | create_agent 替换手动 loop | 核心重构，解决扩展性问题 |
| Must | middleware 错误处理 | 替代手动 try/catch，更优雅 |
| Must | CLI 兼容性验证 | 确保现有功能正常 |
| Should | 保持 API 接口不变 | main.py 无需大改 |
| Could | 更好的文本输出格式 | 利用 graph.stream() |
| Won't | checkpointer 记忆 | 后续阶段 |

### MVP Scope

替换 agent.py 的 Agent 类实现：
- 使用 `create_agent(model, tools=[bash_tool], system_prompt=...)`
- 添加错误处理 middleware
- 保持 `.run()` 方法接口

### User Flow

```text
CLI 启动
    ↓
create_agent 创建 graph
    ↓
用户输入
    ↓
graph.invoke({"messages": [user_input]})
    ↓
LLM 调用 → bash 工具 → ToolMessage
    ↓
继续循环直到无 tool_calls
    ↓
提取最终 AIMessage 返回
```

---

## Technical Approach

**Feasibility**: HIGH

**Architecture Notes**
- 使用 `langchain.agents.create_agent` 而非手动 StateGraph
- middleware 通过 `@wrap_tool_call` 装饰器实现
- 返回 CompiledStateGraph，调用方式为 `.invoke()` 或 `.stream()`

**代码改动范围**
- `agent.py`: 完全重写（约 30 行 vs 93 行）
- `main.py`: 调用方式从 `agent.run()` 改为适配 graph 输出
- `tools/bash.py`: 无需改动

**Technical Risks**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| 返回格式变化 | M | 编写适配函数提取最终消息 |
| 阿里云模型兼容 | L | 继续用 ChatAnthropic 实例 |
| middleware 学习曲线 | L | 参考 docs/s01-agent-loop.md 示例 |

---

## Implementation Phases

<!--
  STATUS: pending | in-progress | complete
  PARALLEL: phases that can run concurrently
  DEPENDS: phases that must complete first
  PRP: link to generated plan file once created
-->

| # | Phase | Description | Status | Parallel | Depends | PRP Plan |
|---|-------|-------------|--------|----------|---------|----------|
| 1 | 重写 agent.py | create_agent + middleware 替换手动 loop | pending | - | - | - |
| 2 | 适配 main.py | 调用方式适配 graph 输出格式 | pending | - | 1 | - |
| 3 | CLI 验证 | 运行 `claw-code --verify` 测试 | pending | - | 2 | - |

### Phase Details

**Phase 1: 重写 agent.py**
- **Goal**: 使用 create_agent 替换手动 while loop
- **Scope**: 
  - 导入 `langchain.agents.create_agent` 和 middleware
  - 实现 `@wrap_tool_call` 错误处理 middleware
  - 保持 `Agent` 类接口（`__init__`, `run`）
- **Success signal**: 类型检查通过，无语法错误

**Phase 2: 适配 main.py**
- **Goal**: 调用方式适配 CompiledStateGraph 输出
- **Scope**:
  - 提取最终 AIMessage 的逻辑
  - 保持 Markdown 输出格式
- **Success signal**: 代码编译无错误

**Phase 3: CLI 验证**
- **Goal**: 验证重构后功能正常
- **Scope**: 运行 `claw-code --verify`，检查输出
- **Success signal**: 成功列出目录文件

### Parallelism Notes

Phase 1 和 2 必须顺序执行（1 → 2 → 3）

---

## Decisions Log

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Agent 模式 | create_agent | 手动 StateGraph | 文档推荐，更简单 |
| 错误处理 | middleware | 手动 try/catch | 可扩展，更优雅 |
| 记忆 | MVP 不实现 | checkpointer | 先验证基础功能 |

---

## Research Summary

**Market Context**
LangChain 提供 `create_agent` 作为推荐的 agent 构建方式，配套 middleware 系统支持各种扩展场景（错误处理、重试、记忆、工具限制等）。

**Technical Context**
- 已安装 langchain.agents 模块（factory.py, middleware/*.py）
- create_agent 返回 CompiledStateGraph，调用方式为 `.invoke({"messages": [...]})`
- middleware 通过 `@wrap_tool_call` 装饰器拦截工具调用
- docs/s01-agent-loop.md 提供示例代码模板

---

*Generated: 2026-04-12*
*Status: DRAFT - needs implementation*