"""
lansend 命令行接口模块
"""

import os, webbrowser, click
from fcbyk.core import start_daemon
from fcbyk.cli_support.output import echo_network_urls, copy_to_clipboard
from fcbyk.cli_support.guard import check_port
from fcbyk.utils.network import get_private_networks
from .controller import start_web_server
from .service import LansendConfig, LansendService


@click.command(help="Start a local web server for sharing files over LAN")
@click.option("-p", "--port", default=80, help="Web server port (default: 80)")
@click.option("-d", "--directory", default=".", help="Directory to share (default: current directory)")
@click.option(
    "-ap",
    "--ask-password",
    is_flag=True,
    default=False,
    help="Prompt to set upload password (default: 123456 if confirmed)",
)
@click.option("-nb", "--no-browser", is_flag=True, help="Disable automatic browser opening")
@click.option("-nd", "--hide-download", is_flag=True, default=False, help="Hide download buttons in directory tab")
@click.option("-nu", "--disable-upload", is_flag=True, default=False, help="Disable upload functionality")
@click.option("--chat", is_flag=True, default=False, help="Enable chat functionality")
@click.option("-D", "--daemon", is_flag=True, help="Run server in background after setup")
@click.option(
    "--daemon-password",
    "daemon_password",
    help="Upload password for daemon/background mode (normally omit to be prompted)",
    hidden=True
)
def lansend(
    port: int,
    directory: str,
    ask_password: bool = False,
    no_browser: bool = False,
    hide_download: bool = False,
    disable_upload: bool = False,
    chat: bool = False,
    daemon: bool = False,
    daemon_password=None,
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
        un_download=hide_download,
        un_upload=disable_upload,
        chat_enabled=chat,
    )
    service = LansendService(config)
    if daemon_password:
        config.upload_password = daemon_password
    else:
        config.upload_password = service.pick_upload_password(ask_password, disable_upload, click)
    
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

    if not daemon:
        start_web_server(port, service)
        return

    args = ["-p", str(port), "-d", shared_directory]
    if hide_download:
        args.append("--hide-download")
    if disable_upload:
        args.append("--disable-upload")
    if chat:
        args.append("--chat")
    args.append("--no-browser")
    if config.upload_password:
        args.extend(["--daemon-password", config.upload_password])
    start_daemon("lansend", args)
