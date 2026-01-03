"""lansend 命令行接口模块
对外提供 lansend / ls 命令。

保持原有参数与行为：
- 支持选择共享目录
- 支持展示局域网访问地址并复制到剪贴板
- 可选提示设置上传密码
- 可选自动打开浏览器
"""

import os
import webbrowser

import click
import pyperclip

from fcbyk.cli_support.output import echo_network_urls
from fcbyk.utils.network import get_private_networks

from .controller import create_lansend_app
from .service import LansendConfig, LansendService


def _lansend_impl(port: int, directory: str, name=None, password: bool = False, no_browser: bool = False, ide: bool = False):
    if not os.path.exists(directory):
        click.echo(f"Error: Directory {directory} does not exist")
        return

    if not os.path.isdir(directory):
        click.echo(f"Error: {directory} is not a directory")
        return

    shared_directory = os.path.abspath(directory)

    config = LansendConfig(
        shared_directory=shared_directory,
        display_name=name or "共享文件夹",
        upload_password=None,
        ide_mode=ide,
    )
    service = LansendService(config)
    config.upload_password = service.pick_upload_password(password, ide, click)

    private_networks = get_private_networks()
    if private_networks:
        local_ip = private_networks[0]["ips"][0]
    else:
        local_ip = "127.0.0.1"
        click.echo(" * Warning: No private network interface found, using localhost")

    click.echo(f" * Directory: {shared_directory}")
    click.echo(f" * Display Name: {config.display_name}")
    if config.upload_password:
        click.echo(" * Upload Password: Enabled")
    echo_network_urls(private_networks, port, include_virtual=True)

    try:
        pyperclip.copy(f"http://{local_ip}:{port}")
        click.echo(" * URL has been copied to clipboard")
    except Exception:
        click.echo(" * Warning: Could not copy URL to clipboard")

    if not no_browser:
        webbrowser.open(f"http://{local_ip}:{port}")

    app = create_lansend_app(service)
    app.run(host="0.0.0.0", port=port)


@click.command(help="Start a local web server for sharing files over LAN")
@click.option("-p", "--port", default=80, help="Web server port (default: 80)")
@click.option("-d", "--directory", default=".", help="Directory to share (default: current directory)")
@click.option("-n", "--name", help="Display name for the page title (default: '共享文件夹')")
@click.option(
    "-pw",
    "--password",
    is_flag=True,
    default=False,
    help="Prompt to set upload password (default: no password, or 123456 if skipped)",
)
@click.option("-nb", "--no-browser", is_flag=True, help="Disable automatic browser opening")
@click.option("--ide/--no-ide", default=True, help="IDE mode: text-share layout (default: on)")
def lansend(port, directory, name, password, no_browser, ide: bool = False):
    _lansend_impl(port, directory, name, password, no_browser, ide)


@click.command(name="ls", help="alias for lansend")
@click.option("-p", "--port", default=80, help="Web server port (default: 80)")
@click.option("-d", "--directory", default=".", help="Directory to share (default: current directory)")
@click.option("-n", "--name", help="Display name for the page title (default: '共享文件夹')")
@click.option(
    "-pw",
    "--password",
    is_flag=True,
    default=False,
    help="Prompt to set upload password (default: no password, or 123456 if skipped)",
)
@click.option("-nb", "--no-browser", is_flag=True, help="Disable automatic browser opening")
@click.option("--ide", is_flag=True, default=False, help="IDE mode: disable upload UI (default: off)")
def ls(port, directory, name, password, no_browser, ide: bool = False):
    _lansend_impl(port, directory, name, password, no_browser, ide)

