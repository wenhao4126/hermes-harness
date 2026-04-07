# HumanEval 编码能力基准测试
# 基于 OpenAI HumanEval 数据集

import json
import time
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict


# =============================================================================
# HumanEval 任务定义
# =============================================================================

@dataclass
class HumanEvalTask:
    """HumanEval 任务定义"""
    task_id: str
    prompt: str
    test: str
    entry_point: str
    canonical_solution: str


@dataclass
class HumanEvalResult:
    """HumanEval 评估结果"""
    task_id: str
    passed: bool
    code: str
    test_output: str
    error: str = None
    duration_seconds: float = 0.0


# =============================================================================
# HumanEval 数据集（示例）
# =============================================================================

# 注意：完整的 HumanEval 有 164 个任务
# 这里只放几个示例任务用于演示

HUMANEVAL_EXAMPLES = [
    {
        "task_id": "HumanEval/0",
        "prompt": "from typing import List\n\n\ndef has_close_elements(numbers: List[float], threshold: float) -> bool:\n    \"\"\" Check if in given list of numbers, are any two numbers closer to each other than\n    given threshold.\n    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)\n    False\n    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)\n    True\n    \"\"\"\n",
        "test": "\n\nMETADATA = {\n    'author': 'jt',\n    'dataset': 'test'\n}\n\n\ndef check(candidate):\n    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) == True\n    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) == False\n    assert candidate([1.0, 2.0, 5.9, 4.0, 5.0], 0.95) == True\n    assert candidate([1.0, 2.0, 5.9, 4.0, 5.0], 0.8) == False\n    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0, 2.0], 0.1) == True\n    assert candidate([1.1, 2.2, 3.1, 4.1, 5.1], 1.0) == True\n    assert candidate([1.1, 2.2, 3.1, 4.1, 5.1], 0.5) == False\n",
        "entry_point": "has_close_elements",
        "canonical_solution": "    for idx, elem in enumerate(numbers):\n        for idx2, elem2 in enumerate(numbers):\n            if idx != idx2:\n                distance = abs(elem - elem2)\n                if distance < threshold:\n                    return True\n\n    return False"
    },
    {
        "task_id": "HumanEval/1",
        "prompt": "from typing import List\n\n\ndef separate_paren_groups(paren_string: str) -> List[str]:\n    \"\"\" Input to this function is a string containing multiple groups of nested parentheses.\n    Your goal is to separate those group into separate strings and return the list of those.\n    Separate groups are balanced (each open brace is properly closed) and not nested within each other.\n    Ignore any spaces in the input string.\n    >>> separate_paren_groups('( ) (( )) (( )( ))')\n    ['()', '(())', '(()())']\n    \"\"\"\n",
        "test": "\n\nMETADATA = {\n    'author': 'jt',\n    'dataset': 'test'\n}\n\n\ndef check(candidate):\n    assert candidate('(()())') == ['(()())']\n    assert candidate('() ()') == ['()', '()']\n    assert candidate('((()))') == ['((()))']\n    assert candidate('()((()))()') == ['()', '((()))', '()']\n    assert candidate('((()()))') == ['((()()))']\n    assert candidate('()()()') == ['()', '()', '()']\n",
        "entry_point": "separate_paren_groups",
        "canonical_solution": "    result = []\n    current_string = []\n    current_depth = 0\n\n    for c in paren_string:\n        if c == ' ':\n            continue\n        if c == '(':\n            current_depth += 1\n            current_string.append(c)\n        elif c == ')':\n            current_depth -= 1\n            current_string.append(c)\n\n        if current_depth == 0 and len(current_string) > 0:\n            result.append(''.join(current_string))\n            current_string = []\n\n    return result"
    },
    {
        "task_id": "HumanEval/2",
        "prompt": "def truncate_number(number: float) -> float:\n    \"\"\" Given a positive number, separate it into integer and fractional parts.\n    Return the fractional part of the number.\n    >>> truncate_number(3.5)\n    0.5\n    \"\"\"\n",
        "test": "\n\nMETADATA = {\n    'author': 'jt',\n    'dataset': 'test'\n}\n\n\ndef check(candidate):\n    assert candidate(3.5) == 0.5\n    assert isinstance(candidate(3.5), float)\n    assert candidate(1.33) == 0.33\n    assert candidate(123.456) == 0.456\n",
        "entry_point": "truncate_number",
        "canonical_solution": "    return number % 1.0"
    },
    {
        "task_id": "HumanEval/3",
        "prompt": "def below_zero(operations: List[int]) -> bool:\n    \"\"\" You're given a list of deposit and withdrawal operations on a bank account that starts with\n    zero balance. Your task is to detect if at any point the balance of account fallls below zero, and\n    at that point function should return True. Otherwise it should return False.\n    >>> below_zero([1, 2, 3])\n    False\n    >>> below_zero([1, 2, -4, 5])\n    True\n    \"\"\"\n",
        "test": "\n\nMETADATA = {\n    'author': 'jt',\n    'dataset': 'test'\n}\n\n\ndef check(candidate):\n    assert candidate([]) == False\n    assert candidate([1, 2, -3, 1, 2, -3]) == False\n    assert candidate([1, 2, -4, 5, 6]) == True\n    assert candidate([1, -1, 2, -2, 5, -5, 4, -4]) == False\n    assert candidate([1, -1, 2, -2, 5, -5, 4, -4, -1]) == True\n    assert candidate([1, -2, 2, -2, 5, -5, 4, -4]) == True\n",
        "entry_point": "below_zero",
        "canonical_solution": "    balance = 0\n\n    for op in operations:\n        balance += op\n        if balance < 0:\n            return True\n\n    return False"
    },
    {
        "task_id": "HumanEval/4",
        "prompt": "from typing import List\n\n\ndef mean_absolute_deviation(numbers: List[float]) -> float:\n    \"\"\" For a given list of input numbers, calculate Mean Absolute Deviation\n    around the mean of the dataset.\n    Mean Absolute Deviation is the average absolute difference between each\n    element and a centerpoint (mean in this case):\n    MAD = average | x - x_mean |\n    >>> round(mean_absolute_deviation([1.0, 2.0, 3.0, 4.0]), 2)\n    1.0\n    \"\"\"\n",
        "test": "\n\nMETADATA = {\n    'author': 'jt',\n    'dataset': 'test'\n}\n\n\ndef check(candidate):\n    assert abs(candidate([1.0, 2.0, 3.0]) - 2.0/3.0) < 1e-6\n    assert abs(candidate([1.0, 2.0, 3.0, 4.0]) - 1.0) < 1e-6\n    assert abs(candidate([1.0, 2.0, 3.0, 4.0, 5.0]) - 6.0/5.0) < 1e-6\n",
        "entry_point": "mean_absolute_deviation",
        "canonical_solution": "    mean = sum(numbers) / len(numbers)\n    return sum(abs(x - mean) for x in numbers) / len(numbers)"
    }
]


