"""
lansend 命令行接口模块 (局域网内共享文件)
"""

import os, webbrowser, click
from fcbyk.cli_support.output import echo_network_urls, copy_to_clipboard
from fcbyk.cli_support.guard import check_port
from fcbyk.utils.network import get_private_networks
from .controller import start_web_server
from .service import LansendConfig, LansendService


@click.command(help="Start a local web server for sharing files over LAN")
@click.option("-p", "--port", default=80, help="Web server port (default: 80)")
@click.option("-d", "--directory", default=".", help="Directory to share (default: current directory)")
@click.option(
    "-pw",
    "--password",
    is_flag=True,
    default=False,
    help="Prompt to set upload password (default: no password, or 123456 if skipped)",
)
@click.option("-nb", "--no-browser", is_flag=True, help="Disable automatic browser opening")
@click.option("-un-d","--un-download", is_flag=True, default=False, help="Hide download buttons in directory tab")
@click.option("-un-up","--un-upload", is_flag=True, default=False, help="Disable upload functionality")
@click.option("--chat", is_flag=True, default=False, help="Enable chat functionality")
def lansend(
    port: int,
    directory: str,
    password: bool = False,
    no_browser: bool = False,
    un_download: bool = False,
    un_upload: bool = False,
    chat: bool = False,
):
    if not os.path.exists(directory):
        click.echo(f"Error: Directory {directory} does not exist")
        return

    if not os.path.isdir(directory):
        click.echo(f"Error: {directory} is not a directory")
        return

    shared_directory = os.path.abspath(directory)

    config = LansendConfig(
        shared_directory=shared_directory,
        upload_password=None,
        un_download=un_download,
        un_upload=un_upload,
        chat_enabled=chat,
    )
    service = LansendService(config)
    config.upload_password = service.pick_upload_password(password, un_upload, click)
    
    click.echo()
    private_networks = get_private_networks()
    local_ip = private_networks[0]["ips"][0]

    if not check_port(port):
        return

    click.echo(f" Directory: {shared_directory}")
    if config.upload_password:
        click.echo(" Upload Password: Enabled")
    echo_network_urls(private_networks, port, include_virtual=True)
    copy_to_clipboard(f"http://{local_ip}:{port}")

    if not no_browser:
        webbrowser.open(f"http://{local_ip}:{port}")
    click.echo()
    start_web_server(port, service)
