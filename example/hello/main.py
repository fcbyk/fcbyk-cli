from __future__ import annotations

import click

from .cli import hello

def register(cli: click.Group) -> str:
    cli.add_command(hello)
    return "bykcli-hello"
