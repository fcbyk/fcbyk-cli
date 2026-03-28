import click
import subprocess
import re
import os
from fcbyk.utils import storage
from fcbyk.cli_support.output import get_display_width, pad_display_text

DATA_FILE = storage.get_path('scripts.byk.json')
DEFAULT_DATA = {}

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

def load_commands(merge_local=False):
    """从磁盘加载命令数据"""
    commands = storage.load_json(DATA_FILE, default=DEFAULT_DATA, create_if_missing=True)
    
    if merge_local:
        local_path = os.path.abspath('scripts.byk.json')
        if os.path.exists(local_path):
            try:
                local_cmds = storage.load_json(local_path, default={}, create_if_missing=False)
                if local_cmds:
                    # 本地配置覆盖全局配置
                    commands = commands.copy()
                    commands.update(local_cmds)
            except Exception as e:
                click.secho(f"Warning: Failed to load local scripts.byk.json: {e}", fg="yellow", err=True)
    
    return commands

def save_commands(commands):
    """保存命令数据到磁盘"""
    storage.save_json(DATA_FILE, commands)

def is_dangerous(command):
    """检测命令是否包含危险操作"""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

@click.command(name='run', help='Run reusable command scripts from scripts.byk.json')
@click.argument('name', required=False)
@click.argument('args', nargs=-1)
@click.option('--cwd', '-C', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True), help='Temporarily specify or override the execution directory')
def run(name, args, cwd):
    """Run a saved command snippet with optional arguments."""
    if name is None:
        # 无参数时列出所有脚本
        list_scripts()
        return
    
    commands = load_commands(merge_local=True)
    if name in commands:
        cmd_data = commands[name]
        
        # 兼容旧版本的字符串格式
        if isinstance(cmd_data, str):
            command = cmd_data
            saved_cwd = None
        else:
            command = cmd_data.get("cmd", "")
            saved_cwd = cmd_data.get("cwd")
        
        # 优先级：命令行指定的 cwd > 保存的 cwd
        target_cwd = cwd if cwd else saved_cwd
        
        # 检查目录是否存在
        if target_cwd and not os.path.exists(target_cwd):
            click.secho(f"Error: Directory '{target_cwd}' not found.", fg="red", err=True)
            return

        # 替换占位符：同时支持 $1 和 {1} 风格
        for i, arg in enumerate(args, 1):
            command = command.replace(f"${i}", arg)
            command = command.replace(f"{{{i}}}", arg)
            
        # 危险命令检测
        if is_dangerous(command):
            click.secho("\n[WARNING] DANGEROUS COMMAND DETECTED!", fg="red", bold=True)
            click.secho(f"Command: {command}", fg="red")
            if not click.confirm("This command contains potentially harmful operations. Are you sure you want to execute it?", default=False):
                click.echo("Execution aborted.")
                return

        if target_cwd:
            click.echo(f"Running in {target_cwd}: {command}")
        else:
            click.echo(f"Running: {command}")
            
        try:
            subprocess.run(command, shell=True, cwd=target_cwd)
        except Exception as e:
            click.secho(f"Error executing command: {e}", fg="red", err=True)
    else:
        click.echo(f"Script '{name}' not found.")

def list_scripts():
    """List all saved scripts."""
    commands = load_commands(merge_local=True)
    if commands:
        click.echo("Scripts:")
        items = list(commands.items())
        max_name_len = max(get_display_width(name) for name, _ in items)
        for name, cmd_data in items:
            if isinstance(cmd_data, str):
                command = cmd_data
                cwd_str = ""
            else:
                command = cmd_data.get("cmd", "")
                cwd = cmd_data.get("cwd")
                cwd_str = f" [CWD: {cwd}]" if cwd else ""
            
            name_with_padding = pad_display_text(name, max_name_len, min_spaces=2)
            click.echo("  {}->  {}{}".format(name_with_padding, command, cwd_str))
    else:
        click.echo("No scripts saved yet.")
