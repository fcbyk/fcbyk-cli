import click
import subprocess
import re
import os
from ...utils import storage
from ...cli_support.callbacks import get_version

try:
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# 全局配置路径
GLOBAL_CONFIG_FILE = "alias.byk.json"
LOCAL_CONFIG_FILE = "alias.byk.json"

# 危险命令模式
DANGEROUS_PATTERNS = [
    r'rm\s+-[^ ]*[rf]',
    r'git\s+push\s+.*(-f|--force)',
    r'shutdown',
    r'reboot',
    r'format\s+[a-zA-Z]:',
    r'rd\s+/[sq]',
    r'del\s+/[sq]',
    r'>\s*/dev/sd',
]


def load_aliases(merge_local=False):
    """加载别名配置（全局 + 本地合并）"""
    # 加载全局配置
    global_path = storage.get_path(GLOBAL_CONFIG_FILE)
    aliases = storage.load_json(global_path, default={}, create_if_missing=True)
    
    if not isinstance(aliases, dict):
        aliases = {}
    
    if merge_local:
        # 加载本地配置（当前目录）
        local_path = os.path.abspath(LOCAL_CONFIG_FILE)
        if os.path.exists(local_path):
            try:
                local_aliases = storage.load_json(local_path, default={}, create_if_missing=False)
                if local_aliases and isinstance(local_aliases, dict):
                    # 本地配置覆盖全局配置
                    aliases = aliases.copy()
                    aliases.update(local_aliases)
            except Exception as e:
                click.secho(f"Warning: Failed to load local {LOCAL_CONFIG_FILE}: {e}", fg="yellow", err=True)
    
    return aliases


def is_dangerous(command):
    """检测命令是否包含危险操作"""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def resolve_nested_alias(aliases, path):
    """解析嵌套别名（支持分组）
    
    Args:
        aliases: 别名字典
        path: 点号分隔的路径，如 '开发。构建。前端'
    
    Returns:
        tuple: (cmd_str, saved_cwd) 或 (None, None) 如果未找到
    """
    parts = path.split('.')
    current = aliases
    
    # 逐级查找
    for i, part in enumerate(parts):
        if not isinstance(current, dict):
            return None, None
        
        if part not in current:
            return None, None
        
        current = current[part]
        
        # 如果不是最后一部分，必须是字典
        if i < len(parts) - 1:
            if not isinstance(current, dict):
                return None, None
    
    # 到达最终节点，解析命令
    if isinstance(current, str):
        return current, None
    elif isinstance(current, dict):
        cmd_str = current.get('cmd', '')
        saved_cwd = current.get('cwd')
        if cmd_str:
            return cmd_str, saved_cwd
        else:
            # 如果是字典但没有 cmd 字段，可能是中间分组
            return None, None
    
    return None, None


def collect_all_alias_paths(aliases, prefix=''):
    """递归收集所有别名路径
    
    Args:
        aliases: 别名字典
        prefix: 当前前缀
    
    Returns:
        list: 所有别名路径列表
    """
    paths = []
    
    if not isinstance(aliases, dict):
        return paths
    
    for key, value in aliases.items():
        current_path = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, str):
            # 简单字符串别名
            paths.append(current_path)
        elif isinstance(value, dict):
            if 'cmd' in value:
                # 完整形式的别名
                paths.append(current_path)
            else:
                # 分组对象，递归收集
                paths.extend(collect_all_alias_paths(value, current_path))
    
    return paths


def parse_arguments(cmd_str, args):
    """解析参数并替换占位符
    
    规则：
    - 无占位符 → 自动透传所有参数
    - {args} → 替换为全部参数
    - {0}, {1}, ... → 精确替换对应位置的参数（支持非连续索引）
    """
    # 处理 {args} 占位符
    if '{args}' in cmd_str:
        all_args = ' '.join(args)
        cmd_str = cmd_str.replace('{args}', all_args)
        return cmd_str
    
    # 检查是否有数字占位符
    placeholders = re.findall(r'\{(\d+)\}', cmd_str)
    
    if not placeholders:
        # 无占位符，自动透传
        return cmd_str + ' ' + ' '.join(args) if args else cmd_str
    
    # 处理 {0}, {1}, ... 精确占位符
    for placeholder in placeholders:
        index = int(placeholder)
        if index < len(args):
            cmd_str = cmd_str.replace('{%s}' % placeholder, args[index])
        else:
            raise ValueError(f"Missing argument for placeholder {{{placeholder}}}")
    
    return cmd_str


class AliasedGroup(click.Group):
    """支持从 alias.byk.json 动态解析别名的 Group"""

    def resolve_command(self, ctx, args):
        # 1. 尝试正常解析（内置子命令优先）
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError:
            # 如果解析失败，可能是别名
            pass

        # 2. 查别名（支持分组路径）
        if not args:
            return super().resolve_command(ctx, args)

        cmd_name = args[0]
        aliases = load_aliases(merge_local=True)
        
        # 尝试解析别名（包括分组路径）
        cmd_str, saved_cwd = resolve_nested_alias(aliases, cmd_name)
        
        if cmd_str:
            # 解析参数
            try:
                final_cmd = parse_arguments(cmd_str, args[1:])
            except ValueError as e:
                raise click.UsageError(str(e))
            
            # 确定 cwd（CLI > 配置）- CLI 选项在 ctx.params 中
            cli_cwd = ctx.params.get('cwd')
            target_cwd = cli_cwd if cli_cwd else saved_cwd
            
            # 计算绝对路径
            if target_cwd:
                actual_cwd = os.path.abspath(target_cwd)
            else:
                actual_cwd = os.getcwd()
            
            # 安全检查
            if is_dangerous(final_cmd):
                click.secho("\n[WARNING] DANGEROUS COMMAND DETECTED!", fg="red", bold=True)
                click.secho(f"Command: {final_cmd}", fg="red")
                if not click.confirm("This command contains potentially harmful operations. Are you sure you want to execute it?", default=False):
                    click.echo("Execution aborted.")
                    raise SystemExit(1)
            
            # 显示执行信息
            click.echo()
            click.echo(f"fcbyk-cli v{get_version()} {cmd_name} ")
            click.echo(f"Running in {actual_cwd}")
            if RICH_AVAILABLE:
                console = Console()
                console.print(f"Running: [bold green]{final_cmd}[/bold green]")
            else:
                click.echo(f"Running: {final_cmd}")
            click.echo()
            
            try:
                subprocess.run(final_cmd, shell=True, cwd=actual_cwd)
            except Exception as e:
                click.secho(f"Error executing command: {e}", fg="red", err=True)
            
            # 阻止 Click 继续执行其他命令
            raise SystemExit(0)

        # 3. 没找到别名，提供有用的错误提示
        all_paths = collect_all_alias_paths(aliases)
        if all_paths:
            # 查找是否有相似的路径
            similar = [p for p in all_paths if p.startswith(cmd_name + '.') or cmd_name.startswith(p + '.')]
            if similar:
                raise click.UsageError(
                    f"Unknown alias '{cmd_name}'.\n"
                    f"Did you mean one of these?\n"
                    f"  " + "\n  ".join(similar[:5])  # 最多显示 5 个
                )
        
        raise click.UsageError(f"Unknown alias '{cmd_name}'")

        # 3. 如果没别名，再次尝试（这会抛出正常的 Click 错误）
        return super().resolve_command(ctx, args)
