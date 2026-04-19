import click
from rich.console import Console

import fcbyk.svc as svc_core


console = Console()


@click.group(
    name="svc",
    help="Manage background services for fcbyk web servers.",
    invoke_without_command=True,
)
@click.pass_context
def svc(ctx) -> None:
    if ctx.invoked_subcommand is not None:
        return
    items = svc_core.status_all()
    if not items:
        console.print("No running services.")
        return
    console.print("[bold]Current background services:[/bold]\n")
    for item in items:
        alive = bool(item.get("alive"))
        status = "running" if alive else "stopped"
        status_color = "green" if alive else "red"
        status_symbol = "●"
        port = item.get("port")
        port_str = "?" if not port else str(port)
        console.print(
            "[{0}]{1}[/{0}] {2}: PID {3} (port {4}) [[{0}]{5}[/{0}]]".format(
                status_color,
                status_symbol,
                item.get("name"),
                item.get("pid"),
                port_str,
                status,
            ),
            highlight=False,
        )
    click.echo("\nUse 'fcbyk svc stop <service>' to stop all processes of a service.")
    click.echo("Use 'fcbyk svc stop all' to stop all services.")


@svc.command(name="stop")
@click.argument("name")
def svc_stop(name: str) -> None:
    if name == "all":
        results = []
        for svc_name in sorted(svc_core.SERVICE_REGISTRY.keys()):
            svc_results = svc_core.stop_service(svc_name)
            if svc_results:
                results.extend(svc_results)
        if not results:
            click.echo("No tracked processes for any service.")
            return
    else:
        if name not in svc_core.SERVICE_REGISTRY:
            click.echo("Error: unknown service '{0}'.".format(name), err=True)
            available = ", ".join(sorted(svc_core.SERVICE_REGISTRY.keys()))
            click.echo("Available services: {0}".format(available), err=True)
            raise click.Abort()
        results = svc_core.stop_service(name)
        if not results:
            click.echo("No tracked processes for service '{0}'.".format(name))
            return
    terminated = [r for r in results if r.get("status") == "terminated"]
    not_running = [r for r in results if r.get("status") == "not_running"]
    alive = [r for r in results if r.get("status") == "alive"]
    for item in terminated:
        name = item.get("name") or "unknown"
        pid = item.get("pid")
        click.echo("PID {0} ({1}) terminated.".format(pid, name))
    for item in not_running:
        name = item.get("name") or "unknown"
        pid = item.get("pid")
        click.echo("PID {0} ({1}) already not running.".format(pid, name))
    for item in alive:
        name = item.get("name") or "unknown"
        pid = item.get("pid")
        click.echo("PID {0} ({1}) could not be terminated.".format(pid, name), err=True)
    if alive:
        raise click.Abort()


@svc.command(name="status")
@click.argument("name", required=False)
def svc_status(name: str = None) -> None:
    if name is None:
        items = svc_core.status_all()
    else:
        if name not in svc_core.SERVICE_REGISTRY:
            console.print("Error: unknown service '{0}'.".format(name))
            available = ", ".join(sorted(svc_core.SERVICE_REGISTRY.keys()))
            console.print("Available services: {0}".format(available))
            raise click.Abort()
        items = svc_core.status_service(name)
    if not items:
        if name is None:
            console.print("No tracked services.")
        else:
            console.print("No tracked processes for service '{0}'.".format(name))
        return
    for item in items:
        alive = bool(item.get("alive"))
        status = "running" if alive else "stopped"
        status_color = "green" if alive else "red"
        status_symbol = "●"
        port = item.get("port")
        port_str = "?" if not port else str(port)
        console.print(
            "[{0}]{1}[/{0}] {2}: PID {3} (port {4}) [[{0}]{5}[/{0}]]".format(
                status_color,
                status_symbol,
                item.get("name"),
                item.get("pid"),
                port_str,
                status,
            ),
            highlight=False,
        )


@svc.command(name="kill")
@click.argument("pid", type=int)
def svc_kill(pid: int) -> None:
    results = svc_core.stop_by_pid(pid)
    if not results:
        click.echo("No tracked process with PID {0}.".format(pid))
        return
    alive = []
    for item in results:
        status = item.get("status")
        name = item.get("name") or "unknown"
        ipid = item.get("pid")
        if status == "terminated":
            click.echo("PID {0} ({1}) terminated.".format(ipid, name))
        elif status == "not_running":
            click.echo("PID {0} ({1}) already not running.".format(ipid, name))
        else:
            click.echo("PID {0} ({1}) could not be terminated.".format(ipid, name), err=True)
            alive.append(item)
    if alive:
        raise click.Abort()
