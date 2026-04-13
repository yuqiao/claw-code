"""Read 工具测试。"""

import os
import tempfile
from pathlib import Path

import pytest

from claw_code.tools.read import execute_read, read_tool


class TestExecuteRead:
    """测试 read 命令执行。"""

    def test_execute_read_when_file_exists_should_return_content(self) -> None:
        """存在的文件应返回内容。"""
        # 创建临时测试文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, dir=os.getcwd()
        ) as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = execute_read(temp_path)
            assert "test content" in result
        finally:
            Path(temp_path).unlink()

    def test_execute_read_when_file_not_exists_should_return_error(self) -> None:
        """不存在的文件应返回错误消息。"""
        result = execute_read("nonexistent_file.txt")
        assert "不存在" in result or "错误" in result

    def test_execute_read_when_outside_workspace_should_raise_error(self) -> None:
        """工作区外路径应抛出 ValueError。"""
        with pytest.raises(ValueError, match="不在工作区内"):
            execute_read("/etc/passwd")

    def test_execute_read_when_directory_should_return_error(self) -> None:
        """目录路径应返回错误消息。"""
        result = execute_read("src")
        assert "不是文件" in result or "错误" in result


class TestReadTool:
    """测试 LangChain StructuredTool。"""

    def test_read_tool_should_have_correct_name(self) -> None:
        """工具名称应为 'read'。"""
        assert read_tool.name == "read"

    def test_read_tool_should_have_description(self) -> None:
        """工具应有描述。"""
        assert read_tool.description
        assert "工作区" in read_tool.description

    def test_read_tool_should_have_args_schema(self) -> None:
        """工具应有参数 schema。"""
        assert read_tool.args_schema
        schema = read_tool.args_schema.schema()
        assert "file_path" in schema["properties"]