"""
pick 命令行接口模块

提供随机抽奖功能，支持列表抽奖和文件抽奖两种模式。

常量:
- data_file: 数据文件路径（持久化 items）
- default_data: 默认数据结构（items 列表）

函数:
- delayed_newline_simple(): 延迟打印空行（用于改善控制台输出体验）
- pick(): Click 命令入口，处理所有参数和模式切换
"""

import click

from fcbyk.cli_support.output import show_dict
from fcbyk.cli_support.guard import load_json_object_or_exit, ensure_list_field
from fcbyk.utils import storage

from .service import PickService
from .controller import start_web_server
from fcbyk.utils.port import ensure_port_available

# items 持久化数据文件：~/.fcbyk/data/pick_data.json
data_file = storage.get_path('pick_data.json', subdir='data')

default_data = {
    'items': []
}

# 兑换码持久化数据文件：~/.fcbyk/data/pick_redeem_codes.json
redeem_codes_file = storage.get_path('pick_redeem_codes.json', subdir='data')

default_redeem_codes = {
    'codes': {}
}


def _load_redeem_codes():
    data = storage.load_json(redeem_codes_file, default=default_redeem_codes, create_if_missing=True, strict=False)
    if not isinstance(data, dict):
        return dict(default_redeem_codes)
    codes = data.get('codes')
    if not isinstance(codes, dict):
        data['codes'] = {}
    return data


def _save_redeem_codes(data):
    storage.save_json(redeem_codes_file, data)


@click.command(name='pick', help='Randomly pick one item from the list')
@click.option(
    "--config", "-c",
    is_flag=True,
    callback=lambda ctx, param, value: show_dict(
        ctx,
        param,
        value,
        f"data file: {data_file}",
        ensure_list_field(
            load_json_object_or_exit(
                ctx,
                data_file,
                default=default_data,
                create_if_missing=True,
                label="pick data file",
            ),
            "items",
        ),
    ),
    expose_value=False,
    is_eager=True,
    help="show data and exit"
)
@click.option('--add', '-a', multiple=True, help='Add item to list (can be used multiple times)')
@click.option('--remove', '-r', multiple=True, help='Remove item from list (can be used multiple times)')
@click.option('--clear', is_flag=True, help='Clear the list')
@click.option('--list', '-l', 'show_list', is_flag=True, help='Show current list')
@click.option('--web', '-w', is_flag=True, help='Start web picker server')
@click.option('--port', '-p', default=80, show_default=True, type=int, help='Port for web mode')
@click.option('--no-browser', is_flag=True, help='Do not auto-open browser in web mode')
@click.option('--files','-f', type=click.Path(exists=True, dir_okay=True, file_okay=True, readable=True, resolve_path=True), help='Start web file picker with given file')
@click.option('--gen-codes','-gc', type=int, default=0, show_default=True, help='Generate redeem codes and save to file')
@click.option('--show-codes','-sc', is_flag=True, help='Show saved redeem codes status and exit')
@click.option('--password', '-pw', is_flag=True, default=False, help='Prompt to set admin password (default: 123456 if not set)')
@click.argument('items', nargs=-1)
@click.pass_context
def pick(ctx, add, remove, clear, show_list, web, port, no_browser, files, gen_codes, show_codes, password, items):
    data = ensure_list_field(
        load_json_object_or_exit(
            ctx,
            data_file,
            default=default_data,
            create_if_missing=True,
            label="pick data file",
        ),
        "items",
    )

    service = PickService(data_file, default_data)

    # --gen-codes/--show-codes 可单独运行
    if gen_codes is not None and gen_codes > 0:
        if gen_codes > 100:
            click.echo("Error: --gen-codes max is 100")
            return

        codes_data = _load_redeem_codes()
        codes_map = codes_data.get('codes', {})
        existed = set(codes_map.keys())

        # 生成并追加（尽量去重）
        new_codes = []
        tries = 0
        max_tries = max(100, gen_codes * 20)
        while len(new_codes) < gen_codes and tries < max_tries:
            tries += 1
            c = None
            try:
                c = list(service.generate_redeem_codes(1))[0]
            except Exception:
                c = None
            if not c:
                continue
            if c in existed:
                continue
            existed.add(c)
            new_codes.append(c)
            codes_map[c] = {'used': False}

        codes_data['codes'] = codes_map
        _save_redeem_codes(codes_data)

        click.echo("Generated %d redeem codes." % len(new_codes))
        if show_codes and new_codes:
            click.echo()
            click.echo("New redeem codes:")
            for c in new_codes:
                click.echo("  %s" % c)

        if not files:
            return

    if show_codes and not files:
        codes_data = _load_redeem_codes()
        codes_map = codes_data.get('codes', {})
        total = len(codes_map)
        used = 0
        for _, info in codes_map.items():
            if isinstance(info, dict) and info.get('used'):
                used += 1
        unused = total - used

        click.echo("Redeem codes:")
        click.echo("  Total: %d" % total)
        click.echo("  Unused: %d" % unused)
        click.echo("  Used: %d" % used)

        if total:
            click.echo()
            for c, info in sorted(codes_map.items()):
                st = "USED" if (isinstance(info, dict) and info.get('used')) else "UNUSED"
                click.echo("  %s - %s" % (c, st))
        return

    # 端口占用检测
    if files or web:
        try:
            ensure_port_available(port, host="0.0.0.0")
        except OSError as e:
            click.echo(f" Error: Port {port} is already in use (or you don't have permission). Please choose another port (e.g. --port {int(port) + 1}).")
            click.echo(f" Details: {e}")
            return

    if show_list:
        items_list = data.get('items', [])
        if items_list:
            click.echo("Current items list:")
            for i, item in enumerate(items_list, 1):
                click.echo(f"  {i}. {item}")
        else:
            click.echo("List is empty. Please use --add to add items")
        return

    if clear:
        data['items'] = []
        storage.save_json(data_file, data)
        click.echo("List cleared")
        return

    if add:
        items_list = data.get('items', [])
        for item in add:
            if item not in items_list:
                items_list.append(item)
                click.echo(f"Added: {item}")
            else:
                click.echo(f"Item already exists: {item}")
        data['items'] = items_list
        storage.save_json(data_file, data)
        return

    if remove:
        items_list = data.get('items', [])
        for item in remove:
            if item in items_list:
                items_list.remove(item)
                click.echo(f"Removed: {item}")
            else:
                click.echo(f"Item does not exist: {item}")
        data['items'] = items_list
        storage.save_json(data_file, data)
        return

    if files:
        codes = None
        if gen_codes and gen_codes > 0:
            codes = list(service.generate_redeem_codes(gen_codes))

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

        start_web_server(
            port,
            no_browser,
            files_root=files,
            codes=codes,
            admin_password=admin_password,
        )
        return

    if web:
        start_web_server(port, no_browser)
        return

    # 优先使用命令行参数，否则使用持久化数据文件中的列表
    if items:
        service.pick_item(list(items))
    else:
        items_list = data.get('items', [])
        if not items_list:
            click.echo("Error: No items available")
            click.echo("Usage:")
            click.echo("  1. Use --add to add items: fcbyk pick --add item1 --add item2")
            click.echo("  2. Or provide items directly: fcbyk pick item1 item2 item3")
            return
        service.pick_item(items_list)
