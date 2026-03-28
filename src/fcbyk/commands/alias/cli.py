import click
import subprocess
import re
import os
from ...utils import storage

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


def parse_arguments(cmd_str, args):
    """解析参数并替换占位符
    
    规则：
    - 无占位符 → 自动透传所有参数
    - {args} → 替换为全部参数
    - {0}, {1}, ... → 精确替换对应位置的参数
    """
    has_placeholder = '{args}' in cmd_str or any('{%d}' % i in cmd_str for i in range(len(args)))
    
    if not has_placeholder:
        # 无占位符，自动透传
        return cmd_str + ' ' + ' '.join(args) if args else cmd_str
    
    # 处理 {args} 占位符
    if '{args}' in cmd_str:
        all_args = ' '.join(args)
        cmd_str = cmd_str.replace('{args}', all_args)
        return cmd_str
    
    # 处理 {0}, {1}, ... 精确占位符
    for i, arg in enumerate(args):
        cmd_str = cmd_str.replace('{%d}' % i, arg)
    
    # 检查是否有未替换的占位符（参数不足）
    remaining_placeholders = re.findall(r'\{\d+\}', cmd_str)
    if remaining_placeholders:
        raise ValueError(f"Missing arguments for placeholders: {remaining_placeholders}")
    
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

        # 2. 查别名
        if not args:
            return super().resolve_command(ctx, args)

        cmd_name = args[0]
        aliases = load_aliases(merge_local=True)
        alias_data = aliases.get(cmd_name)
        
        if alias_data:
            # 支持简单字符串和完整形式
            if isinstance(alias_data, str):
                cmd_str = alias_data
                saved_cwd = None
            elif isinstance(alias_data, dict):
                cmd_str = alias_data.get('cmd', '')
                saved_cwd = alias_data.get('cwd')
            else:
                raise click.UsageError(f"Invalid alias format for '{cmd_name}'")
            
            # 解析参数
            try:
                final_cmd = parse_arguments(cmd_str, args[1:])
            except ValueError as e:
                raise click.UsageError(str(e))
            
            # 确定 cwd（CLI > 配置）- CLI 选项在 ctx.params 中
            cli_cwd = ctx.params.get('cwd')
            target_cwd = cli_cwd if cli_cwd else saved_cwd
            
            # 安全检查
            if is_dangerous(final_cmd):
                click.secho("\n[WARNING] DANGEROUS COMMAND DETECTED!", fg="red", bold=True)
                click.secho(f"Command: {final_cmd}", fg="red")
                if not click.confirm("This command contains potentially harmful operations. Are you sure you want to execute it?", default=False):
                    click.echo("Execution aborted.")
                    raise SystemExit(1)
            
            # 直接执行 shell 命令
            if target_cwd:
                click.echo(f"Running in {target_cwd}: {final_cmd}")
            else:
                click.echo(f"Running: {final_cmd}")
            
            try:
                subprocess.run(final_cmd, shell=True, cwd=target_cwd)
            except Exception as e:
                click.secho(f"Error executing command: {e}", fg="red", err=True)
            
            # 阻止 Click 继续执行其他命令
            raise SystemExit(0)

        # 3. 如果没别名，再次尝试（这会抛出正常的 Click 错误）
        return super().resolve_command(ctx, args)


@click.command(name='alias', help='Manage command aliases (deprecated: edit alias.byk.json directly)')
def execute_alias():
    """管理命令别名（已废弃：请直接编辑 alias.byk.json）"""
    click.echo("The 'alias' command is deprecated.")
    click.echo("Please edit ~/.fcbyk/alias.byk.json or ./alias.byk.json directly.")
