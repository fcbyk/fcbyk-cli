import click
from typing import Any, Dict
from ..utils.config import load_json_config

def colored_key_value(key: str, value: Any, key_color: str = 'cyan', value_color: str = 'yellow') -> str:
    """
    返回格式化后的彩色 key:value 字符串。

    Args:
        key (str): 字段名
        value (Any): 字段值
        key_color (str): key 的颜色
        value_color (str): value 的颜色

    Returns:
        str: 彩色格式化字符串
    """
    return f"{click.style(str(key), fg=key_color)}: {click.style(str(value), fg=value_color)}"


def show_config(
    ctx: click.Context,
    param: Any,
    value: bool,
    config_file_url: str,
    default_config: Dict[str, Any]
) -> None:
    """
    显示指定配置文件内容，并退出 CLI（彩色高亮）。

    输出格式：
        config file: <路径>   （key 青色，value 黄色）
        key: value            （key 青色，value 黄色）

    Args:
        ctx (click.Context): click 上下文对象
        param (Any): click 参数对象
        value (bool): 是否触发显示
        config_file_url (str): 配置文件路径
        default_config (Dict[str, Any]): 默认配置字典
    """
    if not value:
        return

    config = load_json_config(config_file_url, default_config)
    
    click.echo(colored_key_value("config file", config_file_url))

    for key, val in config.items():
        click.echo(colored_key_value(key, val))

    ctx.exit()


def show_dict(
    ctx: click.Context,
    param: Any,
    value: bool,
    title: str,
    data: Dict[str, Any]
) -> None:
    """直接显示一个 dict，并退出 CLI（彩色高亮）。

    用途：
        当配置不再是“单独一个 json 文件”时（例如统一配置文件的某个 section），
        调用方可以先自行拿到 dict，再交给该函数统一打印。

    输出格式：
        <title>: <...>   （key 青色，value 黄色）
        key: value

    Args:
        ctx: click 上下文对象
        param: click 参数对象（占位，保持与 click callback 签名一致）
        value: 是否触发显示
        title: 标题（例如 "config file"、"section"、"ai config"）
        data: 要显示的字典
    """
    if not value:
        return

    click.echo(colored_key_value(title, ""))
    for k, v in data.items():
        click.echo(colored_key_value(k, v))

    ctx.exit()


def echo_network_urls(networks: list, port: int, include_virtual: bool = False):
    """
    打印可访问的本地和局域网 URL，支持彩色高亮。

    Args:
        networks (list[dict]): get_private_networks() 返回的网卡信息列表
        port (int): 端口号
        include_virtual (bool): 是否显示虚拟网卡（如 VMware、Docker）

    输出示例：
        Local: http://localhost:5173
        Local: http://127.0.0.1:5173
        [Ethernet] Network URL: http://192.168.0.101:5173
    """
    # 本地访问地址
    for host in ["localhost", "127.0.0.1"]:
        click.echo(colored_key_value(" Local", f"http://{host}:{port}", key_color=None, value_color="cyan"))

    # 局域网访问
    for net in networks:
        if net['virtual'] and not include_virtual:
            continue  # 跳过虚拟网卡

        for ip in net["ips"]:
            click.echo(colored_key_value(f" [{net['iface']}] Network URL:", f"http://{ip}:{port}", key_color=None, value_color="cyan"))

    