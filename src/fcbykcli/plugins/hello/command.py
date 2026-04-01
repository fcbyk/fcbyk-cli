"""示例子命令插件。"""

from __future__ import annotations

import click

from fcbykcli.api import CommandContext, PathItem, pass_command_context, register_path_provider


@click.command(help="Example subcommand to verify dynamic registration.")
@click.option("--name", default="world", show_default=True, help="The object to greet.")
@click.option("--reset-state", is_flag=True, help="Clear hello's local state.")
@pass_command_context
def hello(ctx: CommandContext, name: str, reset_state: bool) -> None:
    store = ctx.state
    if reset_state:
        store.clear()
        click.echo("hello state cleared")
        return

    count = int(store.get("run_count", 0)) + 1
    store.update({"run_count": count, "last_name": name})

    click.echo(f"hello {name}")
    click.echo(f"run count: {count}")
    click.echo(f"state file: {store.path}")


def hello_path_items(context) -> list[PathItem]:
    """Return hello-related paths."""
    return [("Data File", str(context.command_store("hello").path))]


def register(cli: click.Group) -> None:
    """注册命令。"""
    cli.add_command(hello)
    register_path_provider("hello", hello_path_items)
