"""环境信息命令。"""

from __future__ import annotations

import click

from fcbykcli.app import CliState


@click.command(help="显示运行环境信息。")
@click.pass_obj
def info(state: CliState) -> None:
    env = state.context.environment
    click.echo(f"app: {env.app_name}")
    click.echo(f"version: {env.version}")
    click.echo(f"python: {env.python_version}")
    click.echo(f"platform: {env.platform_name}")
    click.echo(f"executable: {env.executable}")


def register(cli: click.Group) -> None:
    """注册命令。"""
    cli.add_command(info)
