#!/usr/bin/env python3
import click
from fcbyk import commands
from fcbyk.core import AliasedGroup
from fcbyk.cli_support import (
    version_callback, 
    print_aliases
)


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
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        click.echo()
        click.echo(ctx.get_help())
        print_aliases()


for cmd_name in commands.__all__:
    main.add_command(getattr(commands, cmd_name))


if __name__ == "__main__":
    main()
