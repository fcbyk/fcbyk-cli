"""应用配置存储的 JSON 文件实现。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bykcli.core.config import ConfigStore
from bykcli.infra.persistence import read_json, write_json


class JsonFileConfigStore:
    """基于 JSON 文件的配置存储实现。"""

    def __init__(self, config_file: Path) -> None:
        self.config_file = config_file

    def load(self) -> dict[str, Any]:
        """读取完整应用配置。"""
        data = read_json(self.config_file, default={})
        return data if isinstance(data, dict) else {}

    def save(self, data: dict[str, Any]) -> None:
        """覆盖保存应用配置。"""
        write_json(self.config_file, data)

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
