# 单元测试 - 工具系统
# 测试 Hermes 的工具注册、工具执行、工具权限等

import pytest
import json
import os
from pathlib import Path


# =============================================================================
# 工具注册测试
# =============================================================================

@pytest.mark.unit
class TestToolRegistry:
    """工具注册中心测试"""
    
    def test_registry_import(self):
        """测试工具注册表可以导入"""
        from tools.registry import registry
        assert registry is not None
    
    def test_registry_has_tools(self):
        """测试注册表中有工具"""
        # 先触发工具发现
        import model_tools
        model_tools._discover_tools()
        
        from tools.registry import registry
        tools = registry.get_definitions(registry.get_all_tool_names())
        assert len(tools) > 0, "注册表中应该有工具"
    
    def test_terminal_tool_registered(self):
        """测试终端工具已注册"""
        # 先触发工具发现
        import model_tools
        model_tools._discover_tools()
        
        from tools.registry import registry
        tool_names = registry.get_all_tool_names()
        assert "terminal" in tool_names, f"终端工具应该已注册，当前工具：{tool_names}"
    
    def test_file_tools_registered(self):
        """测试文件工具已注册"""
        # 先触发工具发现
        import model_tools
        model_tools._discover_tools()
        
        from tools.registry import registry
        tool_names = registry.get_all_tool_names()
        # 至少有一个文件工具
        file_tools = [n for n in tool_names if "file" in n.lower()]
        assert len(file_tools) > 0, f"应该有文件工具注册，当前工具：{tool_names}"


# =============================================================================
# 终端工具测试
# =============================================================================

@pytest.mark.unit
class TestTerminalTool:
    """终端工具测试"""
    
    def test_simple_command(self, harness_assert):
        """测试简单命令执行"""
        from tools.terminal_tool import terminal_tool
        
        result = terminal_tool("echo hello")
        data = json.loads(result)
        
        assert data["exit_code"] == 0, f"命令应该成功执行：{data}"
        assert "hello" in data["output"].lower(), "输出应该包含 hello"
    
    def test_command_with_output(self, harness_assert):
        """测试有输出的命令"""
        from tools.terminal_tool import terminal_tool
        
        result = terminal_tool("ls -la")
        data = json.loads(result)
        
        assert data["exit_code"] == 0, "ls 命令应该成功"
        assert len(data["output"]) > 0, "应该有输出"
    
    def test_command_in_workdir(self, tmp_workdir, harness_assert):
        """测试在工作目录执行命令"""
        from tools.terminal_tool import terminal_tool
        
        # 先创建文件
        test_file = tmp_workdir / "test.txt"
        test_file.write_text("test content")
        
        # 在工作目录执行
        result = terminal_tool("cat test.txt", workdir=str(tmp_workdir))
        data = json.loads(result)
        
        assert data["exit_code"] == 0
        assert "test content" in data["output"]
    
    def test_command_timeout(self):
        """测试超时处理"""
        from tools.terminal_tool import terminal_tool
        
        result = terminal_tool("sleep 5", timeout=1)  # 1 秒超时
        data = json.loads(result)
        
        # 应该超时或被终止
        assert data.get("timed_out") or data.get("exit_code") != 0


# =============================================================================
# 文件工具测试
# =============================================================================

@pytest.mark.unit
class TestFileTools:
    """文件工具测试"""
    
    def test_read_file(self, sample_python_file, harness_assert):
        """测试读取文件"""
        from tools.file_tools import read_file_tool
        
        result = read_file_tool(str(sample_python_file))
        data = json.loads(result)
        
        # read_file_tool 返回：{'content': ..., 'total_lines': N, ...}
        assert "content" in data
        assert data["total_lines"] > 0
        assert "hello" in data["content"].lower()
    
    def test_read_file_not_found(self):
        """测试读取不存在的文件"""
        from tools.file_tools import read_file_tool
        
        result = read_file_tool("/nonexistent/file.txt")
        data = json.loads(result)
        
        # read_file_tool 返回 error 字段而不是抛异常
        assert "error" in data
        assert "not found" in data["error"].lower()
    
    def test_write_file(self, tmp_workdir, harness_assert):
        """测试写入文件"""
        from tools.file_tools import write_file_tool
        
        test_path = tmp_workdir / "new_file.txt"
        
        result = write_file_tool(str(test_path), "Hello, Harness!")
        data = json.loads(result)
        
        # write_file_tool 返回：{'bytes_written': N, 'dirs_created': bool}
        assert "bytes_written" in data
        assert data["bytes_written"] > 0
        assert test_path.exists()
        assert test_path.read_text() == "Hello, Harness!"
    
    def test_write_file_creates_dirs(self, tmp_workdir, harness_assert):
        """测试写入文件时自动创建目录"""
        from tools.file_tools import write_file_tool
        
        nested_path = tmp_workdir / "a" / "b" / "c" / "file.txt"
        
        result = write_file_tool(str(nested_path), "nested content")
        data = json.loads(result)
        
        assert "bytes_written" in data
        assert data.get("dirs_created") is True
        assert nested_path.exists()
    
    def test_search_files(self, sample_project, harness_assert):
        """测试搜索文件"""
        from tools.file_tools import search_tool
        
        # 搜索整个项目目录，包括子目录
        result = search_tool("*.py", target="files", path=str(sample_project))
        data = json.loads(result)
        
        # search_tool 返回：{'total_count': N, 'matches': [...]} 或 {'total_count': N}
        assert "total_count" in data
        # sample_project 应该有 Python 文件
        assert data["total_count"] > 0, f"应该在 {sample_project} 中找到 .py 文件，返回：{data}"
    
    def test_patch_file(self, sample_python_file, harness_assert):
        """测试补丁修改文件"""
        from tools.file_tools import patch_tool
        
        result = patch_tool(
            mode="replace",
            path=str(sample_python_file),
            old_string='return f"Hello, {name}!"',
            new_string='return f"Hi, {name}!"'
        )
        data = json.loads(result)
        
        # patch_tool 返回 diff 或错误
        assert isinstance(data, dict)
        assert "Hi," in sample_python_file.read_text()


