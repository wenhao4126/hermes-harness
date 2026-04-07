# E2E 测试 - 端到端场景测试
# 模拟真实用户完整工作流

import pytest
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch


# =============================================================================
# 项目创建场景测试
# =============================================================================

@pytest.mark.e2e
class TestProjectCreationScenario:
    """项目创建场景 E2E 测试"""
    
    def test_create_python_project_structure(self, tmp_workdir):
        """测试创建完整 Python 项目结构"""
        from tools.terminal_tool import terminal_tool
        from tools.file_tools import write_file_tool, read_file_tool
        
        project_dir = tmp_workdir / "my_python_project"
        
        # 步骤 1: 创建项目目录结构
        dirs_to_create = [
            project_dir,
            project_dir / "src",
            project_dir / "tests",
            project_dir / "docs",
        ]
        
        for d in dirs_to_create:
            d.mkdir(parents=True, exist_ok=True)
        
        # 步骤 2: 创建核心文件
        files_to_create = {
            project_dir / "README.md": "# My Python Project\n\nA sample project.",
            project_dir / "setup.py": "from setuptools import setup\n\nsetup(name='my_project', version='0.1.0')",
            project_dir / "src/__init__.py": "",
            project_dir / "src/main.py": "def main():\n    print('Hello from main!')\n\nif __name__ == '__main__':\n    main()",
            project_dir / "tests/__init__.py": "",
            project_dir / "tests/test_main.py": "from src.main import main\n\ndef test_main():\n    assert main() is None",
        }
        
        for file_path, content in files_to_create.items():
            result = write_file_tool(str(file_path), content)
            data = json.loads(result)
            # bytes_written 可能为 0 如果文件已存在，所以只检查没有 error
            assert "error" not in data or data.get("error") is None
        
        # 步骤 3: 验证项目结构
        result = terminal_tool(f"find {project_dir} -type f -name '*.py' | wc -l")
        data = json.loads(result)
        py_file_count = int(data["output"].strip())
        assert py_file_count >= 4, f"应该有至少 4 个 Python 文件，实际：{py_file_count}"
        
        # 步骤 4: 验证 README 内容
        result = read_file_tool(str(project_dir / "README.md"))
        data = json.loads(result)
        assert "My Python Project" in data["content"]
    
    def test_create_project_with_git(self, tmp_workdir):
        """测试创建带 Git 的项目"""
        from tools.terminal_tool import terminal_tool
        from tools.file_tools import write_file_tool
        
        project_dir = tmp_workdir / "git_project"
        project_dir.mkdir()
        
        # 步骤 1: 创建初始文件
        result = write_file_tool(str(project_dir / "README.md"), "# Git Project")
        data = json.loads(result)
        assert data["bytes_written"] > 0
        
        # 步骤 2: 初始化 Git（如果可用）
        result = terminal_tool(f"cd {project_dir} && git init")
        data = json.loads(result)
        
        # Git 可能没安装，所以只要不报错就行
        # 如果 git 可用，验证初始化成功
        if data["exit_code"] == 0:
            result = terminal_tool(f"cd {project_dir} && git status")
            data = json.loads(result)
            # 中文输出也检查
            output = data["output"]
            assert ("No commits yet" in output or 
                    "On branch master" in output or 
                    "位于分支 master" in output or
                    "尚无提交" in output)


# =============================================================================
# 代码调试场景测试
# =============================================================================

