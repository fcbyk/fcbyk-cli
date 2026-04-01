"""paths 子命令插件。"""

from __future__ import annotations

import click

from fcbykcli.api import CommandContext, get_path_provider, global_path_items, pass_command_context


@click.command(help="显示 CLI 常用路径，可选查看某个子命令自己的数据路径。")
@click.argument("command_name", required=False)
@pass_command_context
def paths(ctx: CommandContext, command_name: str | None) -> None:
    """显示全局路径或某个子命令的附加路径。"""
    if command_name is None:
        for label, value in global_path_items(ctx.app):
            click.echo(f"{label}: {value}")
        return

    provider = get_path_provider(command_name)
    if provider is None:
        raise click.ClickException(f"未找到命令 {command_name} 的路径信息")

    items = provider(ctx.app)
    if not items:
        return

    for label, value in items:
        click.echo(f"{label}: {value}")


def register(cli: click.Group) -> None:
    """注册命令。"""
    cli.add_command(paths)
