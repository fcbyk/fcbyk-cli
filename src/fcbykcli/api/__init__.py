"""面向子命令和插件的公开运行时 API。"""

from fcbykcli.api.context import CommandContext, pass_command_context
from fcbykcli.api.paths import (
    PathItem,
    PathProvider,
    register_path_provider,
    get_path_provider,
    global_path_items,
)
from fcbykcli.api.files import (
    get_files_metadata,
    format_size,
    safe_filename,
    is_image_file,
    is_video_file,
)
from fcbykcli.api.network import (
    get_private_networks,
    ensure_port_available,
    detect_iface_type,
)
from fcbykcli.api.response import success, error
from fcbykcli.api.web import create_spa
from fcbykcli.core.state import StateStore

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
    # 文件处理
    "get_files_metadata",
    "format_size",
    "safe_filename",
    "is_image_file",
    "is_video_file",
    # 网络工具
    "get_private_networks",
    "ensure_port_available",
    "detect_iface_type",
    # Web 响应
    "success",
    "error",
    # Web 应用创建
    "create_spa",
    # 状态存储
    "StateStore",
]
