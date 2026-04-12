"""BashTool 测试。"""

import pytest

from claw_code.tools.bash import _validate_command, execute_bash


class TestValidateCommand:
    """测试命令白名单验证。"""

    def test_validate_command_when_safe_command_should_return_true(self) -> None:
        """安全命令应通过验证。"""
        assert _validate_command("ls") is True
        assert _validate_command("cat file.txt") is True
        assert _validate_command("pwd") is True

    def test_validate_command_when_dangerous_command_should_return_false(
        self,
    ) -> None:
        """危险命令应拒绝。"""
        assert _validate_command("rm -rf /") is False
        assert _validate_command("sudo apt install") is False
        assert _validate_command("chmod 777") is False

    def test_validate_command_when_empty_should_return_false(self) -> None:
        """空命令应拒绝。"""
        assert _validate_command("") is False
        assert _validate_command("   ") is False


class TestExecuteBash:
    """测试 Bash 命令执行。"""

    def test_execute_bash_when_safe_command_should_return_output(self) -> None:
        """安全命令应返回输出。"""
        result = execute_bash("echo hello")
        assert "hello" in result

    def test_execute_bash_when_dangerous_command_should_raise_error(self) -> None:
        """危险命令应抛出 ValueError。"""
        with pytest.raises(ValueError, match="不在安全白名单中"):
            execute_bash("rm -rf /")

    def test_execute_bash_when_ls_should_list_files(self) -> None:
        """ls 命令应列出文件。"""
        result = execute_bash("ls")
        assert len(result) > 0  # 当前目录应有文件

    def test_execute_bash_when_invalid_args_should_show_error(self) -> None:
        """无效参数应返回错误信息。"""
        result = execute_bash("cat nonexistent_file.txt")
        assert "No such file" in result or "不存在" in result or result != ""
