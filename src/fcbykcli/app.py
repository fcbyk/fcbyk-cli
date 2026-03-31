"""CLI 应用装配。"""

from __future__ import annotations

from dataclasses import dataclass

import click

from fcbykcli.core.aliases import AliasAwareGroup
from fcbykcli.core.context import AppContext
from fcbykcli.core.daemon import kill_daemon_callback
from fcbykcli.core.logging import setup_logging
from fcbykcli.core.registry import register_builtin_commands, register_plugins
from fcbykcli.core.runtime import build_runtime
from fcbykcli.core.view import render_dashboard


@dataclass(slots=True)
class CliState:
    """Click 根命令共享状态。"""

    context: AppContext


def version_callback(
    ctx: click.Context,
    _param: click.Parameter,
    value: bool,
) -> None:
    """输出版本并退出。"""
    if not value or ctx.resilient_parsing:
        return

    app_context: AppContext = ctx.obj.context if ctx.obj else build_runtime()
    click.echo(app_context.environment.format_version_line())
    ctx.exit()


def create_cli() -> click.Group:
    """创建根 CLI 对象。"""

    runtime: AppContext | None = None

    def get_runtime() -> AppContext:
        nonlocal runtime
        if runtime is None:
            runtime = build_runtime()
            setup_logging(runtime)
        return runtime

    @click.group(
        cls=AliasAwareGroup,
        context_settings={"help_option_names": ["-h", "--help"]},
        invoke_without_command=True,
    )
    @click.option(
        "--version",
        "-v",
        is_flag=True,
        callback=version_callback,
        expose_value=False,
        is_eager=True,
        help="显示版本并退出。",
    )
    @click.option(
        "--kill",
        "-k",
        type=str,
        callback=kill_daemon_callback,
        expose_value=False,
        is_eager=True,
        help='终止后台守护进程，可传入 "all" 或具体 PID。',
    )
    @click.pass_context
    def cli(ctx: click.Context) -> None:
        ctx.obj = CliState(context=get_runtime())
        if ctx.invoked_subcommand is None:
            render_dashboard(ctx.obj.context, cli)

    cli.runtime_provider = get_runtime
    register_builtin_commands(cli)
    register_plugins(cli)
    return cli
