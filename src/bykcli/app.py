"""CLI 应用装配。"""

from __future__ import annotations

from dataclasses import dataclass

import click

from bykcli.core.context import AppContext
from bykcli.infra.aliases import AliasAwareGroup
from bykcli.infra.daemon import kill_daemon_callback
from bykcli.infra.logging import setup_logging
from bykcli.infra.registry import register_builtin_plugins, register_plugins
from bykcli.infra.view import render_dashboard
from bykcli.runtime import build_runtime
import bykcli.plugins as builtin_plugins


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

    from bykcli.infra.view import format_version_line
    from rich.console import Console

    app_context: AppContext = ctx.obj.context if ctx.obj else build_runtime()
    console = Console()
    console.print(format_version_line(app_context.environment))
    ctx.exit()


def list_plugins_callback(
    ctx: click.Context,
    _param: click.Parameter,
    value: bool,
) -> None:
    """List all external plugins and their versions."""
    if not value or ctx.resilient_parsing:
        return

    from importlib.metadata import entry_points, version, PackageNotFoundError, distributions
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()
    
    try:
        plugin_entries = entry_points(group="bykcli.plugins")
    except TypeError:
        plugin_entries = entry_points().get("bykcli.plugins", [])

    if not plugin_entries:
        console.print("[dim]No external plugins installed.[/dim]")
        ctx.exit()

    table = Table(
        title="[bold cyan]External Plugins[/bold cyan]",
        box=box.ROUNDED,
        border_style="bright_blue",
        header_style="bold bright_magenta",
        show_lines=True,
        padding=(0, 2),
        collapse_padding=False,
    )
    table.add_column("Package Name", style="bold cyan", no_wrap=True)
    table.add_column("Version", style="bold green", justify="center")
    table.add_column("Entry Point", style="dim", overflow="fold")

    for entry in plugin_entries:
        pkg_name = entry.name
        pkg_version = "unknown"
        
        candidates = [entry.name]
        
        if entry.name.startswith("bykcli"):
            candidates.append(f"bykcli-{entry.name[5:]}")
        else:
            candidates.append(f"bykcli-{entry.name}")
        
        candidates.append(entry.name.replace("-", "_"))
        candidates.append(entry.name.replace("_", "-"))
        
        try:
            module_path = entry.value.split(":")[0]
            top_level_pkg = module_path.split(".")[0]
            candidates.append(top_level_pkg)
            if not top_level_pkg.startswith("bykcli"):
                candidates.append(f"bykcli-{top_level_pkg}")
        except (IndexError):
            pass
        
        found = False
        for candidate in candidates:
            if not candidate:
                continue
            try:
                pkg_version = version(candidate)
                pkg_name = candidate
                found = True
                break
            except PackageNotFoundError:
                continue
        
        table.add_row(pkg_name, pkg_version, entry.value)

    click.echo()
    console.print(table)
    click.echo()
    ctx.exit()


def create_cli() -> click.Group:
    """创建根 CLI 对象。"""

    runtime: AppContext | None = None

    def get_runtime() -> AppContext:
        nonlocal runtime
        if runtime is None:
            runtime = build_runtime()
        return runtime

    temp_runtime = build_runtime()
    setup_logging(temp_runtime)

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
    @click.option(
        "--list",
        "-l",
        is_flag=True,
        callback=list_plugins_callback,
        expose_value=False,
        is_eager=True,
        help="List all external plugins and their versions.",
    )
    @click.pass_context
    def cli(ctx: click.Context) -> None:
        ctx.obj = CliState(context=get_runtime())
        ctx.obj.context.logger.info("BYK CLI v%s started", ctx.obj.context.version)
        if ctx.invoked_subcommand is None:
            render_dashboard(ctx.obj.context, cli)

    cli.runtime_provider = get_runtime
    register_builtin_plugins(cli, builtin_plugins)
    register_plugins(cli)
    return cli
