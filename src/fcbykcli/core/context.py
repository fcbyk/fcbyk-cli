"""CLI 运行时上下文。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from fcbykcli.core.environment import EnvironmentInfo
from fcbykcli.core.persistence import PathLayout

if TYPE_CHECKING:
    from fcbykcli.core.config import ConfigStore
    from fcbykcli.core.state import StateStore


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
    ) -> StateStore:
        """返回某个子命令的状态存储。"""
        raise NotImplementedError

    def shared_store(self, filename: str = "shared-state.json") -> StateStore:
        """返回应用级共享状态存储。"""
        raise NotImplementedError

    def config_store(self) -> ConfigStore:
        """返回应用配置存储。"""
        raise NotImplementedError
