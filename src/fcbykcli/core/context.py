"""CLI 运行时上下文。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from fcbykcli.core.environment import EnvironmentInfo
from fcbykcli.core.persistence import PathLayout

if TYPE_CHECKING:
    from fcbykcli.core.state import CommandStateStore, StateStore


@dataclass(slots=True)
class AppContext:
    """子命令共享的核心上下文。"""

    app_name: str
    version: str
    paths: PathLayout
    environment: EnvironmentInfo

    def command_store(
        self,
        command_name: str,
        filename: str = "state.json",
    ) -> CommandStateStore:
        """返回某个子命令的状态存储。"""
        from fcbykcli.core.state import CommandStateStore

        return CommandStateStore(
            command_name=command_name,
            path=self.paths.command_file(command_name, filename),
        )

    def shared_store(self, filename: str = "shared-state.json") -> StateStore:
        """返回应用级共享状态存储。"""
        from fcbykcli.core.state import StateStore

        return StateStore(path=self.paths.config_dir / filename)
