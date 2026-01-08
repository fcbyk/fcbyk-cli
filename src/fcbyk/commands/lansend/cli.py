"""
lansend 命令行接口模块

对外提供 lansend 命令，用于在局域网内共享文件。

函数:
- lansend(): Click 命令入口，提供完整参数选项
"""

import os
import webbrowser

import click
import pyperclip

from fcbyk.cli_support.output import echo_network_urls, show_dict
from fcbyk.utils import storage
from fcbyk.utils.network import get_private_networks
from fcbyk.utils.port import ensure_port_available

from .controller import create_lansend_app
from .service import LansendConfig, LansendService


def _show_lansend_config(ctx: click.Context, param, value: bool) -> None:
    if not value:
        return

    try:
        data = storage.load_section("fcbyk_config.json", "lansend", default={})
    except Exception:
        data = {}

    if not isinstance(data, dict):
        data = {}

    show_dict(ctx, param, True, "fcbyk_config.json:lansend", data)


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
@click.option(
    "--show-config",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_show_lansend_config,
    help="Show saved config and exit",
)
@click.option("--last", is_flag=True, default=False, help="Reuse last saved config")
@click.option("--save", is_flag=True, default=False, help="Save current args to config")
def lansend(
    port: int,
    directory: str,
    password: bool = False,
    no_browser: bool = False,
    un_download: bool = False,
    un_upload: bool = False,
    chat: bool = False,
    last: bool = False,
    save: bool = False,
):
    # --last: 完全复用持久化配置（忽略其它参数）
    if last:
        try:
            cfg = storage.load_section("fcbyk_config.json", "lansend", default=None)
        except Exception:
            cfg = None

        if not isinstance(cfg, dict):
            click.echo("Error: No saved lansend config found. Use --save first.")
            return

        directory = str(cfg.get("shared_directory") or ".")
        try:
            port = int(cfg.get("port") or 80)
        except Exception:
            port = 80

        password = bool(cfg.get("password_flag") or False)
        no_browser = bool(cfg.get("no_browser") or False)
        un_download = bool(cfg.get("un_download") or False)
        un_upload = bool(cfg.get("un_upload") or False)
        chat = bool(cfg.get("chat") or False)

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
    if private_networks:
        local_ip = private_networks[0]["ips"][0]
    else:
        local_ip = "127.0.0.1"
        click.echo(" * Warning: No private network interface found, using localhost")

    try:
        ensure_port_available(port, host="0.0.0.0")
    except OSError as e:
        click.echo(
            f" Error: Port {port} is already in use (or you don't have permission). "
            f" Please choose another port (e.g. --port {int(port) + 1})."
        )
        click.echo(f" Details: {e}")
        return

    click.echo(f" Directory: {shared_directory}")
    if config.upload_password:
        click.echo(" Upload Password: Enabled")
    echo_network_urls(private_networks, port, include_virtual=True)

    try:
        pyperclip.copy(f"http://{local_ip}:{port}")
        click.echo(" URL has been copied to clipboard")
    except Exception:
        click.echo(" Warning: Could not copy URL to clipboard")

    if save:
        try:
            storage.save_section(
                "fcbyk_config.json",
                "lansend",
                {
                    "shared_directory": shared_directory,
                    "port": str(port),
                    "password_flag": bool(password),
                    "no_browser": bool(no_browser),
                    "un_download": bool(un_download),
                    "un_upload": bool(un_upload),
                    "chat": bool(chat),
                },
            )
        except Exception:
            pass

    if not no_browser:
        webbrowser.open(f"http://{local_ip}:{port}")
    click.echo()
    app = create_lansend_app(service)
    from waitress import serve

    # waitress 线程数：按机器性能自适应，避免老机器被过多线程拖慢
    cpu = os.cpu_count() or 2
    threads = min(16, max(4, cpu * 2))

    serve(
        app,
        host="0.0.0.0",
        port=port,
        max_request_body_size=50 * 1024 * 1024 * 1024,
        threads=threads,
    )