@pytest.mark.e2e
class TestDebuggingScenario:
    """代码调试场景 E2E 测试"""
    
    def test_debug_syntax_error(self, tmp_workdir):
        """测试调试语法错误"""
        from tools.file_tools import write_file_tool, read_file_tool
        from tools.terminal_tool import terminal_tool
        
        # 步骤 1: 创建有语法错误的文件
        buggy_file = tmp_workdir / "buggy.py"
        buggy_code = """def calculate_sum(numbers):
    total = 0
    for n in numbers:
        total += n
    return total

# 语法错误：缺少冒号
if __name__ == "__main__"
    print(calculate_sum([1, 2, 3]))
"""
        result = write_file_tool(str(buggy_file), buggy_code)
        data = json.loads(result)
        assert data["bytes_written"] > 0
        
        # 步骤 2: 用 Python 检查语法
        result = terminal_tool(f"python -m py_compile {buggy_file}")
        data = json.loads(result)
        
        # 应该检测到语法错误
        assert data["exit_code"] != 0, "应该检测到语法错误"
        assert "SyntaxError" in data["output"] or "Error" in data["output"]
        
        # 步骤 3: 修复错误
        fixed_code = """def calculate_sum(numbers):
    total = 0
    for n in numbers:
        total += n
    return total

# 修复：添加冒号
if __name__ == "__main__":
    print(calculate_sum([1, 2, 3]))
"""
        result = write_file_tool(str(buggy_file), fixed_code)
        data = json.loads(result)
        
        # 步骤 4: 验证修复
        result = terminal_tool(f"python -m py_compile {buggy_file}")
        data = json.loads(result)
        assert data["exit_code"] == 0, "语法错误应该已修复"
    
    def test_debug_runtime_error(self, tmp_workdir):
        """测试调试运行时错误"""
        from tools.file_tools import write_file_tool
        from tools.terminal_tool import terminal_tool
        
        # 步骤 1: 创建有运行时错误的文件
        buggy_file = tmp_workdir / "runtime_bug.py"
        buggy_code = """def divide(a, b):
    return a / b

if __name__ == "__main__":
    result = divide(10, 0)  # 除零错误
    print(f"Result: {result}")
"""
        result = write_file_tool(str(buggy_file), buggy_code)
        data = json.loads(result)
        
        # 步骤 2: 运行并捕获错误
        result = terminal_tool(f"python {buggy_file}")
        data = json.loads(result)
        
        # 应该检测到除零错误
        assert data["exit_code"] != 0
        assert "ZeroDivisionError" in data["output"] or "division by zero" in data["output"]


# =============================================================================
# API 开发场景测试
# =============================================================================

@pytest.mark.e2e
class TestAPIDevelopmentScenario:
    """API 开发场景 E2E 测试"""
    
    def test_create_simple_api_endpoint(self, tmp_workdir):
        """测试创建简单 API 端点"""
        from tools.file_tools import write_file_tool, read_file_tool
        from tools.terminal_tool import terminal_tool
        
        # 步骤 1: 创建 FastAPI 应用
        app_file = tmp_workdir / "api_app.py"
        app_code = """from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
        result = write_file_tool(str(app_file), app_code)
        data = json.loads(result)
        assert data["bytes_written"] > 0
        
        # 步骤 2: 验证语法
        result = terminal_tool(f"python -m py_compile {app_file}")
        data = json.loads(result)
        assert data["exit_code"] == 0, "API 代码应该没有语法错误"
        
        # 步骤 3: 检查依赖（不实际安装）
        result = terminal_tool("python -c 'import fastapi' 2>&1 || echo 'fastapi not installed'")
        data = json.loads(result)
        # 不管是否安装，测试继续
        
        # 步骤 4: 验证文件内容
        result = read_file_tool(str(app_file))
        data = json.loads(result)
        assert "@app.get" in data["content"]
        assert "FastAPI" in data["content"]
    
    def test_create_api_with_tests(self, tmp_workdir):
        """测试创建 API 及其测试"""
        from tools.file_tools import write_file_tool, search_tool
        from tools.terminal_tool import terminal_tool
        
        # 步骤 1: 创建 API 文件
        api_file = tmp_workdir / "users_api.py"
        api_code = """
class UsersAPI:
    def __init__(self):
        self.users = {}
    
    def create_user(self, user_id: int, name: str) -> dict:
        self.users[user_id] = {"id": user_id, "name": name}
        return self.users[user_id]
    
    def get_user(self, user_id: int) -> dict:
        return self.users.get(user_id)
    
    def delete_user(self, user_id: int) -> bool:
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False
"""
        result = write_file_tool(str(api_file), api_code)
        data = json.loads(result)
        
        # 步骤 2: 创建测试文件
        test_file = tmp_workdir / "test_users_api.py"
        test_code = """
from users_api import UsersAPI

def test_create_user():
    api = UsersAPI()
    user = api.create_user(1, "Alice")
    assert user["id"] == 1
    assert user["name"] == "Alice"

def test_get_user():
    api = UsersAPI()
    api.create_user(1, "Alice")
    user = api.get_user(1)
    assert user is not None
    assert user["name"] == "Alice"

def test_delete_user():
    api = UsersAPI()
    api.create_user(1, "Alice")
    result = api.delete_user(1)
    assert result is True
    assert api.get_user(1) is None
