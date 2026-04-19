"""根命令状态面板。"""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

from bykcli.core.context import AppContext
from bykcli.core.environment import EnvironmentInfo
from bykcli.infra.aliases import render_alias_lines, wrap_text, get_terminal_width
from bykcli.infra.daemon import list_daemons
from bykcli.infra.registry import plugin_load_errors


def format_version_line(environment: EnvironmentInfo) -> Text:
    """格式化版本信息。"""
    text = Text()
    text.append(" Version: ", style="orange1")
    text.append(f"v{environment.version}\n")
    text.append("  Python: ", style="orange1")
    text.append(f"{environment.python_version}\n")
    text.append("Platform: ", style="orange1")
    text.append(f"{environment.platform_name}")
    return text   


def _get_status_symbol(alive: bool) -> str:
    """获取状态符号。"""
    return "●" if alive else "○"


def render_dashboard(context: AppContext, cli: click.Group) -> None:
    """Show CLI status overview."""
    console = Console()

    welcome_text = Text()
    welcome_text.append(f"✦ Welcome to Bykcli!", style="bold cyan")
    welcome_text.append(f" {context.version}", style="dim")
    welcome_text.append("\n")
    welcome_text.append("\n")
    welcome_text.append("Docs: https://cli.fcbyk.com", style="dim")

    welcome_panel = Panel(
        welcome_text,
        box=box.ASCII,
        border_style="dim",
        padding=(0, 1),
        width=56,
    )
    console.print()
    console.print(welcome_panel)
    console.print()

    if plugin_load_errors:
        click.echo()
        for plugin_name, error_msg in plugin_load_errors:
            colored_text = click.style(f"  {plugin_name}: {error_msg}", fg="red", bold=True)
            click.echo(colored_text)
        click.echo()
    
    # Get full help text from Click
    ctx = click.Context(cli)
    ctx.info_name = 'byk'  # Set the command name
    help_text = cli.get_help(ctx)
    click.echo(help_text)

    console.print()
    console.print(Text("Aliases:"))
    alias_lines = render_alias_lines(context)
    if alias_lines:
        for line in alias_lines:
            click.echo(f"  {line}")
    else:
        console.print(Text("  No aliases configured.", style="dim"))
        console.print(Text("  Manage your aliases in alias.byk.json", style="dim"))

    console.print()
    console.print(Text("Daemons:"))
    daemons = list_daemons(context)
    if daemons:
        for daemon in daemons:
            alive = daemon["alive"]
            status = "running" if alive else "stopped"
            status_color = "green" if alive else "red"
            status_symbol = _get_status_symbol(alive)
            port_str = str(daemon["port"]) if daemon["port"] else "?"
            
            colored_symbol = click.style(status_symbol, fg=status_color)
            colored_status = click.style(status, fg=status_color)
            click.echo(
                f"  {colored_symbol} {daemon['name']}: PID {daemon['pid']} (port {port_str}) [{colored_status}]"
            )
        
        console.print()
        console.print(Text("  Use 'byk --kill <PID|all>' to stop daemons.", style="dim"))
    else:
        console.print(Text("  No background daemons running.", style="dim"))
        help_text = "Use options like '-D' to start a background service in commands that support it."
        indent = "  "
        terminal_width = get_terminal_width()
        max_width = terminal_width - len(indent)
        
        wrapped_lines = wrap_text(help_text, max_width)
        for line in wrapped_lines:
            console.print(Text(f"{indent}{line}", style="dim"))
    click.echo()