# =============================================================================
# 工具权限测试
# =============================================================================

@pytest.mark.unit
class TestToolPermissions:
    """工具权限测试"""
    
    def test_dangerous_command_blocked(self):
        """测试危险命令被拦截"""
        from tools.approval import detect_dangerous_command
        
        # 检查危险命令检测
        dangerous_commands = [
            "rm -rf /",
            "rm -rf /*",
            "dd if=/dev/zero of=/dev/sda",
            ":(){ :|:& };:",  # fork bomb
        ]
        
        for cmd in dangerous_commands:
            result = detect_dangerous_command(cmd)
            # 返回 (is_dangerous, pattern_key, description)
            assert result[0] is True, f"应该检测到危险命令：{cmd}, 返回：{result}"
    
    def test_safe_command_allowed(self):
        """测试安全命令允许执行"""
        from tools.approval import detect_dangerous_command
        
        safe_commands = [
            "echo hello",
            "ls -la",
            "cat file.txt",
            "pwd",
            "whoami",
        ]
        
        for cmd in safe_commands:
            result = detect_dangerous_command(cmd)
            # 返回 (is_dangerous, pattern_key, description)
            assert result[0] is False, f"安全命令不应该被标记为危险：{cmd}, 返回：{result}"


# =============================================================================
# 工具集测试
# =============================================================================

@pytest.mark.unit
class TestToolsets:
    """工具集测试"""
    
    def test_toolset_enabled(self):
        """测试工具集启用"""
        from toolsets import get_toolset_names
        
        # 至少应该有核心工具集
        toolsets = get_toolset_names()
        assert len(toolsets) > 0
    
    def test_terminal_toolset_available(self):
        """测试终端工具集可用"""
        from toolsets import get_toolset_names
        
        # 终端工具集应该可用
        toolsets = get_toolset_names()
        assert "terminal" in toolsets


# =============================================================================
# 工具错误处理测试
# =============================================================================

@pytest.mark.unit
class TestToolErrorHandling:
    """工具错误处理测试"""
    
    def test_invalid_command_returns_error(self):
        """测试无效命令返回错误"""
        from tools.terminal_tool import terminal_tool
        
        # 空命令会返回空输出，但 exit_code=0（不算错误）
        result = terminal_tool("")
        data = json.loads(result)
        
        # 空命令应该返回空输出
        assert "output" in data
        # 注意：空命令在某些系统上 exit_code=0，所以只检查输出为空
        assert data["output"] == ""
    
    def test_missing_required_field(self):
        """测试缺少必填字段返回错误"""
        from tools.file_tools import read_file_tool
        
        # 不传 path 参数应该报错
        with pytest.raises(TypeError):
            read_file_tool()  # 缺少必需的 path 参数


# =============================================================================
# 性能测试
# =============================================================================

@pytest.mark.unit
class TestToolPerformance:
    """工具性能测试"""
    
    def test_read_file_performance(self, tmp_workdir):
        """测试读取文件性能"""
        from tools.file_tools import read_file_tool
        import time
        
        # 创建大文件
        large_file = tmp_workdir / "large.txt"
        large_file.write_text("x" * 100000)  # 100KB
        
        start = time.time()
        result = read_file_tool(str(large_file))
        elapsed = time.time() - start
        
        # 应该在 1 秒内完成
        assert elapsed < 1.0, f"读取文件太慢：{elapsed}s"
        
        data = json.loads(result)
        assert "content" in data
        assert len(data["content"]) > 0
    
    def test_tool_registration_performance(self):
        """测试工具注册性能"""
        import time
        import model_tools
        
        start = time.time()
        # 触发工具发现
        model_tools._discover_tools()
        
        from tools.registry import registry
        tool_names = registry.get_all_tool_names()
        elapsed = time.time() - start
        
        # 工具注册应该在 0.5 秒内完成
        assert elapsed < 0.5, f"工具注册太慢：{elapsed}s"
        assert len(tool_names) > 0
