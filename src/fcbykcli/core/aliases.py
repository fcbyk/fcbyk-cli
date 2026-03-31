"""别名解析与执行。"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import subprocess
from typing import Any

import click

from fcbykcli.core.context import AppContext
from fcbykcli.core.errors import CliError
from fcbykcli.core.persistence import read_json

LOCAL_ALIAS_FILES = ("alias.byk.json", "script.byk.json")
DANGEROUS_PATTERNS = (
    r"rm\s+-[^ ]*[rf]",
    r"git\s+push\s+.*(-f|--force)",
    r"shutdown",
    r"reboot",
    r"format\s+[a-zA-Z]:",
    r"rd\s+/[sq]",
    r"del\s+/[sq]",
    r">\s*/dev/sd",
)
logger = logging.getLogger("fcbykcli")


@dataclass(slots=True)
class AliasDefinition:
    """别名定义。"""

    command: str
    cwd: str | None = None


def load_aliases(context: AppContext, merge_local: bool = True) -> dict[str, Any]:
    """加载全局和本地别名。"""
    aliases = read_json(context.paths.alias_file, default={})
    data = aliases if isinstance(aliases, dict) else {}
    return _merge_local_aliases(data) if merge_local else data


def _merge_local_aliases(aliases: dict[str, Any]) -> dict[str, Any]:
    merged = aliases.copy()
    for filename in LOCAL_ALIAS_FILES:
        local_path = Path.cwd() / filename
        local_data = read_json(local_path, default={})
        if isinstance(local_data, dict):
            merged.update(local_data)
    return merged


def resolve_nested_alias(aliases: dict[str, Any], name: str) -> AliasDefinition | None:
    """解析嵌套别名路径。"""
    current: Any = aliases
    for index, part in enumerate(name.split(".")):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
        if index < len(name.split(".")) - 1 and not isinstance(current, dict):
            return None

    if isinstance(current, str):
        return AliasDefinition(command=current)
    if isinstance(current, dict):
        command = current.get("cmd")
        cwd = current.get("cwd")
        if isinstance(command, str):
            return AliasDefinition(command=command, cwd=cwd if isinstance(cwd, str) else None)
    return None


def collect_alias_paths(aliases: dict[str, Any], prefix: str = "") -> list[str]:
    """收集所有可执行别名路径。"""
    result: list[str] = []
    for key, value in aliases.items():
        current_path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, str):
            result.append(current_path)
            continue
        if isinstance(value, dict):
            if "cmd" in value:
                result.append(current_path)
            else:
                result.extend(collect_alias_paths(value, prefix=current_path))
    return result


def parse_alias_arguments(command: str, args: list[str]) -> str:
    """处理别名占位符。"""
    if "{args}" in command:
        return command.replace("{args}", " ".join(args))

    placeholders = re.findall(r"\{(\d+)\}", command)
    if not placeholders:
        return f"{command} {' '.join(args)}".strip()

    rendered = command
    for placeholder in placeholders:
        index = int(placeholder)
        if index >= len(args):
            raise CliError(f"缺少占位参数: {{{placeholder}}}")
        rendered = rendered.replace(f"{{{placeholder}}}", args[index])
    return rendered


def is_dangerous_command(command: str) -> bool:
    """判断命令是否存在明显风险。"""
    return any(re.search(pattern, command, flags=re.IGNORECASE) for pattern in DANGEROUS_PATTERNS)


def render_alias_lines(context: AppContext) -> list[str]:
    """返回别名展示文本。"""
    aliases = load_aliases(context, merge_local=True)
    lines: list[str] = []
    for path in sorted(collect_alias_paths(aliases)):
        alias = resolve_nested_alias(aliases, path)
        if alias is None:
            continue
        suffix = f" (cwd: {alias.cwd})" if alias.cwd else ""
        lines.append(f"{path} -> {alias.command}{suffix}")
    return lines


class AliasAwareGroup(click.Group):
    """支持别名透传的命令组。"""

    runtime_provider: Any = None

    def resolve_command(
        self,
        ctx: click.Context,
        args: list[str],
    ) -> tuple[str | None, click.Command | None, list[str]]:
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError:
            pass

        if not args:
            return super().resolve_command(ctx, args)

        context = self._get_context(ctx)
        aliases = load_aliases(context, merge_local=True)
        alias = resolve_nested_alias(aliases, args[0])
        if alias is None:
            suggestions = [
                item for item in collect_alias_paths(aliases)
                if item.startswith(f"{args[0]}.") or args[0].startswith(f"{item}.")
            ]
            if suggestions:
                raise click.UsageError(
                    f"未知命令或别名: {args[0]}\n可尝试:\n  " + "\n  ".join(suggestions[:5])
                )
            raise click.UsageError(f"未知命令或别名: {args[0]}")

        final_command = parse_alias_arguments(alias.command, args[1:])
        working_dir = Path(alias.cwd or os.getcwd()).expanduser().resolve()
        if is_dangerous_command(final_command):
            click.secho("检测到高风险命令，请确认后再执行。", fg="yellow", err=True)
            if not click.confirm("是否继续执行？", default=False):
                raise SystemExit(1)

        click.echo(f"{context.app_name} v{context.version} alias: {args[0]}")
        click.echo(f"cwd: {working_dir}")
        click.echo(f"run: {final_command}")
        subprocess.run(final_command, shell=True, cwd=str(working_dir), check=False)
        raise SystemExit(0)

    def _get_context(self, ctx: click.Context) -> AppContext:
        """在命令解析阶段获取运行时上下文。"""
        if ctx.obj is not None:
            return ctx.obj.context
        if callable(self.runtime_provider):
            return self.runtime_provider()
        raise click.ClickException("运行时上下文尚未初始化")

    def invoke(self, ctx: click.Context) -> Any:
        """统一兜底未处理异常。"""
        try:
            return super().invoke(ctx)
        except click.ClickException:
            raise
        except CliError as exc:
            logger.warning("cli error: %s", exc)
            raise click.ClickException(str(exc)) from exc
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("unexpected cli error")
            log_file = getattr(ctx.obj.context.paths, "app_log_file", "日志文件") if ctx.obj else "日志文件"
            raise click.ClickException(f"发生未处理异常，详细日志见: {log_file}") from exc
