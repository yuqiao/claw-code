# 阶段2: 新增文件操作工具

**让 agent 具备读写文件的能力，同时防止逃逸工作区。**

## 需求背景

阶段1 实现了 agent loop，但只有 bash 工具（白名单机制），缺少文件读写能力。

要完成完整的编码任务，agent 需要：
- 读取现有代码文件
- 写入新文件或修改文件
- 编辑文件中的特定内容

同时必须确保安全：只能在工作区内操作，不能访问系统敏感文件。

## 新增工具

| 工具 | 功能 | 参数 |
|------|------|------|
| `read_tool` | 读取文件内容 | `file_path` |
| `write_tool` | 写入文件（自动创建父目录） | `file_path`, `content` |
| `edit_tool` | 替换文件中字符串（仅首次出现） | `file_path`, `old_string`, `new_string` |

## 路径沙箱机制

### 核心原理

**工作区锁定**：启动时锁定当前工作目录作为工作区根路径。

```python
# sandbox.py
WORKSPACE_ROOT = Path(os.getcwd()).resolve()
```

**验证逻辑**：使用 `relative_to()` 检查路径是否在工作区内。

```python
def _is_safe_path(path: str) -> bool:
    try:
        target_path = Path(path).resolve()
        target_path.relative_to(WORKSPACE_ROOT)
        return True
    except ValueError:
        return False  # 不在工作区内
```

### 攻击防护

| 攻击方式 | 防护措施 |
|---------|---------|
| 路径遍历 `../../../etc/passwd` | `resolve()` 解析真实路径后检查 |
| 绝对路径 `/etc/passwd` | `relative_to()` 检查失败 |
| 符号链接逃逸 | `resolve()` 解析真实路径 |
| 空路径/无效路径 | 返回 False |

### 设计权衡

**为什么用 resolve()？**
- 解析相对路径为绝对路径
- 解析符号链接为真实路径
- 统一路径格式便于比较

**为什么用 relative_to()？**
- 如果 `target.relative_to(workspace)` 成功，说明 target 在 workspace 内
- 如果失败（抛出 ValueError），说明不在工作区内
- 这是 Python pathlib 推荐的"路径包含检查"方式

## 技术实现

### Read 工具

```python
# read.py
def execute_read(file_path: str) -> str:
    safe_path = get_safe_path(file_path)  # 沙箱验证

    if not safe_path.exists():
        return f"错误：文件 '{file_path}' 不存在"

    if not safe_path.is_file():
        return f"错误：'{file_path}' 不是文件"

    return safe_path.read_text(encoding="utf-8")
```

**返回值设计**：返回字符串而非抛异常，让模型看到友好的错误消息。

### Write 工具

```python
# write.py
def execute_write(file_path: str, content: str) -> str:
    safe_path = get_safe_path(file_path)

    # 自动创建父目录
    safe_path.parent.mkdir(parents=True, exist_ok=True)

    safe_path.write_text(content, encoding="utf-8")
    return f"成功写入 '{file_path}'，共 {len(content)} 字符"
```

**自动创建父目录**：避免"目录不存在"错误，简化 agent 使用。

### Edit 工具

```python
# edit.py
def execute_edit(file_path: str, old_string: str, new_string: str) -> str:
    safe_path = get_safe_path(file_path)

    content = safe_path.read_text(encoding="utf-8")

    if old_string not in content:
        return f"错误：未找到要替换的字符串"

    # 仅替换第一次出现
    new_content = content.replace(old_string, new_string, 1)

    safe_path.write_text(new_content, encoding="utf-8")
    return f"成功编辑 '{file_path}'，替换了 1 处"
```

**仅替换首次出现**：避免意外修改多处，让 agent 有精确控制。

## 工具注册

更新 `tools/__init__.py`：

```python
from claw_code.tools.bash import bash_tool
from claw_code.tools.edit import edit_tool
from claw_code.tools.read import read_tool
from claw_code.tools.write import write_tool

__all__ = ["bash_tool", "read_tool", "write_tool", "edit_tool"]
```

更新 `main.py`：

```python
from claw_code.tools import bash_tool, read_tool, write_tool, edit_tool

agent = Agent(
    model=model,
    tools=[bash_tool, read_tool, write_tool, edit_tool],
    max_iterations=max_iterations,
)
```

## 测试验证

### 测试覆盖

| 测试文件 | 测试数量 | 覆盖率 |
|---------|---------|--------|
| `test_sandbox.py` | 11 tests | 90% |
| `test_read.py` | 7 tests | 88% |
| `test_write.py` | 6 tests | 88% |
| `test_edit.py` | 7 tests | 88% |

**总计**: 31 tests passed

### 安全测试验证

```bash
# 读取工作区内文件 - 成功
python3 -c "from claw_code.tools.read import execute_read; print(execute_read('README.md'))"

# 读取工作区外文件 - 拒绝
python3 -c "from claw_code.tools.read import execute_read; execute_read('/etc/passwd')"
# ValueError: 路径 '/etc/passwd' 不在工作区内，禁止访问
```

## 心智模型

现在 agent 的能力扩展为：

```text
用户任务: "修改 README.md 中的项目描述"
    |
    v
LLM 思考: 需要先读取文件，找到目标字符串，再编辑
    |
    +-- read(README.md) ------> 获取文件内容
    |                              |
    |                              v
    |                         LLM 看到内容，定位目标
    |                              |
    +-- edit(README.md, old, new) --> 替换字符串
    |                              |
    v                              v
任务完成                         返回成功消息
```

**关键点**：工具结果（文件内容、编辑结果）都写回消息历史，让下一轮推理有完整上下文。

## 后续扩展

当前实现是"最小可用版本"，后续可扩展：

1. **read 增强**：支持行号范围、分页读取大文件
2. **write 增强**：追加模式、写入前确认
3. **edit 增强**：替换所有匹配、正则表达式
4. **安全增强**：文件类型白名单、大小限制

但记住：**YAGNI**（You Aren't Gonna Need It），只在有真实需求时才扩展。