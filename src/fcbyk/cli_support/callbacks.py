"""CLI 命令回调函数"""
import click
import os
import sys
import shutil
import subprocess


def get_version():
    """获取版本号"""
    try:
        from importlib import metadata
        return metadata.version("fcbyk-cli")
    except Exception:
        try:
            import pkg_resources
            return pkg_resources.get_distribution("fcbyk-cli").version
        except Exception:
            return "unknown"


def version_callback(ctx, param, value):
    """版本号回调，使用 rich 渲染精美界面"""
    if not value or ctx.resilient_parsing:
        return
        
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.padding import Padding
        import sys
        import platform

        console = Console()
        
        table = Table.grid(padding=(0, 1))
        table.add_column(style="cyan", justify="right")
        table.add_column(style="white")
        
        table.add_row("Version:", f"[bold green]v{get_version()}[/bold green]")
        table.add_row("Python:", sys.version.split()[0])
        table.add_row("Platform:", platform.platform())
        
        panel = Panel(
            table,
            title="[bold magenta]FCBYK-CLI[/bold magenta]",
            title_align="left",
            border_style="bright_blue",
            expand=False,
            padding=(1, 2)
        )
        
        # 使用 Padding 包裹 Panel 以实现类似 margin 的效果
        # (上下, 左右)
        margin_panel = Padding(panel, (1, 1))
        
        console.print(margin_panel)
    except ImportError:
        # 如果 rich 不可用，回退到普通打印
        click.echo(f"v{get_version()}")
        
    ctx.exit()


def print_aliases(show_empty=False, leading_newline=True):
    """打印别名列表"""
    try:
        from fcbyk.commands.alias import read_aliases
        aliases = read_aliases()
        if aliases:
            if leading_newline:
                click.echo()
            click.echo("Aliases:")
            items = list(aliases.items())
            max_name_len = max(len(str(name)) for name, _ in items)
            for alias_name, command_parts in items:
                if isinstance(command_parts, list):
                    cmd_str = " ".join(command_parts)
                else:
                    cmd_str = str(command_parts)
                padding = " " * (max_name_len - len(str(alias_name)) + 2)
                click.echo(f"  {alias_name}{padding}->  {cmd_str}")
            click.echo()
        elif show_empty:
            click.echo("No aliases configured.")
    except Exception:
        pass


def print_commands(show_empty=False, leading_newline=True, merge_local=False):
    """打印已保存的命令脚本列表"""
    try:
        from fcbyk.commands.run.cli import load_commands
        commands = load_commands(merge_local=merge_local)
        if commands:
            if leading_newline:
                click.echo()
            click.echo("Scripts:")
            items = list(commands.items())
            max_name_len = max(len(str(name)) for name, _ in items)
            for name, cmd_data in items:
                if isinstance(cmd_data, str):
                    command = cmd_data
                    cwd_str = ""
                else:
                    command = cmd_data.get("cmd", "")
                    cwd = cmd_data.get("cwd")
                    cwd_str = f" [CWD: {cwd}]" if cwd else ""
                
                padding = " " * (max_name_len - len(str(name)) + 2)
                click.echo(f"  {name}{padding}->  {command}{cwd_str}")
            click.echo()
        elif show_empty:
            click.echo("No scripts saved yet.")
    except Exception:
        pass


def paths_callback(ctx, param, value):
    """Callback for --paths option to show file paths."""
    if not value or ctx.resilient_parsing:
        return
    from fcbyk import defaults
    from fcbyk.utils import storage
    
    config_path = storage.get_path(defaults.CONFIG_FILE)
    data_dir = os.path.dirname(config_path)
    log_dir = os.path.join(data_dir, "log")
    
    click.echo("数据目录: {}".format(data_dir))
    click.echo("日志目录: {}".format(log_dir))
    click.echo("配置文件: {}".format(config_path))
    ctx.exit()


def init_callback(ctx, param, value):
    """Callback for --init option to reset configuration."""
    if not value or ctx.resilient_parsing:
        return
    from fcbyk import defaults
    from fcbyk.utils import storage
    
    config_path = storage.get_path(defaults.CONFIG_FILE)
    data_dir = os.path.dirname(config_path)
    
    # 确认操作
    if click.confirm('此操作将删除 ~/.fcbyk 目录并重新生成默认配置,是否继续?'):
        try:
            # 删除 .fcbyk 目录
            if os.path.exists(data_dir):
                shutil.rmtree(data_dir)
                click.echo("已删除目录: {}".format(data_dir))
            
            # 重新创建默认配置
            storage.save_json(config_path, defaults.DEFAULT_CONFIG)
            click.echo("已重新生成默认配置: {}".format(config_path))
            click.secho("初始化完成!", fg="green")
        except Exception as e:
            click.secho("初始化失败: {}".format(str(e)), fg="red", err=True)
            ctx.exit(1)
    else:
        click.echo("操作已取消")
    
    ctx.exit()


def uninstall_callback(ctx, param, value):
    """Callback for --uninstall option to uninstall fcbyk."""
    if not value or ctx.resilient_parsing:
        return
    from fcbyk import defaults
    from fcbyk.utils import storage
    
    config_path = storage.get_path(defaults.CONFIG_FILE)
    data_dir = os.path.dirname(config_path)
    
    # 确认操作
    if click.confirm('此操作将删除 ~/.fcbyk 目录并卸载 fcbyk-cli,是否继续?'):
        try:
            # 删除 .fcbyk 目录
            if os.path.exists(data_dir):
                shutil.rmtree(data_dir)
                click.echo("已删除目录: {}".format(data_dir))
            
            click.echo("正在卸载 fcbyk...")
            # 执行 pip uninstall
            result = subprocess.call([sys.executable, "-m", "pip", "uninstall", "fcbyk-cli", "-y"])
            
            if result == 0:
                click.secho("卸载完成!", fg="green")
            else:
                click.secho("卸载过程中出现错误", fg="yellow")
        except Exception as e:
            click.secho("卸载失败: {}".format(str(e)), fg="red", err=True)
            ctx.exit(1)
    else:
        click.echo("操作已取消")
    
    ctx.exit()
