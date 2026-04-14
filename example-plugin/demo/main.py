from __future__ import annotations

import click

from .hello import hello

def register(cli: click.Group) -> str:
    cli.add_command(hello)
    return "example-plugin (hello)"
