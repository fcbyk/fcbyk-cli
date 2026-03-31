"""运行时装配。"""

from __future__ import annotations

from fcbykcli import __version__
from fcbykcli.core.context import AppContext
from fcbykcli.core.environment import collect_environment
from fcbykcli.core.persistence import build_path_layout


def build_runtime() -> AppContext:
    """构建应用运行时。"""
    app_name = "fcbyk-cli"
    paths = build_path_layout(app_name=app_name)
    environment = collect_environment(app_name=app_name, version=__version__)
    return AppContext(
        app_name=app_name,
        version=__version__,
        paths=paths,
        environment=environment,
    )
