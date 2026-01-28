"""CLI 命令回调函数"""
import click


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


def print_commands(show_empty=False, leading_newline=True):
    """打印已保存的命令脚本列表"""
    try:
        from fcbyk.commands.cmd.cli import load_commands
        commands = load_commands()
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
                    command = cmd_data.get("command", "")
                    cwd = cmd_data.get("cwd")
                    cwd_str = f" [CWD: {cwd}]" if cwd else ""
                
                padding = " " * (max_name_len - len(str(name)) + 2)
                click.echo(f"  {name}{padding}->  {command}{cwd_str}")
            click.echo()
        elif show_empty:
            click.echo("No scripts saved yet.")
    except Exception:
        pass
