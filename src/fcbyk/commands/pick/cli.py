import click
import fcbyk.svc as svc_core
from fcbyk.cli_support.output import echo_network_urls, copy_to_clipboard
from fcbyk.utils.network import get_private_networks

from fcbyk.cli_support.guard import check_port

from .controller import start_web_server

@click.command(name='pick', help='Start web picker server')
@click.option('--port', '-p', default=80, show_default=True, type=int, help='Port for web mode')
@click.option('--no-browser', is_flag=True, help='Do not auto-open browser in web mode')
@click.option('--files','-f', type=click.Path(exists=True, dir_okay=True, file_okay=True, readable=True, resolve_path=True), help='Start web file picker with given file')
@click.option('--password', '-pw', is_flag=True, default=False, help='Prompt to set admin password (default: 123456 if not set)')
@click.option(
    "--daemon-password",
    "daemon_password",
    help="Admin password for daemon/background mode (normally omit to be prompted)",
    hidden=True
)
@click.option('-D', '--daemon', is_flag=True, help='Run web or file picker server in background')
@click.pass_context
def pick(ctx, port, no_browser, files, password, daemon_password, daemon):


    # 端口占用检测
    if not check_port(port):
        return

    if files:
        if daemon_password:
            effective_password = daemon_password
        elif password:
            effective_password = click.prompt(
                'Admin password (press Enter to use default: 123456)',
                hide_input=True,
                default='123456',
                show_default=False,
            )
            if not effective_password:
                effective_password = '123456'
        else:
            effective_password = '123456'

        if not daemon:
            start_web_server(
                port=port,
                no_browser=no_browser,
                files_root=files,
                admin_password=effective_password,
            )
            return

        args = [
            '--files',
            files,
            '--port',
            str(port),
        ]
        args.append('--no-browser')
        if effective_password:
            args.extend(['--daemon-password', effective_password])
        
        # 输出地址信息（与 lansend/slide 保持一致）
        click.echo()
        private_networks = get_private_networks()
        local_ip = private_networks[0]["ips"][0] if private_networks else "127.0.0.1"
        click.echo(f" Directory: {files}")
        echo_network_urls(private_networks, port, include_virtual=True)
        copy_to_clipboard(f"http://{local_ip}:{port}")
        click.echo()
        
        svc_core.start_service('pick', args)
        return

    # 默认启动普通 Web 抽奖
    if daemon:
        args = ['--port', str(port)]
        args.append('--no-browser')
        
        # 输出地址信息（与 lansend/slide 保持一致）
        click.echo()
        private_networks = get_private_networks()
        local_ip = private_networks[0]["ips"][0] if private_networks else "127.0.0.1"
        echo_network_urls(private_networks, port, include_virtual=True)
        copy_to_clipboard(f"http://{local_ip}:{port}")
        click.echo()
        
        svc_core.start_service('pick', args)
        return

    # 非 daemon 模式下，根据 -pw 参数决定是否设置密码
    if password:
        admin_password = click.prompt(
            'Admin password (press Enter to use default: 123456)',
            hide_input=True,
            default='123456',
            show_default=False,
        )
        if not admin_password:
            admin_password = '123456'
    else:
        admin_password = '123456'
    
    start_web_server(port, no_browser, admin_password=admin_password)
