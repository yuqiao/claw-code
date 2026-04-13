"""Edit 工具测试。"""

import os
import tempfile
from pathlib import Path

import pytest

from claw_code.tools.edit import execute_edit, edit_tool


class TestExecuteEdit:
    """测试 edit 命令执行。"""

    def test_execute_edit_when_string_found_should_replace(self) -> None:
        """找到字符串应成功替换。"""
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmp_dir:
            file_path = Path(tmp_dir) / "test_edit.txt"
            file_path.write_text("hello world")
            result = execute_edit(str(file_path), "hello", "hi")
            assert "成功编辑" in result
            assert file_path.read_text() == "hi world"

    def test_execute_edit_when_string_not_found_should_return_error(self) -> None:
        """未找到字符串应返回错误。"""
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmp_dir:
            file_path = Path(tmp_dir) / "test_edit.txt"
            file_path.write_text("hello world")
            result = execute_edit(str(file_path), "not_found", "replacement")
            assert "未找到" in result or "错误" in result

    def test_execute_edit_when_outside_workspace_should_raise_error(self) -> None:
        """工作区外路径应抛出 ValueError。"""
        with pytest.raises(ValueError, match="不在工作区内"):
            execute_edit("/etc/passwd", "old", "new")

    def test_execute_edit_should_replace_only_first_occurrence(self) -> None:
        """应仅替换第一次出现的字符串。"""
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as tmp_dir:
            file_path = Path(tmp_dir) / "test_edit.txt"
            file_path.write_text("hello hello hello")
            result = execute_edit(str(file_path), "hello", "hi")
            assert "成功编辑" in result
            assert file_path.read_text() == "hi hello hello"  # 只替换第一个

    def test_execute_edit_when_file_not_exists_should_return_error(self) -> None:
        """文件不存在应返回错误。"""
        result = execute_edit("nonexistent_file.txt", "old", "new")
        assert "不存在" in result or "错误" in result


class TestEditTool:
    """测试 LangChain StructuredTool。"""

    def test_edit_tool_should_have_correct_name(self) -> None:
        """工具名称应为 'edit'。"""
        assert edit_tool.name == "edit"

    def test_edit_tool_should_have_args_schema(self) -> None:
        """工具应有参数 schema。"""
        assert edit_tool.args_schema
        schema = edit_tool.args_schema.model_json_schema()
        assert "file_path" in schema["properties"]
        assert "old_string" in schema["properties"]
        assert "new_string" in schema["properties"]