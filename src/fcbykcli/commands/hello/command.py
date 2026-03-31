"""示例命令。"""

from __future__ import annotations

import click

from fcbykcli.core.context import AppContext
from fcbykcli.core.paths import register_path_provider
from fcbykcli.runtime import CommandContext, pass_command_context


@click.command(help="示例子命令，用于验证动态注册链路。")
@click.option("--name", default="world", show_default=True, help="问候对象。")
@click.option("--reset-state", is_flag=True, help="清空 hello 的本地状态。")
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


def hello_path_items(context: AppContext) -> list[tuple[str, str]]:
    """返回 hello 相关路径。"""
    return [("数据文件", str(context.command_store("hello").path))]


def register(cli: click.Group) -> None:
    """注册命令。"""
    cli.add_command(hello)
    register_path_provider("hello", hello_path_items)
