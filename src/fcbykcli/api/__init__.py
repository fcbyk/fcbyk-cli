"""面向子命令和插件的公开运行时 API。"""

from fcbykcli.api.context import CommandContext, pass_command_context
from fcbykcli.api.paths import (
    PathItem,
    PathProvider,
    register_path_provider,
    get_path_provider,
    global_path_items,
)
from fcbykcli.api.state import CommandStateStore, StateStore

__all__ = [
    # 上下文
    "CommandContext",
    "pass_command_context",
    # 路径管理
    "PathItem",
    "PathProvider",
    "register_path_provider",
    "get_path_provider",
    "global_path_items",
    # 状态存储
    "StateStore",
    "CommandStateStore",
]
