"""CLI 应用装配。"""

from __future__ import annotations

from dataclasses import dataclass

import click

from fcbykcli.core.context import AppContext
from fcbykcli.infra.aliases import AliasAwareGroup
from fcbykcli.infra.daemon import kill_daemon_callback
from fcbykcli.infra.logging import setup_logging
from fcbykcli.infra.registry import register_builtin_plugins, register_plugins
from fcbykcli.infra.view import render_dashboard
from fcbykcli.runtime import build_runtime
import fcbykcli.plugins as builtin_plugins


@dataclass(slots=True)
class CliState:
    """Click 根命令共享状态。"""

    context: AppContext


def version_callback(
    ctx: click.Context,
    _param: click.Parameter,
    value: bool,
) -> None:
    """Show version and exit."""
    if not value or ctx.resilient_parsing:
        return

    from fcbykcli.infra.view import format_version_line

    app_context: AppContext = ctx.obj.context if ctx.obj else build_runtime()
    click.echo(format_version_line(app_context.environment))
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
        help="Show version and exit.",
    )
    @click.option(
        "--kill",
        "-k",
        type=str,
        callback=kill_daemon_callback,
        expose_value=False,
        is_eager=True,
        help='Kill background daemon processes. Use "all" to kill all or specify PID.',
    )
    @click.pass_context
    def cli(ctx: click.Context) -> None:
        ctx.obj = CliState(context=get_runtime())
        if ctx.invoked_subcommand is None:
            render_dashboard(ctx.obj.context, cli)

    cli.runtime_provider = get_runtime
    register_builtin_plugins(cli, builtin_plugins)
    register_plugins(cli)
    return cli
