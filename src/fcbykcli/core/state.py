"""子命令状态存储协议。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class StateStore(Protocol):
    """状态存储协议。"""

    path: Path

    def load(self) -> dict[str, Any]: ...
    def save(self, data: dict[str, Any]) -> dict[str, Any]: ...
    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any) -> dict[str, Any]: ...
    def update(self, values: dict[str, Any]) -> dict[str, Any]: ...
    def delete(self, key: str) -> dict[str, Any]: ...
    def clear(self) -> dict[str, Any]: ...


@dataclass(slots=True)
class CommandStateStore(StateStore):
    """带命令元信息的状态存储协议。"""

    command_name: str
