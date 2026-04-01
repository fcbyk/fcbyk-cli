"""路径管理 API。"""

from __future__ import annotations

from collections.abc import Callable

from fcbykcli.core.context import AppContext

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
    from fcbykcli.core.paths import global_path_items as core_global_path_items
    
    return core_global_path_items(context)
