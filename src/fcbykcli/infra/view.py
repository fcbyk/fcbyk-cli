"""根命令状态面板。"""

from __future__ import annotations

import click

from fcbykcli.core.context import AppContext
from fcbykcli.core.environment import EnvironmentInfo
from fcbykcli.infra.aliases import render_alias_lines, wrap_text, get_terminal_width
from fcbykcli.infra.daemon import list_daemons
from fcbykcli.infra.registry import plugin_display_info


def format_version_line(environment: EnvironmentInfo) -> str:
    """格式化版本信息。"""
    return (
        f"{environment.app_name} v{environment.version} | "
        f"Python {environment.python_version} | {environment.platform_name}"
    )


def _get_status_symbol(alive: bool) -> str:
    """获取状态符号。"""
    return "●" if alive else "○"


def render_dashboard(context: AppContext, cli: click.Group) -> None:
    """Show CLI status overview."""

    click.echo()
    click.echo(click.style("Plugins:", bold=True))
    for plugin in plugin_display_info:
        click.echo(f"  {plugin}")

    click.echo()
    click.echo(click.style("Aliases:", bold=True))
    alias_lines = render_alias_lines(context)
    if alias_lines:
        for line in alias_lines:
            click.echo(f"  {line}")
    else:
        click.echo("  No aliases configured.")
        click.echo("  Manage your aliases in alias.byk.json")

    click.echo()
    click.echo(click.style("Background Daemons:", bold=True))
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
        
        click.echo()
        click.echo("  Use 'fcbyk --kill <PID|all>' to stop daemons.")
    else:
        click.echo("  No background daemons running.")
        help_text = "Use options like '-D' to start a background service in commands that support it."
        indent = "  "
        terminal_width = get_terminal_width()
        max_width = terminal_width - len(indent)
        
        wrapped_lines = wrap_text(help_text, max_width)
        for line in wrapped_lines:
            click.echo(f"{indent}{line}")
    click.echo()
