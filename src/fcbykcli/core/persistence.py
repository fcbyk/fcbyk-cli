"""统一持久化路径与基础文件操作。"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
from typing import Any, TypeVar

from fcbykcli.core.errors import CliError

T = TypeVar("T")

CORE_CONFIG_FILE = "config.byk.json"
ALIAS_FILE = "alias.byk.json"


@dataclass(slots=True)
class PathLayout:
    """持久化目录布局。"""

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


def build_path_layout(app_name: str) -> PathLayout:
    """构建目录布局并确保目录存在。"""
    root_dir = Path.home() / f".{app_name}"
    config_dir = root_dir / "config"
    commands_dir = root_dir / "commands"
    logs_dir = root_dir / "logs"
    runtime_dir = root_dir / "runtime"
    daemon_dir = runtime_dir / "daemon"

    for directory in (root_dir, config_dir, commands_dir, logs_dir, runtime_dir, daemon_dir):
        directory.mkdir(parents=True, exist_ok=True)

    return PathLayout(
        root_dir=root_dir,
        config_dir=config_dir,
        commands_dir=commands_dir,
        logs_dir=logs_dir,
        runtime_dir=runtime_dir,
        app_config_file=config_dir / CORE_CONFIG_FILE,
        alias_file=config_dir / ALIAS_FILE,
        app_log_file=logs_dir / "fcbykcli.log",
        daemon_dir=daemon_dir,
    )


def read_json(path: Path, default: T) -> T:
    """读取 JSON 文件。"""
    if not path.exists():
        return default

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise CliError(f"JSON 文件解析失败: {path}") from exc
    except OSError as exc:
        raise CliError(f"无法读取文件: {path}") from exc

    return data if data is not None else default


def write_json(path: Path, data: Any) -> None:
    """以原子方式写入 JSON 文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            dir=path.parent,
            encoding="utf-8",
        ) as temp_file:
            json.dump(data, temp_file, indent=2, ensure_ascii=False)
            temp_path = Path(temp_file.name)
        temp_path.replace(path)
    except OSError as exc:
        raise CliError(f"无法写入文件: {path}") from exc


def read_text(path: Path, default: str | None = None) -> str | None:
    """读取文本文件。"""
    if not path.exists():
        return default
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CliError(f"无法读取文件: {path}") from exc


def write_text(path: Path, content: str) -> None:
    """以原子方式写入文本文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            dir=path.parent,
            encoding="utf-8",
        ) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)
        temp_path.replace(path)
    except OSError as exc:
        raise CliError(f"无法写入文件: {path}") from exc
