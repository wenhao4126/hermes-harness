# 集成测试 - 工具间协作测试
# 测试多个工具一起工作的场景（不使用 Mock Agent）

import pytest
import json
import time
from pathlib import Path


# =============================================================================
# 终端 + 文件系统协作测试
# =============================================================================

@pytest.mark.integration
class TestTerminalFilesystemIntegration:
    """终端和文件系统协作测试"""
    
    def test_create_file_then_read_with_terminal(self, tmp_workdir):
        """测试用终端创建文件然后读取"""
        from tools.terminal_tool import terminal_tool
        from tools.file_tools import read_file_tool
        
        test_file = tmp_workdir / "terminal_created.txt"
        
        # 1. 用终端命令创建文件
        result1 = terminal_tool(f"echo 'Hello from terminal' > {test_file}")
        data1 = json.loads(result1)
        assert data1["exit_code"] == 0
        
        # 2. 用文件工具读取
        result2 = read_file_tool(str(test_file))
        data2 = json.loads(result2)
        assert "Hello from terminal" in data2["content"]
    
    def test_list_then_read_files(self, tmp_workdir):
        """测试列出文件然后读取"""
        from tools.terminal_tool import terminal_tool
        from tools.file_tools import read_file_tool
        
        # 创建测试文件
        (tmp_workdir / "file1.txt").write_text("Content 1")
        (tmp_workdir / "file2.txt").write_text("Content 2")
        
        # 1. 用终端列出文件
        result1 = terminal_tool(f"ls {tmp_workdir}/*.txt")
        data1 = json.loads(result1)
        assert "file1.txt" in data1["output"]
        assert "file2.txt" in data1["output"]
        
        # 2. 读取第一个文件
        result2 = read_file_tool(str(tmp_workdir / "file1.txt"))
        data2 = json.loads(result2)
        assert "Content 1" in data2["content"]
    
    def test_terminal_search_file_read(self, tmp_workdir):
        """测试终端搜索 + 文件读取"""
        from tools.terminal_tool import terminal_tool
        from tools.file_tools import read_file_tool
        
        # 创建测试文件
        (tmp_workdir / "test1.py").write_text("# Python 1")
        (tmp_workdir / "test2.py").write_text("# Python 2")
        (tmp_workdir / "readme.txt").write_text("# Readme")
        
        # 1. 用终端搜索 Python 文件
        result1 = terminal_tool(f"find {tmp_workdir} -name '*.py'")
        data1 = json.loads(result1)
        assert "test1.py" in data1["output"]
        
        # 2. 读取找到的文件
        result2 = read_file_tool(str(tmp_workdir / "test1.py"))
        data2 = json.loads(result2)
        assert "# Python 1" in data2["content"]


# =============================================================================
# 文件工具间协作测试
# =============================================================================

@pytest.mark.integration
class TestFileToolsIntegration:
    """文件工具间协作测试"""
    
    def test_write_then_read_then_patch(self, tmp_workdir):
        """测试写入→读取→补丁修改流程"""
        from tools.file_tools import write_file_tool, read_file_tool, patch_tool
        
        test_file = tmp_workdir / "workflow_test.txt"
        
        # 1. 写入文件
        result1 = write_file_tool(str(test_file), "Initial content\nLine 2")
        data1 = json.loads(result1)
        assert data1["bytes_written"] > 0
        
        # 2. 读取验证
        result2 = read_file_tool(str(test_file))
        data2 = json.loads(result2)
        assert "Initial content" in data2["content"]
        
        # 3. 补丁修改
        result3 = patch_tool(
            mode="replace",
            path=str(test_file),
            old_string="Initial content",
            new_string="Modified content"
        )
        data3 = json.loads(result3)
        assert isinstance(data3, dict)
        
        # 4. 再次读取验证
        result4 = read_file_tool(str(test_file))
        data4 = json.loads(result4)
        assert "Modified content" in data4["content"]
        assert "Initial content" not in data4["content"]
    
    def test_search_then_batch_read(self, tmp_workdir):
        """测试搜索然后批量读取"""
        from tools.file_tools import search_tool, read_file_tool
        
        # 创建多个文件
        for i in range(3):
            (tmp_workdir / f"batch_{i}.txt").write_text(f"Batch content {i}")
        
        # 1. 搜索文件
        result1 = search_tool("batch_*.txt", path=str(tmp_workdir), target="files")
        data1 = json.loads(result1)
        assert data1["total_count"] >= 3
        
        # 2. 批量读取
        contents = []
        for i in range(3):
            result = read_file_tool(str(tmp_workdir / f"batch_{i}.txt"))
            data = json.loads(result)
            contents.append(data["content"])
        
        # 3. 验证都读到了
        assert any("Batch content 0" in c for c in contents)
        assert any("Batch content 1" in c for c in contents)
        assert any("Batch content 2" in c for c in contents)


