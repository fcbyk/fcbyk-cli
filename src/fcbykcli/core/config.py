"""应用配置管理。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fcbykcli.core.context import AppContext
from fcbykcli.core.persistence import read_json, write_json


@dataclass(slots=True)
class AppConfigStore:
    """应用配置读写入口。"""

    context: AppContext

    def load(self) -> dict[str, Any]:
        """读取完整应用配置。"""
        data = read_json(self.context.paths.app_config_file, default={})
        return data if isinstance(data, dict) else {}

    def save(self, data: dict[str, Any]) -> None:
        """覆盖保存应用配置。"""
        write_json(self.context.paths.app_config_file, data)

    def get(self, key: str, default: Any = None) -> Any:
        """读取单个配置项。"""
        return self.load().get(key, default)

    def set(self, key: str, value: Any) -> dict[str, Any]:
        """保存单个配置项。"""
        data = self.load()
        data[key] = value
        self.save(data)
        return data

    def delete(self, key: str) -> dict[str, Any]:
        """删除单个配置项。"""
        data = self.load()
        data.pop(key, None)
        self.save(data)
        return data
