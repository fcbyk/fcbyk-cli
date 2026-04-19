"""别名解析与执行。"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import subprocess
import unicodedata
from typing import Any

import click

from bykcli.core.context import AppContext
from bykcli.core.errors import CliError
from bykcli.infra.persistence import read_json

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
logger = logging.getLogger("bykcli")


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
    
    alias_entries = []
    for path in sorted(collect_alias_paths(aliases)):
        alias = resolve_nested_alias(aliases, path)
        if alias is None:
            continue
        suffix = f" (cwd: {alias.cwd})" if alias.cwd else ""
        alias_entries.append((path, f"{alias.command}{suffix}"))
    
    if not alias_entries:
        return []
    
    max_name_width = max(get_display_width(path) for path, _ in alias_entries)
    
    terminal_width = get_terminal_width()
    separator = "  "
    indent_width = 2
    name_and_separator_width = max_name_width + len(separator)
    max_command_width = terminal_width - indent_width - name_and_separator_width
    
    for path, command in alias_entries:
        padded_name = pad_display_text(path, max_name_width, min_spaces=0)
        full_command = f"{padded_name}{separator}{command}"
        
        if get_display_width(full_command) <= terminal_width - indent_width:
            lines.append(full_command)
        else:
            wrapped_commands = wrap_text(command, max_command_width)
            if wrapped_commands:
                lines.append(f"{padded_name}{separator}{wrapped_commands[0]}")
                for cmd_line in wrapped_commands[1:]:
                    lines.append(f"{' ' * (max_name_width + len(separator))}{cmd_line}")
    
    return lines


def get_display_width(text: str) -> int:
    """计算字符串在终端中的显示宽度，兼容中英文混排。"""
    width = 0
    for char in str(text):
        if unicodedata.combining(char):
            continue
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            width += 2
        else:
            width += 1
    return width


def pad_display_text(text: str, target_width: int, min_spaces: int = 0) -> str:
    """按终端显示宽度补齐字符串后的空格。"""
    display_width = get_display_width(text)
    padding_width = max(0, target_width - display_width) + min_spaces
    return f"{text}{' ' * padding_width}"


def get_terminal_width() -> int:
    """获取终端宽度，如果无法获取则返回默认值 80。"""
    import shutil
    try:
        size = shutil.get_terminal_size()
        return size.columns or 80
    except Exception:
        return 80


def wrap_text(text: str, max_width: int) -> list[str]:
    """将文本按指定宽度换行，保持单词完整性。"""
    if max_width <= 0:
        return [text]
    
    words = text.split()
    if not words:
        return []
    
    lines = []
    current_line = ""
    
    for word in words:
        if not current_line:
            current_line = word
        elif get_display_width(current_line) + 1 + get_display_width(word) <= max_width:
            current_line += " " + word
        else:
            lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines if lines else [""]


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
                    f"Unknown command or alias: {args[0]}\nDid you mean:\n  " + "\n  ".join(suggestions[:5])
                )
            raise click.UsageError(f"Unknown command or alias: {args[0]}")

        final_command = parse_alias_arguments(alias.command, args[1:])
        working_dir = Path(alias.cwd or os.getcwd()).expanduser().resolve()
        if is_dangerous_command(final_command):
            click.secho("Dangerous command detected. Please confirm before execution.", fg="yellow", err=True)
            if not click.confirm("Do you want to continue?", default=False):
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
        raise click.ClickException("Runtime context not yet initialized")

    def invoke(self, ctx: click.Context) -> Any:
        """统一兜底未处理异常"""
        try:
            return super().invoke(ctx)
        except click.ClickException:
            raise
        except click.exceptions.Exit:
            raise
        except CliError as exc:
            logger.warning("cli error: %s", exc)
            raise click.ClickException(str(exc)) from exc
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("unexpected cli error")
            log_file = "log file"
            try:
                if ctx.obj and hasattr(ctx.obj, 'context'):
                    log_file = getattr(ctx.obj.context.paths, 'app_log_file', 'log file')
            except Exception:
                pass
            
            raise click.ClickException(
                f"Unexpected error occurred, see logs at: {log_file}"
            ) from exc
