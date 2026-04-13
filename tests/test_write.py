"""Write 工具测试。"""

import os
import tempfile
from pathlib import Path

import pytest

from claw_code.tools.write import execute_write, write_tool


class TestExecuteWrite:
    """测试 write 命令执行。"""

    def test_execute_write_when_new_file_should_create(self) -> None:
        """新文件应成功创建。"""
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmp_dir:
            file_path = Path(tmp_dir) / "test_write.txt"
            result = execute_write(str(file_path), "hello world")
            assert "成功写入" in result
            assert file_path.exists()
            assert file_path.read_text() == "hello world"

    def test_execute_write_should_create_parent_directory(self) -> None:
        """应自动创建父目录。"""
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmp_dir:
            file_path = Path(tmp_dir) / "subdir" / "nested" / "test.txt"
            result = execute_write(str(file_path), "nested content")
            assert "成功写入" in result
            assert file_path.exists()
            assert file_path.parent.exists()  # 父目录已创建

    def test_execute_write_when_outside_workspace_should_raise_error(self) -> None:
        """工作区外路径应抛出 ValueError。"""
        with pytest.raises(ValueError, match="不在工作区内"):
            execute_write("/etc/passwd", "test content")

    def test_execute_write_should_overwrite_existing_file(self) -> None:
        """应覆盖已存在的文件。"""
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmp_dir:
            file_path = Path(tmp_dir) / "existing.txt"
            file_path.write_text("old content")
            result = execute_write(str(file_path), "new content")
            assert "成功写入" in result
            assert file_path.read_text() == "new content"


class TestWriteTool:
    """测试 LangChain StructuredTool。"""

    def test_write_tool_should_have_correct_name(self) -> None:
        """工具名称应为 'write'。"""
        assert write_tool.name == "write"

    def test_write_tool_should_have_args_schema(self) -> None:
        """工具应有参数 schema。"""
        assert write_tool.args_schema
        schema = write_tool.args_schema.model_json_schema()
        assert "file_path" in schema["properties"]
        assert "content" in schema["properties"]