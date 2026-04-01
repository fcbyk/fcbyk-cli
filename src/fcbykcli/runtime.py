"""运行时装配。"""

from __future__ import annotations

from fcbykcli import __version__
from fcbykcli.core.context import AppContext
from fcbykcli.core.environment import collect_environment
from fcbykcli.infra.config import JsonFileConfigStore
from fcbykcli.infra.persistence import build_path_layout
from fcbykcli.infra.state import CommandJsonStateStore, JsonFileStateStore


def build_runtime() -> AppContext:
    """构建应用运行时。"""
    app_name = "fcbyk-cli"
    paths = build_path_layout(app_name=app_name)
    environment = collect_environment(app_name=app_name, version=__version__)
    
    # 重写 AppContext 的方法以注入具体实现
    class RuntimeAppContext(AppContext):
        def command_store(self, command_name: str, filename: str = "state.json"):
            return CommandJsonStateStore(
                command_name=command_name,
                path=self.paths.command_file(command_name, filename),
            )
        
        def shared_store(self, filename: str = "shared-state.json"):
            return JsonFileStateStore(path=self.paths.config_dir / filename)
        
        def config_store(self):
            return JsonFileConfigStore(config_file=self.paths.app_config_file)
    
    return RuntimeAppContext(
        app_name=app_name,
        version=__version__,
        paths=paths,
        environment=environment,
    )
