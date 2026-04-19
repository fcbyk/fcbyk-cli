import os

import click

from fcbyk import defaults
from fcbyk.utils import storage


@click.command(help="Show locations of data, log, config and scripts files.")
def config() -> None:
    """Show key directories and config file paths."""
    config_path = storage.get_path(defaults.CONFIG_FILE)
    data_dir = os.path.dirname(config_path)
    log_dir = os.path.join(data_dir, "log")
    scripts_path = storage.get_path("scripts.byk.json")

    click.echo("数据目录: {}".format(data_dir))
    click.echo("日志目录: {}".format(log_dir))
    click.echo("配置文件: {}".format(config_path))
    click.echo("脚本文件: {}".format(scripts_path))
