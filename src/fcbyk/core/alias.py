import click
import subprocess
import re
import os
from typing import Any
from pathlib import Path

try:
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .json_storage import JsonFileStorage, JsonStorage
from fcbyk import __version__


GLOBAL_ALIAS_FILE = "alias.byk.json"
LOCAL_ALIAS_FILES = ["alias.byk.json", "script.byk.json"]
DANGEROUS_PATTERNS: list[str] = [
    r'rm\s+-[^ ]*[rf]',
    r'git\s+push\s+.*(-f|--force)',
    r'shutdown',
    r'reboot',
    r'format\s+[a-zA-Z]:',
    r'rd\s+/[sq]',
    r'del\s+/[sq]',
    r'>\s*/dev/sd',
]


class AliasStorage:
    
    def __init__(self):
        self._global_storage: JsonFileStorage | None = None
    
    @property
    def global_storage(self) -> JsonFileStorage:
        if self._global_storage is None:
            self._global_storage = JsonFileStorage(GLOBAL_ALIAS_FILE)
        return self._global_storage
    
    def load(self, merge_local: bool = False) -> dict[str, Any]:
        aliases = self.global_storage.load()
        
        if not isinstance(aliases, dict):
            aliases = {}
        
        if merge_local:
            aliases = self._merge_local_aliases(aliases)
        
        return aliases
    
    def _merge_local_aliases(self, global_aliases: dict[str, Any]) -> dict[str, Any]:
        merged = global_aliases.copy()
        
        for local_filename in LOCAL_ALIAS_FILES:
            local_path = Path.cwd() / local_filename
            if local_path.exists():
                try:
                    local_storage = JsonFileStorage(
                        filename=local_filename,
                        app_name="",
                        subdir=None
                    )
                    local_storage.path = str(local_path)
                    local_aliases = local_storage.load()
                    
                    if local_aliases and isinstance(local_aliases, dict):
                        merged.update(local_aliases)
                except Exception as e:
                    click.secho(
                        f"Warning: Failed to load local {local_filename}: {e}",
                        fg="yellow",
                        err=True
                    )
        
        return merged


_alias_storage = AliasStorage()



def load_aliases(merge_local: bool = False) -> dict[str, Any]:
    return _alias_storage.load(merge_local)



def is_dangerous(command: str) -> bool:
    return any(
        re.search(pattern, command, re.IGNORECASE)
        for pattern in DANGEROUS_PATTERNS
    )



def resolve_nested_alias(
    aliases: dict[str, Any],
    path: str
) -> tuple[str | None, str | None]:
    parts = path.split('.')
    current: Any = aliases
    
    for i, part in enumerate(parts):
        if not isinstance(current, dict) or part not in current:
            return None, None
        
        current = current[part]
        
        if i < len(parts) - 1 and not isinstance(current, dict):
            return None, None
    
    match current:
        case str():
            return current, None
        case dict():
            cmd_str = current.get('cmd', '')
            saved_cwd = current.get('cwd')
            return (cmd_str, saved_cwd) if cmd_str else (None, None)
        case _:
            return None, None



def collect_all_alias_paths(aliases: dict[str, Any], prefix: str = '') -> list[str]:
    if not isinstance(aliases, dict):
        return []
    
    paths: list[str] = []
    
    for key, value in aliases.items():
        current_path = f"{prefix}.{key}" if prefix else key
        
        match value:
            case str():
                paths.append(current_path)
            case dict():
                if 'cmd' in value:
                    paths.append(current_path)
                else:
                    paths.extend(collect_all_alias_paths(value, current_path))
    
    return paths



def parse_arguments(cmd_str: str, args: list[str]) -> str:
    if '{args}' in cmd_str:
        all_args = ' '.join(args)
        return cmd_str.replace('{args}', all_args)
    
    placeholders = re.findall(r'\{(\d+)\}', cmd_str)
    
    if not placeholders:
        return f"{cmd_str} {' '.join(args)}" if args else cmd_str
    
    for placeholder in placeholders:
        index = int(placeholder)
        if index < len(args):
            cmd_str = cmd_str.replace('{%s}' % placeholder, args[index])
        else:
            raise ValueError(f"Missing argument for placeholder {{{placeholder}}}")
    
    return cmd_str


class AliasedGroup(click.Group):

    def resolve_command(self, ctx: click.Context, args: list[str]) -> tuple[Any, list[str]]:
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError:
            pass

        if not args:
            return super().resolve_command(ctx, args)

        cmd_name = args[0]
        aliases = load_aliases(merge_local=True)
        cmd_str, saved_cwd = resolve_nested_alias(aliases, cmd_name)
        
        if not cmd_str:
            return self._raise_unknown_alias(cmd_name, aliases)
        
        return self._execute_alias(ctx, cmd_name, cmd_str, saved_cwd, args[1:])
    
    def _execute_alias(
        self,
        ctx: click.Context,
        cmd_name: str,
        cmd_str: str,
        saved_cwd: str | None,
        args: list[str]
    ) -> tuple[Any, list[str]]:
        try:
            final_cmd = parse_arguments(cmd_str, args)
        except ValueError as e:
            raise click.UsageError(str(e)) from e
        
        cli_cwd = ctx.params.get('cwd')
        target_cwd = cli_cwd if cli_cwd else saved_cwd
        actual_cwd = os.path.abspath(target_cwd) if target_cwd else os.getcwd()
        
        if is_dangerous(final_cmd):
            self._handle_dangerous_command(final_cmd)
        
        self._show_execution_info(cmd_name, final_cmd, actual_cwd)
        
        try:
            subprocess.run(final_cmd, shell=True, cwd=actual_cwd, check=False)
        except Exception as e:
            click.secho(f"Error executing command: {e}", fg="red", err=True)
        
        raise SystemExit(0)
    
    def _handle_dangerous_command(self, command: str) -> None:
        click.secho("\n[WARNING] DANGEROUS COMMAND DETECTED!", fg="red", bold=True)
        click.secho(f"Command: {command}", fg="red")
        
        if not click.confirm(
            "This command contains potentially harmful operations. "
            "Are you sure you want to execute it?",
            default=False
        ):
            click.echo("Execution aborted.")
            raise SystemExit(1)
    
    def _show_execution_info(
        self,
        cmd_name: str,
        command: str,
        cwd: str
    ) -> None:
        click.echo()
        click.echo(f"fcbyk-cli v{__version__} {cmd_name}")
        click.echo(f"Running in {cwd}")
        
        if RICH_AVAILABLE:
            console = Console()
            console.print(f"Running: [bold green]{command}[/bold green]")
        else:
            click.echo(f"Running: {command}")
        click.echo()
    
    def _raise_unknown_alias(
        self,
        cmd_name: str,
        aliases: dict[str, Any]
    ) -> tuple[Any, list[str]]:
        all_paths = collect_all_alias_paths(aliases)
        
        if all_paths:
            similar = [
                p for p in all_paths
                if p.startswith(cmd_name + '.') or cmd_name.startswith(p + '.')
            ]
            if similar:
                raise click.UsageError(
                    f"Unknown alias '{cmd_name}'.\n"
                    f"Did you mean one of these?\n"
                    f"  " + "\n  ".join(similar[:5])
                )
        
        raise click.UsageError(f"Unknown alias '{cmd_name}'")
