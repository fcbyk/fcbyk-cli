"""CLI 命令回调函数"""
import click
from fcbyk.cli_support.output import get_display_width, pad_display_text


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
        from fcbyk.commands.alias.cli import load_aliases
        aliases = load_aliases(merge_local=True)
        if aliases:
            if leading_newline:
                click.echo()
            click.echo("Aliases:")
            items = list(aliases.items())
            max_name_len = max(get_display_width(name) for name, _ in items)
            for alias_name, alias_data in items:
                if isinstance(alias_data, str):
                    cmd_str = alias_data
                elif isinstance(alias_data, dict):
                    cmd_str = alias_data.get('cmd', '')
                else:
                    cmd_str = str(alias_data)
                alias_with_padding = pad_display_text(alias_name, max_name_len, min_spaces=2)
                click.echo("  {}->  {}".format(alias_with_padding, cmd_str))
            click.echo()
        elif show_empty:
            click.echo("No aliases configured.")
    except Exception:
        pass

