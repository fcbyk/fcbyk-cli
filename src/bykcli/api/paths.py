"""路径展示注册与渲染。"""

from __future__ import annotations

from collections.abc import Callable

from bykcli.core.context import AppContext

PathItem = tuple[str, str]
PathProvider = Callable[[AppContext], list[PathItem]]

_PATH_PROVIDERS: dict[str, PathProvider] = {}


def register_path_provider(command_name: str, provider: PathProvider) -> None:
    """注册子命令路径提供器。"""
    _PATH_PROVIDERS[command_name] = provider


def get_path_provider(command_name: str) -> PathProvider | None:
    """获取某个子命令的路径提供器。"""
    return _PATH_PROVIDERS.get(command_name)


def global_path_items(context: AppContext) -> list[PathItem]:
    """返回默认展示的全局路径。"""
    return [
        ("CLI Home", str(context.paths.root_dir)),
        ("Alias File", str(context.paths.alias_file)),
        ("Logs Directory", str(context.paths.logs_dir)),
    ]
