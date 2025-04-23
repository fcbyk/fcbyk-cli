#!/usr/bin/env python3
import click
import logging
import importlib.metadata
import sys

# 禁用 Flask 的日志
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from .commands import lansend

def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    version = importlib.metadata.version("fcbyk-cli")
    click.echo(f"v{version}")
    ctx.exit()

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--version', '-v', is_flag=True, callback=print_version, expose_value=False, is_eager=True, help='Show version and exit.')
def cli():
    pass

cli.add_command(lansend)

if __name__ == "__main__":
    cli()
