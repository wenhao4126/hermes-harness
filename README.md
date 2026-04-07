# Hermes Harness

> Hermes Agent 测试/评估/质量保障框架

---

## 📚 目录

- [快速开始](#快速开始)
- [测试结构](#测试结构)
- [CLI 命令](#cli 命令)
- [CI/CD](#cicd)
- [添加测试](#添加测试)
- [最佳实践](#最佳实践)

---

## 🚀 快速开始

### 安装依赖

```bash
cd /home/wen/.hermes/harness
pip install pytest pytest-cov
```

### 运行测试

```bash
# 跑所有测试
python cli.py test

# 跑指定类型测试
python cli.py test tests/unit/
python cli.py test tests/integration/
python cli.py test tests/e2e/

# 详细输出
python cli.py test -v

# 生成覆盖度报告
python cli.py test --cov
```

---

## 📁 测试结构

```
tests/
├── unit/                       # 单元测试
│   ├── test_agent_loop.py      # Agent 核心循环测试 (18 个)
│   └── test_tools.py           # 工具测试 (22 个)
│
├── integration/                # 集成测试
│   └── test_collaboration.py   # 工具间协作测试 (10 个)
│
└── e2e/                        # E2E 测试
    └── test_scenarios.py       # 完整场景测试 (11 个)
```

### 测试类型说明

| 类型 | 目的 | 示例 |
|------|------|------|
| **单元测试** | 测试单个函数/类 | 工具执行、Agent 初始化 |
| **集成测试** | 测试模块间协作 | 终端 + 文件系统协作 |
| **E2E 测试** | 测试完整用户场景 | 项目创建、代码调试 |

---

## 🛠 CLI 命令

### `python cli.py test [PATH]`

运行测试。

**选项：**
- `-v, --verbose` - 详细输出
- `-m, --marker` - 只运行指定标记的测试
- `--cov` - 生成覆盖度报告

**示例：**
```bash
# 跑所有单元测试
python cli.py test tests/unit/

# 跑带 -v 标志
python cli.py test -v

# 生成覆盖度报告
python cli.py test --cov
```

### `python cli.py eval [BENCHMARK]`

运行评估基准。

**可用基准：**
- `humaneval` - HumanEval 编码能力评估
- `mbpp` - MBPP 编码能力评估
- `all` - 运行所有基准

**选项：**
- `-m, --model` - 使用的模型（默认：qwen3.5-plus）
- `-o, --output` - 输出文件或目录
- `-l, --limit` - 限制任务数量

**示例：**
```bash
# 运行 HumanEval
python cli.py eval humaneval --model qwen3.5-plus

# 运行所有基准
python cli.py eval all --model qwen3.5-plus --output eval_results

# 限制任务数量
python cli.py eval humaneval --limit 5
```

### `python cli.py report [FILE]`

生成测试报告。（开发中）

### `python cli.py dashboard`

启动监控仪表板。（开发中）

---

## 🔄 CI/CD

### GitHub Actions

Hermes Harness 配置了完整的 GitHub Actions CI/CD 流程：

**触发条件：**
- 推送到 `main`/`master`/`develop` 分支
- Pull Request
- 每周一早上 9 点定时运行
- 手动触发

**工作流：**
1. **Unit Tests** - 跑单元测试 + 生成覆盖度报告
2. **Integration Tests** - 跑集成测试
3. **E2E Tests** - 跑端到端测试
4. **Test Summary** - 生成测试汇总
5. **Code Quality** - 代码质量检查（flake8/black/isort/mypy）
6. **Docs Check** - 文档完整性检查

**产物：**
- 覆盖度报告（HTML）
- 测试结果（XML）
- GitHub Step Summary

### 配置位置

```
.github/workflows/ci.yml
```

### 查看 CI 状态

访问：https://github.com/YOUR_REPO/actions

---

## ➕ 添加测试

### 单元测试

```python
# tests/unit/test_my_feature.py
import pytest
from tools.my_tool import my_tool

@pytest.mark.unit
class TestMyFeature:
    def test_simple_case(self):
        result = my_tool("input")
        data = json.loads(result)
        assert data["success"] is True
```

### 集成测试

```python
# tests/integration/test_my_integration.py
import pytest
from tools.tool_a import tool_a
from tools.tool_b import tool_b

@pytest.mark.integration
class TestMyIntegration:
    def test_tool_chain(self, tmp_workdir):
        # 工具 A 输出作为工具 B 输入
        result_a = tool_a("input")
        result_b = tool_b(result_a)
        assert result_b["success"] is True
```

### E2E 测试

```python
# tests/e2e/test_my_scenario.py
import pytest
from tools.file_tools import write_file_tool, read_file_tool
from tools.terminal_tool import terminal_tool

@pytest.mark.e2e
class TestMyScenario:
    def test_complete_workflow(self, tmp_workdir):
        # 步骤 1: 创建文件
        result = write_file_tool(str(tmp_workdir / "test.txt"), "content")
        
        # 步骤 2: 用终端验证
        result = terminal_tool(f"cat {tmp_workdir / 'test.txt'}")
        
        # 步骤 3: 验证结果
        assert "content" in result
```

---

## 📖 最佳实践

### 1. 测试命名

- 文件名：`test_<feature>.py`
- 类名：`Test<Feature>`
- 方法名：`test_<action>_<condition>`

### 2. 使用 Fixtures

```python
# 使用内置 fixtures
def test_with_tmpdir(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("content")

# 使用自定义 fixtures（conftest.py）
def test_with_sample_file(sample_python_file):
    content = sample_python_file.read_text()
```

### 3. 标记测试

```python
@pytest.mark.unit
def test_unit():
    pass

@pytest.mark.integration
def test_integration():
    pass

@pytest.mark.e2e
def test_e2e():
    pass

@pytest.mark.slow
def test_slow():
    pass
```

### 4. 断言技巧

```python
# 好的断言
assert result["success"] is True
assert "expected" in result["output"]
assert len(items) == 5

# 带消息的断言
assert result["exit_code"] == 0, f"命令应该成功：{result}"
```

### 5. 测试隔离

- 使用 `tmp_path` 或 `tmp_workdir` fixture
- 不依赖外部状态
- 测试间互不影响

---

## 📊 测试统计

| 测试类型 | 文件数 | 测试数 | 状态 |
|---------|--------|--------|------|
| 单元测试 | 2 | 40 | ✅ |
| 集成测试 | 1 | 10 | ✅ |
| E2E 测试 | 1 | 11 | ✅ |
| **总计** | **4** | **61** | **✅** |

---

## 🐛 常见问题

### Q: 测试失败怎么办？

A: 
1. 查看详细输出：`python cli.py test -v`
2. 检查错误信息
3. 本地复现问题
4. 修复后重新跑测试

### Q: 如何跳过慢速测试？

A:
```bash
# 跳过 slow 标记的测试
python cli.py test -m "not slow"
```

### Q: 如何只跑失败的测试？

A:
```bash
# 使用 pytest 的 --lf 选项
python -m pytest tests/ --lf
```

### Q: 覆盖度多少算合格？

A:
- **80%+** - 优秀
- **70-80%** - 良好
- **60-70%** - 可接受
- **<60%** - 需要改进

---

## 📝 更新日志

### v0.1.0 (2026-04-07)
- ✅ 单元测试框架 (40 个测试)
- ✅ 集成测试框架 (10 个测试)
- ✅ E2E 测试框架 (11 个测试)
- ✅ CLI 工具
- ✅ GitHub Actions CI/CD
- ✅ 测试覆盖度报告

---

## 📄 许可证

MIT License
