import click

import fcbyk.svc as svc_core


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
        click.echo("No running services.")
        return
    click.echo("Current background services:")
    for item in items:
        status = "running" if item.get("alive") else "stopped"
        port = item.get("port")
        port_str = "?" if not port else str(port)
        click.echo(
            "{0}: PID {1} (port {2}) [{3}]".format(
                item.get("name"),
                item.get("pid"),
                port_str,
                status,
            )
        )
    click.echo("Use 'fcbyk svc stop <service>' to stop all processes of a service.")


@svc.command(name="stop")
@click.argument("name")
def svc_stop(name: str) -> None:
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
        click.echo("PID {0} terminated.".format(item.get("pid")))
    for item in not_running:
        click.echo("PID {0} already not running.".format(item.get("pid")))
    for item in alive:
        click.echo("PID {0} could not be terminated.".format(item.get("pid")), err=True)
    if alive:
        raise click.Abort()


@svc.command(name="status")
@click.argument("name", required=False)
def svc_status(name: str = None) -> None:
    if name is None:
        items = svc_core.status_all()
    else:
        if name not in svc_core.SERVICE_REGISTRY:
            click.echo("Error: unknown service '{0}'.".format(name), err=True)
            available = ", ".join(sorted(svc_core.SERVICE_REGISTRY.keys()))
            click.echo("Available services: {0}".format(available), err=True)
            raise click.Abort()
        items = svc_core.status_service(name)
    if not items:
        if name is None:
            click.echo("No tracked services.")
        else:
            click.echo("No tracked processes for service '{0}'.".format(name))
        return
    for item in items:
        status = "running" if item.get("alive") else "stopped"
        port = item.get("port")
        port_str = "?" if not port else str(port)
        click.echo(
            "{0}: PID {1} (port {2}) [{3}]".format(
                item.get("name"),
                item.get("pid"),
                port_str,
                status,
            )
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
