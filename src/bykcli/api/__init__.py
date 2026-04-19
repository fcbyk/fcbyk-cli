"""面向子命令和插件的公开运行时 API。"""

from bykcli.api.context import CommandContext, pass_command_context, get_command_context
from bykcli.api.paths import (
    PathItem,
    PathProvider,
    register_path_provider,
    get_path_provider,
    global_path_items,
)

from bykcli.api.network import (
    get_private_networks,
    ensure_port_available,
    detect_iface_type,
)

from bykcli.core.state import StateStore
from bykcli.infra.daemon import start_daemon

__all__ = [
    # 上下文
    "CommandContext",
    "pass_command_context",
    "get_command_context",
    # 路径管理
    "PathItem",
    "PathProvider",
    "register_path_provider",
    "get_path_provider",
    "global_path_items",
    # 网络工具
    "get_private_networks",
    "ensure_port_available",
    "detect_iface_type",
    # 状态存储
    "StateStore",
    # 守护进程
    "start_daemon",
]
