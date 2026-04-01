"""paths 子命令插件。"""

from __future__ import annotations

import click

from fcbykcli.api import CommandContext, get_path_provider, global_path_items, pass_command_context


@click.command(help="Show common CLI paths, optionally view data paths for a specific subcommand.")
@click.argument("command_name", required=False)
@pass_command_context
def paths(ctx: CommandContext, command_name: str | None) -> None:
    """Show global paths or additional paths for a subcommand."""
    if command_name is None:
        for label, value in global_path_items(ctx.app):
            click.echo(f"{label}: {value}")
        return

    provider = get_path_provider(command_name)
    if provider is None:
        raise click.ClickException(f"No path information found for command {command_name}")

    items = provider(ctx.app)
    if not items:
        return

    for label, value in items:
        click.echo(f"{label}: {value}")


def register(cli: click.Group) -> None:
    """注册命令。"""
    cli.add_command(paths)
