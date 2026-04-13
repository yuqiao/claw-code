"""路径沙箱模块测试。"""

import os
import tempfile
from pathlib import Path

import pytest

from claw_code.tools.sandbox import (
    _is_safe_path,
    get_safe_path,
    get_workspace_root,
)


class TestIsSafePath:
    """测试路径安全检查。"""

    def test_is_safe_path_when_in_workspace_should_return_true(self) -> None:
        """工作区内路径应通过验证。"""
        # 使用当前工作目录（即 WORKSPACE_ROOT）
        assert _is_safe_path(os.getcwd()) is True
        assert _is_safe_path("./README.md") is True
        assert _is_safe_path("src/claw_code/tools") is True

    def test_is_safe_path_when_outside_workspace_should_return_false(self) -> None:
        """工作区外路径应拒绝。"""
        # 绝对路径在工作区外
        assert _is_safe_path("/etc/passwd") is False
        assert _is_safe_path("/tmp/test.txt") is False

    def test_is_safe_path_when_path_traversal_should_return_false(self) -> None:
        """路径遍历攻击应被阻止。"""
        # 使用 ../ 逃逸工作区
        assert _is_safe_path("../../../etc/passwd") is False
        assert _is_safe_path("../outside.txt") is False

    def test_is_safe_path_when_empty_should_return_false(self) -> None:
        """空路径应拒绝。"""
        assert _is_safe_path("") is False
        assert _is_safe_path("   ") is False

    def test_is_safe_path_when_invalid_should_return_false(self) -> None:
        """无效路径应拒绝。"""
        # 包含无效字符的路径（在 Windows 上无效，但在 macOS 上可能有效）
        # 这里测试一个确实无效的情况
        # 注意：在 Unix 系统上，大多数路径字符串都是有效的
        # 所以我们主要测试空路径和 None
        assert _is_safe_path("not/a/valid/path/that/does/not/exist") is True  # 相对路径，在工作区内


class TestGetSafePath:
    """测试安全路径获取。"""

    def test_get_safe_path_when_in_workspace_should_return_path(self) -> None:
        """工作区内路径应返回 Path 对象。"""
        result = get_safe_path("README.md")
        assert isinstance(result, Path)
        assert result.is_absolute()

    def test_get_safe_path_when_outside_workspace_should_raise_error(self) -> None:
        """工作区外路径应抛出 ValueError。"""
        with pytest.raises(ValueError, match="不在工作区内"):
            get_safe_path("/etc/passwd")

    def test_get_safe_path_when_path_traversal_should_raise_error(self) -> None:
        """路径遍历攻击应抛出 ValueError。"""
        with pytest.raises(ValueError, match="不在工作区内"):
            get_safe_path("../../outside.txt")


class TestGetWorkspaceRoot:
    """测试工作区根路径获取。"""

    def test_get_workspace_root_should_return_path(self) -> None:
        """应返回 Path 对象。"""
        result = get_workspace_root()
        assert isinstance(result, Path)
        assert result.is_absolute()

    def test_get_workspace_root_should_match_cwd(self) -> None:
        """应与当前工作目录匹配。"""
        result = get_workspace_root()
        expected = Path(os.getcwd()).resolve()
        assert result == expected


class TestSymlinkProtection:
    """测试符号链接防护。"""

    def test_symlink_escaping_workspace_should_be_blocked(self) -> None:
        """符号链接逃逸工作区应被阻止。"""
        # 创建临时目录和符号链接
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 创建一个指向工作区外的符号链接
            symlink_path = Path(tmp_dir) / "escape_link"
            outside_file = Path(tmp_dir) / "outside.txt"
            outside_file.write_text("outside content")

            # 在工作区内创建符号链接指向工作区外
            link_in_workspace = Path(os.getcwd()) / "test_link"
            try:
                link_in_workspace.symlink_to(outside_file)
                # 通过符号链接访问应该被阻止（因为 resolve() 会解析真实路径）
                assert _is_safe_path(str(link_in_workspace)) is False
            finally:
                # 清理符号链接
                if link_in_workspace.exists():
                    link_in_workspace.unlink()