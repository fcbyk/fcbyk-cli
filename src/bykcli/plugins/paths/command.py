"""paths 子命令插件。"""

from __future__ import annotations

import click
from rich.console import Console
from rich.text import Text

from bykcli.api import CommandContext, get_path_provider, global_path_items, pass_command_context


@click.command(help="Show common CLI paths, optionally view data paths for a specific subcommand.")
@click.argument("command_name", required=False)
@pass_command_context
def paths(ctx: CommandContext, command_name: str | None) -> None:
    """Show global paths or additional paths for a subcommand."""
    console = Console()
    
    if command_name is None:
        items = list(global_path_items(ctx.app))
    else:
        provider = get_path_provider(command_name)
        if provider is None:
            raise click.ClickException(f"No path information found for command {command_name}")

        items = provider(ctx.app)
        if not items:
            return
    
    max_label_len = max(len(label) for label, _ in items) if items else 0
    
    for label, value in items:
        padded_label = f"{label:>{max_label_len}}"
        text = Text()
        text.append(padded_label, style="orange1")
        text.append(": ", style="orange1")
        text.append(f"{value}")
        console.print(text)


def register(cli: click.Group) -> None:
    """注册命令。"""
    cli.add_command(paths)
