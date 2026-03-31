"""Web 服务共享运行时。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fcbykcli.core.context import AppContext


@dataclass(slots=True)
class WebServiceSpec:
    """Web 服务描述。"""

    name: str
    host: str
    port: int
    static_dir: Path | None = None


def build_web_workspace(context: AppContext, service_name: str) -> Path:
    """返回某个 Web 服务的运行目录。"""
    return context.paths.command_dir(service_name) / "web"