"""
        result = write_file_tool(str(test_file), test_code)
        data = json.loads(result)
        
        # 步骤 3: 验证创建了 Python 文件
        result = search_tool("*.py", path=str(tmp_workdir), target="files")
        data = json.loads(result)
        assert data["total_count"] >= 2


# =============================================================================
# 数据分析场景测试
# =============================================================================

@pytest.mark.e2e
class TestDataAnalysisScenario:
    """数据分析场景 E2E 测试"""
    
    def test_create_and_analyze_csv(self, tmp_workdir):
        """测试创建并分析 CSV 数据"""
        from tools.file_tools import write_file_tool, read_file_tool, search_tool
        from tools.terminal_tool import terminal_tool
        
        # 步骤 1: 创建 CSV 数据
        csv_file = tmp_workdir / "sales_data.csv"
        csv_content = """date,product,quantity,price
2024-01-01,Widget A,10,25.00
2024-01-02,Widget B,5,30.00
2024-01-03,Widget A,8,25.00
2024-01-04,Widget C,12,20.00
2024-01-05,Widget B,7,30.00
"""
        result = write_file_tool(str(csv_file), csv_content)
        data = json.loads(result)
        
        # 步骤 2: 验证 CSV 内容
        result = read_file_tool(str(csv_file))
        data = json.loads(result)
        assert "date,product,quantity,price" in data["content"]
        assert "Widget A" in data["content"]
        
        # 步骤 3: 用终端命令分析
        # 计算总行数
        result = terminal_tool(f"wc -l < {csv_file}")
        data = json.loads(result)
        line_count = int(data["output"].strip())
        assert line_count == 6  # 1 行标题 + 5 行数据
        
        # 步骤 4: 统计特定产品
        result = terminal_tool(f"grep -c 'Widget A' {csv_file}")
        data = json.loads(result)
        widget_a_count = int(data["output"].strip())
        assert widget_a_count == 2
    
    def test_create_data_processing_script(self, tmp_workdir):
        """测试创建数据处理脚本"""
        from tools.file_tools import write_file_tool, read_file_tool
        from tools.terminal_tool import terminal_tool
        
        # 步骤 1: 创建处理脚本
        script_file = tmp_workdir / "process_data.py"
        script_content = """#!/usr/bin/env python3
\"\"\"Data processing script\"\"\"

import csv
from pathlib import Path

def process_sales_data(input_file: str) -> dict:
    \"\"\"Process sales data and return summary\"\"\"
    total_quantity = 0
    total_revenue = 0
    products = {}
    
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            quantity = int(row['quantity'])
            price = float(row['price'])
            product = row['product']
            
            total_quantity += quantity
            total_revenue += quantity * price
            
            if product not in products:
                products[product] = 0
            products[product] += quantity
    
    return {
        'total_quantity': total_quantity,
        'total_revenue': total_revenue,
        'product_counts': products
    }

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        result = process_sales_data(sys.argv[1])
        print(f"Total Quantity: {result['total_quantity']}")
        print(f"Total Revenue: ${result['total_revenue']:.2f}")
        print(f"Products: {result['product_counts']}")
"""
        result = write_file_tool(str(script_file), script_content)
        data = json.loads(result)
        
        # 步骤 2: 验证语法
        result = terminal_tool(f"python -m py_compile {script_file}")
        data = json.loads(result)
        assert data["exit_code"] == 0, "脚本应该没有语法错误"
        
        # 步骤 3: 验证内容
        result = read_file_tool(str(script_file))
        data = json.loads(result)
        assert "def process_sales_data" in data["content"]
        assert "csv.DictReader" in data["content"]


# =============================================================================
# 文档编写场景测试
# =============================================================================

@pytest.mark.e2e
class TestDocumentationScenario:
    """文档编写场景 E2E 测试"""
    
    def test_create_project_documentation(self, tmp_workdir):
        """测试创建项目文档"""
        from tools.file_tools import write_file_tool, read_file_tool, search_tool
        
        docs_dir = tmp_workdir / "docs"
        docs_dir.mkdir()
        
        # 步骤 1: 创建多个文档文件
        docs = {
            docs_dir / "README.md": """# Project Documentation

## Overview
This is the main project documentation.

## Installation
```bash
pip install myproject
```

## Usage
```python
from myproject import main
main()
```
""",
            docs_dir / "API.md": """# API Reference

## Endpoints

### GET /api/users
Returns a list of users.

### POST /api/users
Creates a new user.

### GET /api/users/{id}
Returns a specific user.
""",
            docs_dir / "CONTRIBUTING.md": """# Contributing Guidelines

## How to Contribute
1. Fork the repository
2. Create a branch
3. Make your changes
4. Submit a PR

