import os
import webbrowser
import click
from typing import List, Dict
from fcbykcli.api import (
    get_private_networks,
    ensure_port_available,
    start_daemon,
    get_command_context
)
from .controller import start_web_server
from .service import LansendConfig, LansendService


def _echo_network_urls(networks: List[Dict], port: int, include_virtual: bool = False) -> None:
    """打印可访问的本地和局域网 URL。"""
    # 本地访问地址
    for host in ["localhost", "127.0.0.1"]:
        click.echo(f"{click.style(' Local', fg=None)}: {click.style(f'http://{host}:{port}', fg='cyan')}")

    # 局域网访问
    for net in networks:
        if net['virtual'] and not include_virtual:
            continue  # 跳过虚拟网卡

        for ip in net["ips"]:
            # 排除回环地址，避免与前面的本地地址重复
            if ip == "127.0.0.1":
                continue
            click.echo(f"{click.style(f' [{net["iface"]}] Network URL:', fg=None)}: {click.style(f'http://{ip}:{port}', fg='cyan')}")


def _copy_to_clipboard(text: str, label: str = "URL", output_prefix: str = " ", silent: bool = False) -> None:
    """将文本复制到剪贴板。"""
    try:
        import pyperclip
        pyperclip.copy(text)
        if not silent:
            click.echo(f"{output_prefix}{label} has been copied to clipboard")
    except Exception:
        if not silent:
            click.echo(f"{output_prefix}Warning: Could not copy {label} to clipboard")


def _check_port(port: int) -> bool:
    """检查端口是否可用。"""
    try:
        ensure_port_available(port)
        return True
    except OSError:
        click.echo(f"Error: Port {port} is already in use")
        return False


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

    if not _check_port(port):
        return

    click.echo(f" Directory: {shared_directory}")
    if config.upload_password:
        click.echo(" Upload Password: Enabled")
    _echo_network_urls(private_networks, port, include_virtual=True)
    _copy_to_clipboard(f"http://{local_ip}:{port}")

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
    
    context = get_command_context()
    start_daemon(context, "lansend", args)

def register(cli: click.Group) -> None:
    """注册命令。"""
    cli.add_command(lansend)