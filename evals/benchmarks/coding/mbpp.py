# MBPP (Mostly Basic Python Problems) 编码能力基准测试

import json
import time
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict


# =============================================================================
# MBPP 任务定义
# =============================================================================

@dataclass
class MBPPTask:
    """MBPP 任务定义"""
    task_id: int
    prompt: str
    test_list: List[str]
    code: str
    entry_point: str


@dataclass
class MBPPResult:
    """MBPP 评估结果"""
    task_id: int
    passed: bool
    code: str
    test_results: List[bool]
    error: str = None
    duration_seconds: float = 0.0


# =============================================================================
# MBPP 数据集（示例）
# =============================================================================

MBPP_EXAMPLES = [
    {
        "task_id": 1,
        "prompt": "Write a function to find the sum of three given numbers.",
        "test_list": [
            "assert sum_of_three(1, 2, 3) == 6",
            "assert sum_of_three(5, 5, 5) == 15",
            "assert sum_of_three(0, 0, 0) == 0",
            "assert sum_of_three(-1, 1, 0) == 0",
        ],
        "code": "def sum_of_three(a, b, c):\n    return a + b + c",
        "entry_point": "sum_of_three"
    },
    {
        "task_id": 2,
        "prompt": "Write a function to check if a given number is a power of two.",
        "test_list": [
            "assert is_power_of_two(4) == True",
            "assert is_power_of_two(8) == True",
            "assert is_power_of_two(5) == False",
            "assert is_power_of_two(1) == True",
            "assert is_power_of_two(0) == False",
        ],
        "code": "def is_power_of_two(n):\n    return n > 0 and (n & (n - 1)) == 0",
        "entry_point": "is_power_of_two"
    },
    {
        "task_id": 3,
        "prompt": "Write a function to find the maximum element in a list.",
        "test_list": [
            "assert max_element([1, 2, 3, 4, 5]) == 5",
            "assert max_element([10, 5, 20, 15]) == 20",
            "assert max_element([-1, -5, -3]) == -1",
            "assert max_element([42]) == 42",
        ],
        "code": "def max_element(lst):\n    return max(lst)",
        "entry_point": "max_element"
    },
    {
        "task_id": 4,
        "prompt": "Write a function to reverse a string.",
        "test_list": [
            "assert reverse_string('hello') == 'olleh'",
            "assert reverse_string('python') == 'nohtyp'",
            "assert reverse_string('') == ''",
            "assert reverse_string('a') == 'a'",
        ],
        "code": "def reverse_string(s):\n    return s[::-1]",
        "entry_point": "reverse_string"
    },
    {
        "task_id": 5,
        "prompt": "Write a function to count the number of vowels in a string.",
        "test_list": [
            "assert count_vowels('hello') == 2",
            "assert count_vowels('aeiou') == 5",
            "assert count_vowels('xyz') == 0",
            "assert count_vowels('AEIOU') == 5",
        ],
        "code": "def count_vowels(s):\n    return sum(1 for c in s.lower() if c in 'aeiou')",
        "entry_point": "count_vowels"
    }
]


# =============================================================================
# MBPP 评估运行器
# =============================================================================

class MBPPRunner:
    """MBPP 评估运行器"""
    
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
    
    def _load_tasks(self) -> List[MBPPTask]:
        """加载 MBPP 任务"""
        return [
            MBPPTask(
                task_id=task["task_id"],
                prompt=task["prompt"],
                test_list=task["test_list"],
                code=task["code"],
                entry_point=task["entry_point"]
            )
            for task in MBPP_EXAMPLES
        ]
    
    def run_task(self, task: MBPPTask) -> MBPPResult:
        """
        运行单个评估任务
        
        Args:
            task: MBPP 任务
            
        Returns:
            MBPPResult: 评估结果
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
            
            # 组合测试代码
            test_code = "\n".join(task.test_list)
            full_code = f"{code}\n\n# Tests\n{test_code}"
            
            # 创建临时文件运行测试
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(full_code)
                temp_file = f.name
            
            try:
                # 运行测试
                proc_result = subprocess.run(
                    ['python', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds
                )
                
                # 检查是否通过
                passed = proc_result.returncode == 0
                
                # 解析单个测试结果
                test_results = []
                for test in task.test_list:
                    # 简单判断：如果整体通过，所有测试都通过
                    test_results.append(passed)
                
                return MBPPResult(
                    task_id=task.task_id,
                    passed=passed,
                    code=code,
                    test_results=test_results,
                    error=proc_result.stderr if not passed else None,
                    duration_seconds=time.time() - start_time
                )
            
            finally:
                # 清理临时文件
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
        
        except subprocess.TimeoutExpired:
            return MBPPResult(
                task_id=task.task_id,
                passed=False,
                code=generated_code if 'generated_code' in locals() else "",
                test_results=[False] * len(task.test_list),
                error=f"Timeout after {self.timeout_seconds} seconds",
                duration_seconds=time.time() - start_time
            )
        
        except Exception as e:
            return MBPPResult(
                task_id=task.task_id,
                passed=False,
                code=generated_code if 'generated_code' in locals() else "",
                test_results=[False] * len(task.test_list),
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
    
    def run_all(self) -> List[MBPPResult]:
        """
        运行所有评估任务
        
        Returns:
            List[MBPPResult]: 所有任务的结果
        """
        results = []
        
        for task in self.tasks:
            print(f"Running MBPP-{task.task_id}...")
            result = self.run_task(task)
            results.append(result)
            
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"  {status} - {result.duration_seconds:.2f}s")
        
        return results
    
    def generate_report(self, results: List[MBPPResult]) -> Dict[str, Any]:
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
        
        # 计算测试通过率
        total_tests = sum(len(r.test_results) for r in results)
        passed_tests = sum(sum(r.test_results) for r in results)
        
        report = {
            "benchmark": "MBPP",
            "total_tasks": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "test_pass_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "average_duration": sum(r.duration_seconds for r in results) / total if total > 0 else 0,
            "results": [asdict(r) for r in results]
        }
        
        return report


# =============================================================================
# CLI 入口
# =============================================================================

def run_mbpp_eval(model: str = "qwen3.5-plus", output: str = "results.json"):
    """
    运行 MBPP 评估
    
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
    runner = MBPPRunner(agent_factory, timeout_seconds=60)
    
    # 运行评估
    print(f"🚀 开始 MBPP 评估 (模型：{model})")
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
    print(f"   测试通过率：{report['test_pass_rate']:.1%}")
    print(f"   平均耗时：{report['average_duration']:.2f}s")
    
    # 保存结果
    with open(output, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 结果已保存到：{output}")
    
    return report


if __name__ == "__main__":
    import sys
    
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen3.5-plus"
    output = sys.argv[2] if len(sys.argv) > 2 else "mbpp_results.json"
    
    run_mbpp_eval(model, output)
