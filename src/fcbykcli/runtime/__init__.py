"""面向子命令和插件的公开运行时 API。"""

from fcbykcli.runtime.context import CommandContext, pass_command_context

__all__ = ["CommandContext", "pass_command_context"]
