#!/usr/bin/env python3
import click
from fcbyk import commands
from fcbyk.core import (
    AliasedGroup,
    kill_daemon_callback,
    print_daemons
)
from fcbyk.cli import (
    version_callback, 
)
from fcbyk.core.alias import print_aliases


@click.group(
    cls=AliasedGroup,
    context_settings=dict(
        help_option_names=['-h', '--help']
    ),
    invoke_without_command=True
)
@click.option(
    '--version', '-v', 
    is_flag=True, 
    callback=version_callback, 
    expose_value=False, 
    is_eager=True, 
    help='Show version and exit.'
)
@click.option(
    '--kill', '-k',
    type=str,
    callback=kill_daemon_callback,
    expose_value=False,
    is_eager=True,
    help='Kill background daemon processes. Use "all" to kill all or specify PID.',
)
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        click.echo()
        click.echo(ctx.get_help())
        print_aliases()
        print_daemons()


for cmd_name in commands.__all__:
    main.add_command(getattr(commands, cmd_name))


if __name__ == "__main__":
    main()
