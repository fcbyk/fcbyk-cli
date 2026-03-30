"""
slide 命令行接口模块
提供 PPT 远程控制的 CLI 命令
"""
import click
from fcbyk.core import start_daemon

from fcbyk.utils.network import get_private_networks
from fcbyk.cli_support.guard import check_port

from .service import SlideService
from .controller import create_slide_app
from fcbyk.cli_support.output import echo_network_urls, copy_to_clipboard


@click.command(name="slide", help="Start PPT remote control server, control slides via mobile web page")
@click.option(
    "-p",
    "--port",
    default=80,
    help="Web server port (default: 80)",
)
@click.option(
    "-D",
    "--daemon",
    is_flag=True,
    help="Run server in background after setup",
)
@click.option(
    "--daemon-password",
    "password",
    help="Access password for daemon/background mode (normally omit to be prompted)",
    hidden=True
)
def slide(port, daemon, password):
    """启动 PPT 远程控制服务器"""

    if not password:
        while True:
            password = click.prompt(
                "Please set access password",
                hide_input=True,
                confirmation_prompt=True,
            )
            if password:
                break
            click.echo(" Error: Password cannot be empty")

    # 端口占用检测
    if not check_port(port):
        return

    click.echo()

    # 创建服务
    service = SlideService(password)

    # 创建 Flask 应用和 SocketIO
    app, socketio = create_slide_app(service)
    
    # 获取网络信息
    private_networks = get_private_networks()
    local_ip = private_networks[0]["ips"][0]
        
    # 显示启动信息
    click.echo(f" PPT Remote Control Server")
    echo_network_urls(private_networks, port, include_virtual=True)
    click.echo(f" Open the URL above on your mobile device to control")

    # 复制 URL 到剪贴板
    copy_to_clipboard(f"http://{local_ip}:{port}")
    
    click.echo()

    if not daemon:
        socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
        return

    args = ["--port", str(port), "--daemon-password", password]
    start_daemon("slide", args)
