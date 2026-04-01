"""持久化路径布局。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PathLayout:
    """持久化目录布局数据结构。"""

    root_dir: Path
    config_dir: Path
    commands_dir: Path
    logs_dir: Path
    runtime_dir: Path
    app_config_file: Path
    alias_file: Path
    app_log_file: Path
    daemon_dir: Path

    def command_dir(self, command_name: str) -> Path:
        """返回子命令专属目录。"""
        path = self.commands_dir / command_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def command_file(self, command_name: str, *parts: str) -> Path:
        """返回子命令专属文件路径。"""
        target = self.command_dir(command_name)
        for part in parts:
            target = target / part
        target.parent.mkdir(parents=True, exist_ok=True)
        return target
