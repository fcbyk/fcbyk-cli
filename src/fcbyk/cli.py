#!/usr/bin/env python3
import click
import logging
import sys

# 禁用 Flask 的日志
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from .commands import lansend

def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    
    version = "unknown"
    try:
        # 优先使用现代方法 (Python 3.8+)
        from importlib import metadata
        version = metadata.version("fcbyk-cli")
    except ImportError:
        # 回退到旧方法 (Python 3.6/3.7)
        try:
            import pkg_resources
            version = pkg_resources.get_distribution("fcbyk-cli").version
        except Exception:
            pass
            
    click.echo("v{}".format(version))
    ctx.exit()

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--version', '-v', is_flag=True, callback=print_version, expose_value=False, is_eager=True, help='Show version and exit.')
def cli():
    pass

cli.add_command(lansend)

if __name__ == "__main__":
    cli()