# =============================================================================
# HumanEval 评估运行器
# =============================================================================

class HumanEvalRunner:
    """HumanEval 评估运行器"""
    
    def __init__(self, agent_factory, timeout_seconds: int = 60):
        """
        初始化评估运行器
        
        Args:
            agent_factory: 创建 Agent 的工厂函数
            timeout_seconds: 每个任务的超时时间（秒）
        """
        self.agent_factory = agent_factory
        self.timeout_seconds = timeout_seconds
        self.tasks = self._load_tasks()
    
    def _load_tasks(self) -> List[HumanEvalTask]:
        """加载 HumanEval 任务"""
        return [
            HumanEvalTask(
                task_id=task["task_id"],
                prompt=task["prompt"],
                test=task["test"],
                entry_point=task["entry_point"],
                canonical_solution=task["canonical_solution"]
            )
            for task in HUMANEVAL_EXAMPLES
        ]
    
    def run_task(self, task: HumanEvalTask) -> HumanEvalResult:
        """
        运行单个评估任务
        
        Args:
            task: HumanEval 任务
            
        Returns:
            HumanEvalResult: 评估结果
        """
        import subprocess
        import tempfile
        import os
        
        start_time = time.time()
        
        # 创建 Agent 并获取代码
        agent = self.agent_factory()
        
        # 让 Agent 完成编程任务
        prompt = f"""
请完成以下 Python 函数实现：

{task.prompt}

只需要返回完整的函数实现代码，不要包含测试代码或解释。
"""
        
        try:
            # 运行 Agent 获取代码
            result = agent.run_conversation(prompt)
            generated_code = result.get("final_response", "")
            
            # 提取代码（清理可能的 markdown 格式）
            code = self._extract_code(generated_code)
            
            # 组合完整代码文件
            full_code = f"{task.prompt}\n{code}\n{task.test}"
            
            # 创建临时文件运行测试
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(full_code)
                temp_file = f.name
            
            try:
                # 运行测试
                result = subprocess.run(
                    ['python', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds
                )
                
                # 检查是否通过
                passed = result.returncode == 0
                
                return HumanEvalResult(
                    task_id=task.task_id,
                    passed=passed,
                    code=code,
                    test_output=result.stdout,
                    error=result.stderr if not passed else None,
                    duration_seconds=time.time() - start_time
                )
            
            finally:
                # 清理临时文件
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
        
        except subprocess.TimeoutExpired:
            return HumanEvalResult(
                task_id=task.task_id,
                passed=False,
                code=generated_code,
                test_output="",
                error=f"Timeout after {self.timeout_seconds} seconds",
                duration_seconds=time.time() - start_time
            )
        
        except Exception as e:
            return HumanEvalResult(
                task_id=task.task_id,
                passed=False,
                code=generated_code if 'generated_code' in locals() else "",
                test_output="",
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    def _extract_code(self, text: str) -> str:
        """从文本中提取代码"""
        import re
        
        # 尝试提取 markdown 代码块
        code_block = re.search(r'```python\n(.*?)\n```', text, re.DOTALL)
        if code_block:
            return code_block.group(1)
        
        # 如果没有 markdown，返回原文本
        return text.strip()
    
    def run_all(self) -> List[HumanEvalResult]:
        """
        运行所有评估任务
        
        Returns:
            List[HumanEvalResult]: 所有任务的结果
        """
        results = []
        
        for task in self.tasks:
            print(f"Running {task.task_id}...")
            result = self.run_task(task)
            results.append(result)
            
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"  {status} - {result.duration_seconds:.2f}s")
        
        return results
    
    def generate_report(self, results: List[HumanEvalResult]) -> Dict[str, Any]:
        """
        生成评估报告
        
        Args:
            results: 评估结果列表
            
        Returns:
            Dict: 评估报告
        """
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        
        report = {
            "benchmark": "HumanEval",
            "total_tasks": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "average_duration": sum(r.duration_seconds for r in results) / total if total > 0 else 0,
            "results": [asdict(r) for r in results]
        }
        
        return report


# =============================================================================
# CLI 入口
# =============================================================================

def run_humaneval_eval(model: str = "qwen3.5-plus", output: str = "results.json"):
    """
    运行 HumanEval 评估
    
    Args:
        model: 使用的模型名称
        output: 输出文件路径
    """
    from run_agent import AIAgent
    
    def agent_factory():
        return AIAgent(
            model=model,
            max_iterations=30,
            quiet_mode=True,
        )
    
    # 创建运行器
    runner = HumanEvalRunner(agent_factory, timeout_seconds=60)
    
    # 运行评估
    print(f"🚀 开始 HumanEval 评估 (模型：{model})")
    print("=" * 60)
    
    results = runner.run_all()
    
    # 生成报告
    report = runner.generate_report(results)
    
    # 打印总结
    print("=" * 60)
    print(f"📊 评估结果:")
    print(f"   总任务数：{report['total_tasks']}")
    print(f"   通过：{report['passed']}")
    print(f"   失败：{report['failed']}")
    print(f"   通过率：{report['pass_rate']:.1%}")
    print(f"   平均耗时：{report['average_duration']:.2f}s")
    
    # 保存结果
    with open(output, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 结果已保存到：{output}")
    
    return report


if __name__ == "__main__":
    import sys
    
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen3.5-plus"
    output = sys.argv[2] if len(sys.argv) > 2 else "humaneval_results.json"
    
    run_humaneval_eval(model, output)
