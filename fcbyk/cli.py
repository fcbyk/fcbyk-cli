#!/usr/bin/env python3
import click
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@click.group()
def cli():
    pass

@cli.command()
@click.option("--name", default="fcbyk", help="Your name")
def hello(name):
    click.echo(f"⚡ Hello, {name}!")

@cli.command()
@click.option("-p", "--port", default=80, help="Port to run the web server on")
def web(port):
    click.echo(f"🌐 Starting web server on port {port}...")
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    cli()
