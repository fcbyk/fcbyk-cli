"""插件发现与注册。"""

from __future__ import annotations

from importlib import import_module
from importlib.metadata import entry_points
import logging
import pkgutil

import click

logger = logging.getLogger("fcbykcli")
plugin_display_info: list[str] = []


def register_builtin_plugins(cli: click.Group, builtin_plugins) -> None:
    """扫描并注册内置插件。"""
    global plugin_display_info
    registered_commands: list[str] = []

    for module in pkgutil.iter_modules(builtin_plugins.__path__):
        target = f"{builtin_plugins.__name__}.{module.name}.command"
        try:
            imported = import_module(target)
        except ModuleNotFoundError:
            continue
        
        register = getattr(imported, "register", None)
        if callable(register):
            register(cli)
            registered_commands.append(module.name)
    
    plugin_display_info.append(f"Builtin ({'、'.join(registered_commands)})")


def register_plugins(cli: click.Group) -> None:
    """加载 entry points 插件。"""
    global plugin_display_info

    try:
        plugin_entries = entry_points(group="fcbyk.plugins")
    except TypeError:
        plugin_entries = entry_points().get("fcbyk.plugins", [])

    for entry in plugin_entries:
        try:
            register = entry.load()
            logger.info("plugin loaded: %s", entry.name)
            # 外部插件注册需返回INFO信息
            plugin_display_info.append(register(cli))
        except Exception as exc:  # noqa: BLE001
            logger.exception("failed to load plugin %s: %s", entry.name, exc)
