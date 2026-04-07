# pytest 配置 - Hermes Harness 测试框架

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch


# =============================================================================
# 临时目录配置
# =============================================================================

@pytest.fixture
def tmp_hermes_home(tmp_path):
    """
    创建隔离的 HERMES_HOME 目录
    
    每个测试都有独立的 ~/.hermes 副本，互不干扰
    """
    home = tmp_path / "hermes_home"
    home.mkdir(parents=True, exist_ok=True)
    
    # 创建最小配置文件
    config = home / "config.yaml"
    config.write_text("""
model:
  default: test-model
  provider: test
  
terminal:
  backend: local
  timeout: 30
  
agent:
  max_turns: 10
  
compression:
  enabled: false
  
delegation:
  model: test-model
  max_iterations: 20
""")
    
    # 创建 .env 文件
    env = home / ".env"
    env.write_text("""
TEST_API_KEY=fake-test-key
TEST_BASE_URL=http://localhost:9999
""")
    
    # 创建必要子目录
    (home / "skills").mkdir(exist_ok=True)
    (home / "sessions").mkdir(exist_ok=True)
    (home / "logs").mkdir(exist_ok=True)
    (home / "memories").mkdir(exist_ok=True)
    
    return home


@pytest.fixture
def tmp_workdir(tmp_path):
    """
    创建临时工作目录
    
    用于测试文件操作
    """
    workdir = tmp_path / "workdir"
    workdir.mkdir(parents=True, exist_ok=True)
    return workdir


# =============================================================================
# Mock API 服务器
# =============================================================================

@pytest.fixture
def mock_api_response():
    """
    创建 Mock API 响应
    
    用于模拟 LLM API 返回
    """
    return {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "Hello, I am a test agent."
            }
        }],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
    }


@pytest.fixture
def mock_api_server(mock_api_response):
    """
    创建 Mock API 服务器
    
    模拟 LLM API 行为
    """
    class MockServer:
        def __init__(self):
            self.url = "http://localhost:9999"
            self.api_key = "fake-test-key"
            self.call_count = 0
            self.responses = []
        
        def chat(self, messages, **kwargs):
            self.call_count += 1
            self.responses.append({
                "messages": messages,
                "kwargs": kwargs
            })
            return mock_api_response
        
        def reset(self):
            self.call_count = 0
            self.responses = []
    
    server = MockServer()
    yield server
    # 清理
    server.reset()


# =============================================================================
# Agent Fixtures
# =============================================================================

@pytest.fixture
def test_agent(tmp_hermes_home, mock_api_server):
    """
    创建测试用 Agent (Mock 版)
    
    使用 Mock API，不产生实际费用，适合快速单元测试
    """
    # 设置环境变量
    old_home = os.environ.get("HERMES_HOME")
    os.environ["HERMES_HOME"] = str(tmp_hermes_home)
    
    try:
        # 创建 Mock Agent
        agent = Mock()
        agent.model = "test-model"
        agent.base_url = mock_api_server.url
        agent.api_key = mock_api_server.api_key
        agent.max_iterations = 10
        agent.enabled_toolsets = ["terminal", "file"]
        agent.api_call_count = 0
        agent.tokens_used = 0
        
        # Mock run_conversation
        def mock_run(prompt):
            agent.api_call_count += 1
            return {
                "final_response": f"Test response to: {prompt[:50]}...",
                "completed": True,
                "exit_reason": "completed",
                "messages": []
            }
        
        agent.run_conversation = mock_run
        
        yield agent
        
    finally:
        # 恢复环境变量
        if old_home:
            os.environ["HERMES_HOME"] = old_home
        else:
            os.environ.pop("HERMES_HOME", None)


@pytest.fixture
def real_agent(tmp_hermes_home):
    """
    创建真实的 AIAgent 实例
    
    用于集成测试，需要配置有效的 base_url 和 api_key
    注意：不会实际调用 API，但会初始化完整的 Agent 环境
    """
    import os
    old_home = os.environ.get("HERMES_HOME")
    os.environ["HERMES_HOME"] = str(tmp_hermes_home)
    
    try:
        from run_agent import AIAgent
        agent = AIAgent(
            base_url="http://localhost:9999",
            api_key="fake-test-key",
            model="test-model",
            max_iterations=10,
            quiet_mode=True,
        )
        yield agent
    finally:
        if old_home:
            os.environ["HERMES_HOME"] = old_home
        else:
            os.environ.pop("HERMES_HOME", None)


# =============================================================================
# 工具 Fixtures
# =============================================================================

@pytest.fixture
def sample_python_file(tmp_workdir):
    """
    创建示例 Python 文件
    
    用于测试文件操作
    """
    content = '''
def hello(name):
    """Say hello to someone"""
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(hello("World"))
'''
    file_path = tmp_workdir / "hello.py"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_project(tmp_workdir):
    """
    创建示例项目结构
    
    用于测试项目分析
    """
    # 创建目录结构
    src = tmp_workdir / "src"
    src.mkdir()
    tests = tmp_workdir / "tests"
    tests.mkdir()
    
    # 创建文件
    (tmp_workdir / "README.md").write_text("# Test Project")
    (tmp_workdir / "setup.py").write_text("from setuptools import setup; setup()")
    (src / "__init__.py").write_text("")
    (src / "main.py").write_text("def main(): pass")
    (tests / "test_main.py").write_text("def test_main(): pass")
    
    return tmp_workdir


# =============================================================================
# 断言辅助
# =============================================================================

class HarnessAssertions:
    """
    测试断言辅助类
    
    提供常用的断言方法
    """
    
    @staticmethod
    def assert_file_exists(path):
        assert Path(path).exists(), f"文件不存在：{path}"
    
    @staticmethod
    def assert_file_contains(path, text):
        content = Path(path).read_text()
        assert text in content, f"文件 {path} 不包含文本：{text}"
    
    @staticmethod
    def assert_valid_json(text):
        import json
        try:
            json.loads(text)
        except json.JSONDecodeError as e:
            pytest.fail(f"不是有效的 JSON: {e}")


@pytest.fixture
def harness_assert():
    """提供断言辅助"""
    return HarnessAssertions


# =============================================================================
# pytest 配置
# =============================================================================

def pytest_configure(config):
    """pytest 启动时执行"""
    config.addinivalue_line(
        "markers", "unit: 单元测试标记"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试标记"
    )
    config.addinivalue_line(
        "markers", "e2e: 端到端测试标记"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试标记"
    )


# =============================================================================
# 日志配置
# =============================================================================

@pytest.fixture(autouse=True)
def capture_logs(caplog):
    """
    自动捕获所有测试的日志
    
    失败时输出日志帮助调试
    """
    import logging
    caplog.set_level(logging.DEBUG)
    yield caplog
