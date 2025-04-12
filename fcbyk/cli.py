#!/usr/bin/env python3
import click


@click.command()
@click.option("--name", default="fcbyk", help="Your name")
def hello(name):
    click.echo(f"⚡ Hello, {name}!")


if __name__ == "__main__":
    hello()
