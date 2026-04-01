"""面向子命令的上下文封装。"""

from __future__ import annotations

from dataclasses import dataclass
from functools import update_wrapper
from typing import Any, Callable, TypeVar, cast

import click

from fcbykcli.app import CliState
from fcbykcli.core.context import AppContext
from fcbykcli.core.state import CommandStateStore, StateStore

F = TypeVar("F", bound=Callable[..., Any])


@dataclass(slots=True)
class CommandContext:
    """提供给子命令的便捷上下文。"""

    name: str
    app: AppContext
    state: CommandStateStore
    shared_state: StateStore


def build_command_context(ctx: click.Context) -> CommandContext:
    """根据当前 Click 上下文构建命令上下文。"""
    state = cast(CliState, ctx.obj)
    command_name = ctx.command.name or "unknown"
    return CommandContext(
        name=command_name,
        app=state.context,
        state=state.context.command_store(command_name),
        shared_state=state.context.shared_store(),
    )


def pass_command_context(func: F) -> F:
    """向子命令注入便捷上下文。"""

    @click.pass_context
    def new_func(ctx: click.Context, *args: Any, **kwargs: Any) -> Any:
        return ctx.invoke(func, build_command_context(ctx), *args, **kwargs)

    return cast(F, update_wrapper(new_func, func))
