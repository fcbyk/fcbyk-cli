import click
import threading
import time
from fcbyk.utils.config import get_config_path, load_json_config, save_config
from fcbyk.cli_support.output import show_config
from .service import PickService
from .controller import start_web_server

config_file = get_config_path('fcbyk', 'pick.json')

default_config = {
    'items': []
}


def delayed_newline_simple():
    """延迟打印空行"""
    time.sleep(2)
    click.echo()


@click.command(name='pick', help='Randomly pick one item from the list')
@click.option(
    "--config", "-c",
    is_flag=True,
    callback=lambda ctx, param, value: show_config(
        ctx, param, value, config_file, default_config
    ),
    expose_value=False,
    is_eager=True,
    help="show configuration and exit"
)
@click.option('--add', '-a', multiple=True, help='Add item to list (can be used multiple times)')
@click.option('--remove', '-r', multiple=True, help='Remove item from list (can be used multiple times)')
@click.option('--clear', is_flag=True, help='Clear the list')
@click.option('--list', '-l', 'show_list', is_flag=True, help='Show current list')
@click.option('--web', '-w', is_flag=True, help='Start web picker server')
@click.option('--port', '-p', default=80, show_default=True, type=int, help='Port for web mode')
@click.option('--no-browser', is_flag=True, help='Do not auto-open browser in web mode')
@click.option('--files','-f', type=click.Path(exists=True, dir_okay=True, file_okay=True, readable=True, resolve_path=True), help='Start web file picker with given file')
@click.option('--gen-codes','-gc', type=int, default=5, show_default=True, help='Generate redeem codes for web file picker (only with --files)')
@click.option('--show-codes','-sc', is_flag=True, help='Show the redeem codes in console (only with --files)')
@click.option('--password', '-pw', is_flag=True, default=False, help='Prompt to set admin password (default: 123456 if not set)')
@click.argument('items', nargs=-1)
@click.pass_context
def pick(ctx, add, remove, clear, show_list, web, port, no_browser, files, gen_codes, show_codes, password, items):
    config = load_json_config(config_file, default_config)
    service = PickService(config_file, default_config)
    
    # 显示配置
    if show_list:
        items_list = config.get('items', [])
        if items_list:
            click.echo("Current items list:")
            for i, item in enumerate(items_list, 1):
                click.echo(f"  {i}. {item}")
        else:
            click.echo("List is empty. Please use --add to add items")
        return
    
    # 清空列表
    if clear:
        config['items'] = []
        save_config(config, config_file)
        click.echo("List cleared")
        return
    
    # 添加元素
    if add:
        items_list = config.get('items', [])
        for item in add:
            if item not in items_list:
                items_list.append(item)
                click.echo(f"Added: {item}")
            else:
                click.echo(f"Item already exists: {item}")
        config['items'] = items_list
        save_config(config, config_file)
        return
    
    # 移除元素
    if remove:
        items_list = config.get('items', [])
        for item in remove:
            if item in items_list:
                items_list.remove(item)
                click.echo(f"Removed: {item}")
            else:
                click.echo(f"Item does not exist: {item}")
        config['items'] = items_list
        save_config(config, config_file)
        return
    
    # 文件抽奖模式（优先）
    if files:
        codes = None
        if gen_codes and gen_codes > 0:
            codes = list(service.generate_redeem_codes(gen_codes))
            if show_codes:
                click.echo()
                click.echo("Generated redeem codes (each can be used once):")
                for c in codes:
                    click.echo(f"  {c}")

        if password:
            admin_password = click.prompt('Admin password (press Enter to use default: 123456)', hide_input=True, default='123456', show_default=False)
            admin_password = admin_password if admin_password else '123456'
        else:
            admin_password = '123456'

        # 在启动Web服务器前，先启动延迟任务线程
        delay_thread = threading.Thread(target=delayed_newline_simple, daemon=True)
        delay_thread.start()

        start_web_server(port, no_browser, files_root=files, codes=codes, admin_password=admin_password)
        return

    # Web 抽奖模式
    if web:
        start_web_server(port, no_browser)
        return
    
    # 执行抽奖
    # 如果命令行提供了参数，使用命令行参数；否则使用配置文件中的列表
    if items:
        service.pick_item(list(items))
    else:
        items_list = config.get('items', [])
        if not items_list:
            click.echo("Error: No items available")
            click.echo("Usage:")
            click.echo("  1. Use --add to add items: fcbyk pick --add item1 --add item2")
            click.echo("  2. Or provide items directly: fcbyk pick item1 item2 item3")
            return
        service.pick_item(items_list)