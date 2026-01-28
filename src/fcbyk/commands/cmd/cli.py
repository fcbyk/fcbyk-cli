import click
import subprocess
import re
from fcbyk.utils import storage

# 持久化配置
DATA_FILE = storage.get_path('cmd_data.json', subdir='data')
DEFAULT_DATA = {}

# 危险命令检测正则列表
DANGEROUS_PATTERNS = [
    r'rm\s+-[^ ]*[rf]',             # rm -rf, rm -f, rm -rvf
    r'git\s+push\s+.*(-f|--force)',  # git push -f, git push --force
    r'shutdown',                    # 关机
    r'reboot',                      # 重启
    r'format\s+[a-zA-Z]:',          # Windows 格式化
    r'rd\s+/[sq]',                  # Windows 静默删除目录
    r'del\s+/[sq]',                 # Windows 静默删除文件
    r'>\s*/dev/sd',                 # Linux 直接写磁盘
]

def load_commands():
    """从磁盘加载命令数据"""
    return storage.load_json(DATA_FILE, default=DEFAULT_DATA, create_if_missing=True)

def save_commands(commands):
    """保存命令数据到磁盘"""
    storage.save_json(DATA_FILE, commands)

def is_dangerous(command):
    """检测命令是否包含危险操作"""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

@click.group(name='cmd', help='Manage reusable command snippets')
def cmd():
    """Manage reusable command snippets."""
    pass

@cmd.command(name='add')
@click.argument('name')
@click.argument('command')
@click.option('--cwd', '-C', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True), help='Specify the default directory for the command')
@click.option('--yes', '-y', is_flag=True, help='Confirm overwrite of existing command')
def add(name, command, cwd, yes):
    """Add a new command snippet.
    
    Supports using {1}, {2} or $1, $2 as placeholders.
    Note: When using $1 in double quotes, the Shell might try to expand it.
    Use single quotes or {1} syntax to avoid this.
    """
    commands = load_commands()
    
    # 检查是否已存在同名命令
    if name in commands and not yes:
        old_cmd = commands[name]
        old_cmd_str = old_cmd if isinstance(old_cmd, str) else old_cmd.get("command", "")
        if not click.confirm(f"Command '{name}' already exists (Current: {old_cmd_str}). Overwrite?"):
            click.echo("Aborted.")
            return

    # 存储为字典以支持扩展属性（如 cwd）
    cmd_info = {
        "command": command
    }
    if cwd:
        # 保存时已经是绝对路径（由 click.Path(resolve_path=True) 处理）
        cmd_info["cwd"] = cwd
        
    commands[name] = cmd_info
    save_commands(commands)
    
    msg = f"Added command '{name}': {command}"
    if cwd:
        msg += f" (CWD: {cwd})"
    click.echo(msg)
    
    # 检查潜在的 Shell 变量展开问题
    if '$' in command and any(f'${i}' not in command for i in range(1, 10) if f'${i}' in command):
        pass
    
    # 如果发现异常空格，发出警告
    if command.count('  ') > 0 or command.endswith(' '):
         click.secho("\nWarning: Your command contains suspicious empty spaces. ", fg="yellow", err=True)
         click.secho("If you used $1, $2 in double quotes, the shell might have eaten them.", fg="yellow", err=True)
         click.secho("Try using single quotes: fcbyk cmd add name 'command $1'", fg="yellow", err=True)
         click.secho("Or use shell-safe syntax: fcbyk cmd add name \"command {1}\"", fg="yellow", err=True)

@cmd.command(name='run')
@click.argument('name')
@click.argument('args', nargs=-1)
@click.option('--cwd', '-C', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True), help='Temporarily specify or override the execution directory')
def run(name, args, cwd):
    """Run a saved command snippet with optional arguments."""
    import os
    commands = load_commands()
    if name in commands:
        cmd_data = commands[name]
        
        # 兼容旧版本的字符串格式
        if isinstance(cmd_data, str):
            command = cmd_data
            saved_cwd = None
        else:
            command = cmd_data.get("command", "")
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
        click.echo(f"Command '{name}' not found.")

@cmd.command(name='list')
def list_cmds():
    """List all saved command snippets."""
    from fcbyk.cli_support import print_commands
    print_commands(show_empty=True, leading_newline=False)

@cmd.command(name='rm')
@click.argument('name')
def rm(name):
    """Remove a command snippet."""
    commands = load_commands()
    if name in commands:
        del commands[name]
        save_commands(commands)
        click.echo(f"Removed command '{name}'.")
    else:
        click.echo(f"Command '{name}' not found.")
