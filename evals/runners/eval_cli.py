# 评估运行器 CLI
# 统一入口用于运行各种评估基准

import click
import sys
import os
from pathlib import Path


# =============================================================================
# CLI 主入口
# =============================================================================

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='详细输出')
@click.pass_context
def cli(ctx, verbose):
    """Hermes Evals - 评估基准运行工具"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


# =============================================================================
# HumanEval 命令
# =============================================================================

@cli.command()
@click.option('--model', '-m', default='qwen3.5-plus', help='使用的模型')
@click.option('--output', '-o', default='humaneval_results.json', help='输出文件')
@click.option('--timeout', '-t', default=60, help='每个任务超时（秒）')
@click.option('--limit', '-l', type=int, help='限制任务数量')
def humaneval(model, output, timeout, limit):
    """运行 HumanEval 编码能力评估"""
    from evals.benchmarks.coding.humaneval import HumanEvalRunner, run_humaneval_eval
    from run_agent import AIAgent
    
    def agent_factory():
        return AIAgent(
            model=model,
            max_iterations=30,
            quiet_mode=True,
        )
    
    # 创建运行器
    runner = HumanEvalRunner(agent_factory, timeout_seconds=timeout)
    
    # 如果有限制
    if limit:
        runner.tasks = runner.tasks[:limit]
    
    # 运行评估
    click.echo(f"🚀 开始 HumanEval 评估 (模型：{model})")
    click.echo("=" * 60)
    
    results = runner.run_all()
    
    # 生成报告
    report = runner.generate_report(results)
    
    # 打印总结
    click.echo("=" * 60)
    click.echo(f"📊 评估结果:")
    click.echo(f"   总任务数：{report['total_tasks']}")
    click.echo(f"   通过：{report['passed']}")
    click.echo(f"   失败：{report['failed']}")
    click.echo(f"   通过率：{report['pass_rate']:.1%}")
    click.echo(f"   平均耗时：{report['average_duration']:.2f}s")
    
    # 保存结果
    with open(output, 'w') as f:
        import json
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    click.echo(f"\n💾 结果已保存到：{output}")


# =============================================================================
# MBPP 命令
# =============================================================================

@cli.command()
@click.option('--model', '-m', default='qwen3.5-plus', help='使用的模型')
@click.option('--output', '-o', default='mbpp_results.json', help='输出文件')
@click.option('--timeout', '-t', default=60, help='每个任务超时（秒）')
@click.option('--limit', '-l', type=int, help='限制任务数量')
def mbpp(model, output, timeout, limit):
    """运行 MBPP 编码能力评估"""
    from evals.benchmarks.coding.mbpp import MBPPRunner
    from run_agent import AIAgent
    
    def agent_factory():
        return AIAgent(
            model=model,
            max_iterations=30,
            quiet_mode=True,
        )
    
    # 创建运行器
    runner = MBPPRunner(agent_factory, timeout_seconds=timeout)
    
    # 如果有限制
    if limit:
        runner.tasks = runner.tasks[:limit]
    
    # 运行评估
    click.echo(f"🚀 开始 MBPP 评估 (模型：{model})")
    click.echo("=" * 60)
    
    results = runner.run_all()
    
    # 生成报告
    report = runner.generate_report(results)
    
    # 打印总结
    click.echo("=" * 60)
    click.echo(f"📊 评估结果:")
    click.echo(f"   总任务数：{report['total_tasks']}")
    click.echo(f"   通过：{report['passed']}")
    click.echo(f"   失败：{report['failed']}")
    click.echo(f"   通过率：{report['pass_rate']:.1%}")
    click.echo(f"   测试通过率：{report['test_pass_rate']:.1%}")
    click.echo(f"   平均耗时：{report['average_duration']:.2f}s")
    
    # 保存结果
    with open(output, 'w') as f:
        import json
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    click.echo(f"\n💾 结果已保存到：{output}")


# =============================================================================
# 运行所有基准
# =============================================================================

@cli.command()
@click.option('--model', '-m', default='qwen3.5-plus', help='使用的模型')
@click.option('--output-dir', '-o', default='eval_results', help='输出目录')
@click.option('--timeout', '-t', default=60, help='每个任务超时（秒）')
def all(model, output_dir, timeout):
    """运行所有评估基准"""
    import json
    from datetime import datetime
    from run_agent import AIAgent
    
    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    def agent_factory():
        return AIAgent(
            model=model,
            max_iterations=30,
            quiet_mode=True,
        )
    
    # 运行 HumanEval
    click.echo("\n" + "=" * 60)
    click.echo("🔶 运行 HumanEval")
    click.echo("=" * 60)
    
    from evals.benchmarks.coding.humaneval import HumanEvalRunner
    humaneval_runner = HumanEvalRunner(agent_factory, timeout_seconds=timeout)
    humaneval_results = humaneval_runner.run_all()
    humaneval_report = humaneval_runner.generate_report(humaneval_results)
    
    humaneval_file = Path(output_dir) / f"humaneval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(humaneval_file, 'w') as f:
        json.dump(humaneval_report, f, indent=2, ensure_ascii=False)
    
    # 运行 MBPP
    click.echo("\n" + "=" * 60)
    click.echo("🔶 运行 MBPP")
    click.echo("=" * 60)
    
    from evals.benchmarks.coding.mbpp import MBPPRunner
    mbpp_runner = MBPPRunner(agent_factory, timeout_seconds=timeout)
    mbpp_results = mbpp_runner.run_all()
    mbpp_report = mbpp_runner.generate_report(mbpp_results)
    
    mbpp_file = Path(output_dir) / f"mbpp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(mbpp_file, 'w') as f:
        json.dump(mbpp_report, f, indent=2, ensure_ascii=False)
    
    # 生成汇总报告
    click.echo("\n" + "=" * 60)
    click.echo("📊 汇总报告")
    click.echo("=" * 60)
    
    summary = {
        "model": model,
        "timestamp": datetime.now().isoformat(),
        "benchmarks": {
            "humaneval": {
                "pass_rate": humaneval_report['pass_rate'],
                "total_tasks": humaneval_report['total_tasks'],
                "passed": humaneval_report['passed'],
            },
            "mbpp": {
                "pass_rate": mbpp_report['pass_rate'],
                "total_tasks": mbpp_report['total_tasks'],
                "passed": mbpp_report['passed'],
            }
        },
        "average_pass_rate": (humaneval_report['pass_rate'] + mbpp_report['pass_rate']) / 2
    }
    
    summary_file = Path(output_dir) / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # 打印总结
    click.echo(f"\n模型：{model}")
    click.echo(f"HumanEval 通过率：{humaneval_report['pass_rate']:.1%}")
    click.echo(f"MBPP 通过率：{mbpp_report['pass_rate']:.1%}")
    click.echo(f"平均通过率：{summary['average_pass_rate']:.1%}")
    click.echo(f"\n💾 结果已保存到：{output_dir}/")


# =============================================================================
# 报告命令
# =============================================================================

@cli.command()
@click.argument('result_file')
@click.option('--format', '-f', type=click.Choice(['text', 'markdown', 'json']), default='text')
def report(result_file, format):
    """生成评估报告"""
    import json
    
    if not Path(result_file).exists():
        click.echo(f"❌ 文件不存在：{result_file}")
        sys.exit(1)
    
    with open(result_file, 'r') as f:
        data = json.load(f)
    
    if format == 'text':
        click.echo(f"\n{'=' * 60}")
        click.echo(f"📊 {data.get('benchmark', '评估')} 报告")
        click.echo(f"{'=' * 60}")
        click.echo(f"总任务数：{data.get('total_tasks', 'N/A')}")
        click.echo(f"通过：{data.get('passed', 'N/A')}")
        click.echo(f"失败：{data.get('failed', 'N/A')}")
        click.echo(f"通过率：{data.get('pass_rate', 0):.1%}")
        click.echo(f"平均耗时：{data.get('average_duration', 0):.2f}s")
    
    elif format == 'markdown':
        click.echo(f"\n# {data.get('benchmark', '评估')} 报告")
        click.echo(f"\n## 概览")
        click.echo(f"| 指标 | 值 |")
        click.echo(f"|------|-----|")
        click.echo(f"| 总任务数 | {data.get('total_tasks', 'N/A')} |")
        click.echo(f"| 通过 | {data.get('passed', 'N/A')} |")
        click.echo(f"| 失败 | {data.get('failed', 'N/A')} |")
        click.echo(f"| 通过率 | {data.get('pass_rate', 0):.1%} |")
        click.echo(f"| 平均耗时 | {data.get('average_duration', 0):.2f}s |")
    
    elif format == 'json':
        click.echo(json.dumps(data, indent=2))


# =============================================================================
# 主入口
# =============================================================================

if __name__ == '__main__':
    cli()
