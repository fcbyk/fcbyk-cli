import os

import click

from fcbyk import defaults
from fcbyk.utils import storage


@click.command()
def config() -> None:
    config_path = storage.get_path(defaults.CONFIG_FILE)
    data_dir = os.path.dirname(config_path)
    log_dir = os.path.join(data_dir, "log")

    click.echo("数据目录: {}".format(data_dir))
    click.echo("日志目录: {}".format(log_dir))
    click.echo("配置文件: {}".format(config_path))
