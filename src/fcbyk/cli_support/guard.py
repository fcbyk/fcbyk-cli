"""CLI guard / 验证工具

这里放置“面向 CLI 的保护性工具函数”，用于：
- 读取用户可编辑的数据文件
- 在文件损坏/格式不对时给出友好错误提示
- 并以一致的方式退出（ctx.exit）

注意：
- 这里可以依赖 click（因为它属于 CLI 边界层）。
- 不要把这类逻辑放到 utils/storage.py（storage 应保持纯 IO，不依赖 click）。
"""

import json
from typing import Any, Dict, Optional

import click

from fcbyk.utils import storage


def load_json_object_or_exit(
    ctx: click.Context,
    path: str,
    *,
    default: Optional[Dict[str, Any]] = None,
    create_if_missing: bool = True,
    label: str = "data file",
) -> Dict[str, Any]:
    """读取一个 JSON 文件并确保顶层为 object(dict)，失败则友好提示并退出。"""
    try:
        data = storage.load_json(
            path,
            default=default,
            create_if_missing=create_if_missing,
            strict=True,
        )
    except json.JSONDecodeError as e:
        click.secho(f"Error: {label} is not valid JSON.", fg="red", err=True)
        click.secho(f"File: {path}", fg="red", err=True)
        click.secho(f"Details: {e}", fg="red", err=True)
        ctx.exit(1)
    except Exception as e:
        click.secho(f"Error: failed to read {label}.", fg="red", err=True)
        click.secho(f"File: {path}", fg="red", err=True)
        click.secho(f"Details: {e}", fg="red", err=True)
        ctx.exit(1)

    if data is None:
        # 只有 default=None 且文件不存在时才可能发生
        click.secho(f"Error: {label} does not exist.", fg="red", err=True)
        click.secho(f"File: {path}", fg="red", err=True)
        ctx.exit(1)

    if not isinstance(data, dict):
        click.secho(f"Error: invalid {label} format. Expected a JSON object.", fg="red", err=True)
        click.secho(f"File: {path}", fg="red", err=True)
        ctx.exit(1)

    return data


def ensure_list_field(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    """确保 data[key] 是 list。

    - 如果 key 不存在，或对应值不是 list，则会设置为空列表 []。
    - 仅修改内存对象，不做写回；是否持久化由调用方决定。

    用途：
        pick 这类数据文件允许用户手改，为避免手改造成字段缺失/类型错误导致命令报错，
        可以在读取后做轻量自愈（不覆盖整个文件）。
    """
    if key not in data or not isinstance(data.get(key), list):
        data[key] = []
    return data
