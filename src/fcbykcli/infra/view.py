"""根命令状态面板。"""

from __future__ import annotations

import click

from fcbykcli.core.context import AppContext
from fcbykcli.core.environment import EnvironmentInfo
from fcbykcli.infra.aliases import render_alias_lines
from fcbykcli.infra.daemon import list_daemons
from fcbykcli.infra.registry import plugin_display_info


def format_version_line(environment: EnvironmentInfo) -> str:
    """格式化版本信息。"""
    return (
        f"{environment.app_name} v{environment.version} | "
        f"Python {environment.python_version} | {environment.platform_name}"
    )


def render_dashboard(context: AppContext, cli: click.Group) -> None:
    """Show CLI status overview."""

    click.echo()
    click.echo("Plugins:")
    for plugin in plugin_display_info:
        click.echo(f"  {plugin}")

    click.echo()
    click.echo("Aliases:")
    alias_lines = render_alias_lines(context)
    if alias_lines:
        for line in alias_lines:
            click.echo(f"  {line}")
    else:
        click.echo("  None")

    click.echo()
    click.echo("Background Daemons:")
    daemons = list_daemons(context)
    if daemons:
        for daemon in daemons:
            status = "running" if daemon["alive"] else "stopped"
            click.echo(
                f'  {daemon["name"]} pid={daemon["pid"]} port={daemon["port"] or "-"} {status}'
            )
    else:
        click.echo("  None")
    click.echo()