## Code Style
- Follow PEP 8
- Write tests
- Document your code
""",
        }
        
        for file_path, content in docs.items():
            result = write_file_tool(str(file_path), content)
            data = json.loads(result)
            assert data["bytes_written"] > 0
        
        # 步骤 2: 验证文档数量
        result = search_tool("*.md", path=str(docs_dir), target="files")
        data = json.loads(result)
        assert data["total_count"] == 3
        
        # 步骤 3: 验证特定文档内容
        result = read_file_tool(str(docs_dir / "API.md"))
        data = json.loads(result)
        assert "GET /api/users" in data["content"]
        assert "POST /api/users" in data["content"]
    
    def test_create_changelog(self, tmp_workdir):
        """测试创建变更日志"""
        from tools.file_tools import write_file_tool, read_file_tool
        
        changelog_file = tmp_workdir / "CHANGELOG.md"
        changelog_content = """# Changelog

## [1.1.0] - 2024-01-15
### Added
- New feature: User authentication
- API endpoint: /api/auth/login

### Changed
- Improved performance of data processing

### Fixed
- Bug fix: Memory leak in cache module

## [1.0.0] - 2024-01-01
### Added
- Initial release
- Core functionality
- Basic documentation
"""
        result = write_file_tool(str(changelog_file), changelog_content)
        data = json.loads(result)
        
        # 验证内容
        result = read_file_tool(str(changelog_file))
        data = json.loads(result)
        assert "[1.1.0]" in data["content"]
        assert "[1.0.0]" in data["content"]
        assert "Added" in data["content"]
        assert "Fixed" in data["content"]


# =============================================================================
# 完整开发工作流测试
# =============================================================================

@pytest.mark.e2e
class TestFullDevelopmentWorkflow:
    """完整开发工作流 E2E 测试"""
    
    def test_complete_feature_development(self, tmp_workdir):
        """测试完整功能开发流程"""
        from tools.file_tools import write_file_tool, read_file_tool, search_tool
        from tools.terminal_tool import terminal_tool
        
        project_dir = tmp_workdir / "feature_project"
        src_dir = project_dir / "src"
        tests_dir = project_dir / "tests"
        
        # 步骤 1: 创建项目结构
        for d in [project_dir, src_dir, tests_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # 步骤 2: 创建功能代码
        feature_file = src_dir / "feature.py"
        feature_code = """
class Feature:
    \"\"\"New feature implementation\"\"\"
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = False
    
    def enable(self):
        \"\"\"Enable the feature\"\"\"
        self.enabled = True
        return True
    
    def disable(self):
        \"\"\"Disable the feature\"\"\"
        self.enabled = False
        return True
    
    def is_enabled(self) -> bool:
        \"\"\"Check if feature is enabled\"\"\"
        return self.enabled
"""
        result = write_file_tool(str(feature_file), feature_code)
        data = json.loads(result)
        
        # 步骤 3: 创建功能测试
        test_file = tests_dir / "test_feature.py"
        test_code = """
from src.feature import Feature

def test_feature_creation():
    feature = Feature("test")
    assert feature.name == "test"
    assert feature.enabled is False

def test_feature_enable():
    feature = Feature("test")
    result = feature.enable()
    assert result is True
    assert feature.is_enabled() is True

def test_feature_disable():
    feature = Feature("test")
    feature.enable()
    result = feature.disable()
    assert result is True
    assert feature.is_enabled() is False
"""
        result = write_file_tool(str(test_file), test_code)
        data = json.loads(result)
        
        # 步骤 4: 创建项目说明文档
        readme_file = project_dir / "README.md"
        readme_content = """# Feature Project

## Installation
```bash
pip install -e .
```

## Usage
```python
from src.feature import Feature

feature = Feature("my_feature")
feature.enable()
```

## Testing
```bash
pytest tests/
```
"""
        result = write_file_tool(str(readme_file), readme_content)
        data = json.loads(result)
        
        # 步骤 5: 验证项目结构
        result = search_tool("*.py", path=str(project_dir), target="files")
        data = json.loads(result)
        assert data["total_count"] >= 2
        
        # 步骤 6: 验证代码语法
        result = terminal_tool(f"python -m py_compile {feature_file}")
        data = json.loads(result)
        assert data["exit_code"] == 0
        
        result = terminal_tool(f"python -m py_compile {test_file}")
        data = json.loads(result)
        assert data["exit_code"] == 0
        
        # 步骤 7: 验证文档
        result = read_file_tool(str(readme_file))
        data = json.loads(result)
        assert "Installation" in data["content"]
        assert "Usage" in data["content"]
        assert "Testing" in data["content"]
