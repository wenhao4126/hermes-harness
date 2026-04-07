#!/usr/bin/env python3
"""
Hermes Harness CLI - 测试/评估/质量保障命令行工具

使用示例:
    hermes-harness test              # 运行所有测试
    hermes-harness test tests/unit/  # 运行指定测试
    hermes-harness eval humaneval    # 运行评估
    hermes-harness report            # 生成报告
"""

import click
import sys
import os
from pathlib import Path

# 添加父目录到 PATH，让 import 能找到 harness 模块
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# CLI 主入口
# =============================================================================

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='详细输出')
@click.option('--hermes-home', type=click.Path(), help='Hermes 主目录')
@click.pass_context
def cli(ctx, verbose, hermes_home):
    """Hermes Harness - 测试/评估/质量保障工具"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['hermes_home'] = hermes_home
    
    # 设置 HERMES_HOME
    if hermes_home:
        os.environ['HERMES_HOME'] = hermes_home


# =============================================================================
# 测试命令
# =============================================================================

@cli.command()
@click.argument('test_path', default='tests/unit/', required=False)
@click.option('--verbose', '-v', is_flag=True, help='详细输出')
@click.option('--marker', '-m', help='只运行指定标记的测试 (unit/integration/e2e)')
@click.option('--cov', is_flag=True, help='生成覆盖度报告')
def test(test_path, verbose, marker, cov):
    """运行测试"""
    import subprocess
    
    # 切换到 harness 目录
    harness_dir = Path(__file__).parent
    os.chdir(harness_dir)
    
    # 构建 pytest 命令
    cmd = [sys.executable, '-m', 'pytest']
    
    if verbose:
        cmd.append('-v')
    
    if marker:
        cmd.extend(['-m', marker])
    
    if cov:
        cmd.extend([
            '--cov=harness',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov'
        ])
    
    cmd.append(test_path)
    
    click.echo(f"🧪 运行测试：{' '.join(cmd)}")
    click.echo()
    
    # 执行测试
    result = subprocess.run(cmd, cwd=harness_dir)
    
    # 输出结果
    click.echo()
    if result.returncode == 0:
        click.echo("✅ 测试通过！")
    else:
        click.echo("❌ 测试失败！")
    
    sys.exit(result.returncode)


# =============================================================================
# 评估命令
# =============================================================================

@cli.command()
@click.argument('benchmark', required=False)
@click.option('--model', '-m', default='qwen3.5-plus', help='使用的模型')
@click.option('--output', '-o', default='eval_results', help='输出文件或目录')
@click.option('--limit', '-l', type=int, help='限制任务数量')
def eval(benchmark, model, output, limit):
    """运行评估基准"""
    import subprocess
    import sys
    
    # 切换到 harness 目录
    harness_dir = Path(__file__).parent
    os.chdir(harness_dir)
    
    click.echo(f"📊 运行评估：{benchmark or 'all'}")
    click.echo(f"   模型：{model}")
    click.echo(f"   输出：{output}")
    click.echo()
    
    # 构建命令
    cmd = [sys.executable, '-m', 'evals.runners.eval_cli']
    
    if benchmark:
        cmd.append(benchmark)
    else:
        cmd.append('all')
    
    cmd.extend(['--model', model])
    cmd.extend(['--output', output])
    
    if limit:
        cmd.extend(['--limit', str(limit)])
    
    # 执行
    result = subprocess.run(cmd, cwd=harness_dir)
    
    click.echo()
    if result.returncode == 0:
        click.echo("✅ 评估完成！")
    else:
        click.echo("❌ 评估失败！")
    
    sys.exit(result.returncode)


# =============================================================================
# 报告命令
# =============================================================================

@cli.command()
@click.argument('input_file', default='results.json')
@click.option('--format', '-f', type=click.Choice(['json', 'markdown', 'html']), default='markdown')
@click.option('--output', '-o', help='输出文件')
def report(input_file, format, output):
    """生成评估报告"""
    from pathlib import Path
    
    input_path = Path(input_file)
    
    if not input_path.exists():
        click.echo(f"❌ 文件不存在：{input_file}")
        sys.exit(1)
    
    click.echo(f"📄 生成报告：{input_file}")
    click.echo(f"   格式：{format}")
    click.echo()
    
    # TODO: 实现报告生成
    click.echo("⚠️  报告生成器正在开发中...")


# =============================================================================
# 监控命令
# =============================================================================

@cli.command()
@click.option('--port', '-p', default=8080, help='仪表板端口')
@click.option('--host', '-h', default='127.0.0.1', help='监听地址')
def dashboard(port, host):
    """启动监控仪表板"""
    click.echo(f"📈 启动监控仪表板")
    click.echo(f"   地址：http://{host}:{port}")
    click.echo()
    
    # TODO: 实现仪表板
    click.echo("⚠️  监控仪表板正在开发中...")


# =============================================================================
# 初始化命令
# =============================================================================

@cli.command()
@click.option('--force', is_flag=True, help='覆盖现有配置')
def init(force):
    """初始化 Harness 配置"""
    from pathlib import Path
    
    harness_dir = Path(__file__).parent
    config_dir = harness_dir / 'config'
    config_dir.mkdir(exist_ok=True)
    
    click.echo("🔧 初始化 Harness 配置...")
    click.echo()
    
    # 创建默认配置
    default_config = config_dir / 'default.yaml'
    if not default_config.exists() or force:
        default_config.write_text("""
# Hermes Harness 默认配置

test:
  timeout: 300
  parallel: 4
  
eval:
  max_iterations: 50
  timeout: 600
  
monitor:
  enabled: true
  interval: 60
""")
        click.echo(f"✅ 创建配置：{default_config}")
    else:
        click.echo(f"⚠️  配置已存在：{default_config}")
    
    click.echo()
    click.echo("完成！运行 'hermes-harness test' 开始测试")


# =============================================================================
# 主入口
# =============================================================================

if __name__ == '__main__':
    cli()
