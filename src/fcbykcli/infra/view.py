"""根命令状态面板。"""

from __future__ import annotations

import click

from fcbykcli.core.context import AppContext
from fcbykcli.core.environment import EnvironmentInfo
from fcbykcli.infra.aliases import render_alias_lines
from fcbykcli.infra.daemon import list_daemons


def format_version_line(environment: EnvironmentInfo) -> str:
    """格式化版本信息。"""
    return (
        f"{environment.app_name} v{environment.version} | "
        f"Python {environment.python_version} | {environment.platform_name}"
    )


def render_dashboard(context: AppContext, cli: click.Group) -> None:
    """展示 CLI 状态总览。"""
    click.echo(format_version_line(context.environment))
    click.echo(f"CLI 家目录：{context.paths.root_dir}")
    click.echo(f"别名文件：{context.paths.alias_file}")
    click.echo(f"日志目录：{context.paths.logs_dir}")
    click.echo()
    click.echo("已注册命令:")
    for command_name in sorted(cli.commands):
        click.echo(f"  - {command_name}")

    click.echo()
    click.echo("别名:")
    alias_lines = render_alias_lines(context)
    if alias_lines:
        for line in alias_lines:
            click.echo(f"  - {line}")
    else:
        click.echo("  - 暂无")

    click.echo()
    click.echo("后台进程:")
    daemons = list_daemons(context)
    if daemons:
        for daemon in daemons:
            status = "running" if daemon["alive"] else "stopped"
            click.echo(
                f'  - {daemon["name"]} pid={daemon["pid"]} port={daemon["port"] or "-"} {status}'
            )
    else:
        click.echo("  - 暂无")
    click.echo()