# =============================================================================
# 危险命令检测 + 终端执行协作测试
# =============================================================================

@pytest.mark.integration
class TestSecurityTerminalIntegration:
    """安全检测和终端执行协作测试"""
    
    def test_dangerous_command_detection(self):
        """测试危险命令检测"""
        from tools.approval import detect_dangerous_command
        from tools.terminal_tool import terminal_tool
        
        # 危险命令列表
        dangerous = [
            "rm -rf /",
            "rm -rf /*",
            "dd if=/dev/zero",
        ]
        
        for cmd in dangerous:
            result = detect_dangerous_command(cmd)
            assert result[0] is True, f"应该检测到危险命令：{cmd}"
    
    def test_safe_command_execution(self, tmp_workdir):
        """测试安全命令执行"""
        from tools.approval import detect_dangerous_command
        from tools.terminal_tool import terminal_tool
        
        # 安全命令
        safe_commands = [
            f"ls {tmp_workdir}",
            f"echo test > {tmp_workdir / 'test.txt'}",
            f"cat {tmp_workdir / 'test.txt'}",
        ]
        
        for cmd in safe_commands:
            # 1. 先检测
            result = detect_dangerous_command(cmd)
            assert result[0] is False, f"安全命令被误判：{cmd}"
            
            # 2. 执行
            exec_result = terminal_tool(cmd)
            data = json.loads(exec_result)
            assert data["exit_code"] == 0, f"命令执行失败：{cmd}"


# =============================================================================
# 工具集协作测试
# =============================================================================

@pytest.mark.integration
class TestToolsetIntegration:
    """工具集协作测试"""
    
    def test_terminal_and_file_toolsets_available(self):
        """测试终端和文件工具集都可用"""
        from toolsets import get_toolset_names
        from tools.registry import registry
        import model_tools
        
        # 1. 触发工具发现
        model_tools._discover_tools()
        
        # 2. 检查工具集
        toolsets = get_toolset_names()
        assert "terminal" in toolsets
        assert "file" in toolsets
        
        # 3. 检查工具有多少
        tool_names = registry.get_all_tool_names()
        terminal_tools = [n for n in tool_names if "terminal" in n.lower() or "bash" in n.lower()]
        file_tools = [n for n in tool_names if "file" in n.lower() or "read" in n.lower() or "write" in n.lower()]
        
        assert len(terminal_tools) > 0, "应该有终端工具"
        assert len(file_tools) > 0, "应该有文件工具"


# =============================================================================
# 性能相关集成测试
# =============================================================================

@pytest.mark.integration
class TestPerformanceIntegration:
    """性能相关集成测试"""
    
    def test_large_file_write_then_read(self, tmp_workdir):
        """测试大文件写入然后读取"""
        from tools.file_tools import write_file_tool, read_file_tool
        import time
        
        large_file = tmp_workdir / "large.txt"
        large_content = "Line\n" * 1000  # 1000 行
        
        # 1. 写入大文件
        start = time.time()
        result1 = write_file_tool(str(large_file), large_content)
        write_time = time.time() - start
        
        data1 = json.loads(result1)
        assert data1["bytes_written"] > 0
        assert write_time < 1.0, f"写入太慢：{write_time}s"
        
        # 2. 读取大文件
        start = time.time()
        result2 = read_file_tool(str(large_file))
        read_time = time.time() - start
        
        data2 = json.loads(result2)
        assert len(data2["content"]) > 0
        assert read_time < 1.0, f"读取太慢：{read_time}s"
    
    def test_multiple_sequential_operations(self, tmp_workdir):
        """测试多个顺序操作的性能"""
        from tools.terminal_tool import terminal_tool
        from tools.file_tools import write_file_tool, read_file_tool
        import time
        
        operations = 10
        start = time.time()
        
        for i in range(operations):
            # 写
            test_file = tmp_workdir / f"perf_{i}.txt"
            write_file_tool(str(test_file), f"Content {i}")
            
            # 读
            read_file_tool(str(test_file))
            
            # 终端命令
            terminal_tool(f"ls {test_file}")
        
        total_time = time.time() - start
        avg_time = total_time / operations
        
        # 工具初始化有开销，平均 2 秒内算正常
        assert avg_time < 2.0, f"平均操作太慢：{avg_time}s"
