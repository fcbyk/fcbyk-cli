"""后台守护进程管理。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any

import click

from bykcli.core.context import AppContext
from bykcli.runtime import build_runtime


@dataclass(slots=True)
class DaemonRecord:
    """守护进程元数据。"""

    name: str
    pid: int
    argv: list[str]
    created_at: float
    log_file: str
    port: int | None = None


def _daemon_dir(context: AppContext) -> Path:
    context.paths.daemon_dir.mkdir(parents=True, exist_ok=True)
    return context.paths.daemon_dir


def _pid_file(context: AppContext, name: str, pid: int) -> Path:
    return _daemon_dir(context) / f"daemon-{name}-{pid}.json"


def _list_pid_files(context: AppContext, name: str | None = None) -> list[Path]:
    prefix = f"daemon-{name}-" if name else "daemon-"
    return sorted(path for path in _daemon_dir(context).glob(f"{prefix}*.json") if path.is_file())


def _read_record(path: Path) -> DaemonRecord | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(data, dict):
        return None
    if not isinstance(data.get("name"), str) or not isinstance(data.get("pid"), int):
        return None
    argv = data.get("argv")
    if not isinstance(argv, list) or not all(isinstance(item, str) for item in argv):
        argv = []
    return DaemonRecord(
        name=data["name"],
        pid=data["pid"],
        argv=argv,
        created_at=float(data.get("created_at", 0)),
        log_file=str(data.get("log_file", "")),
        port=data.get("port") if isinstance(data.get("port"), int) else None,
    )


def _write_record(path: Path, record: DaemonRecord) -> None:
    path.write_text(
        json.dumps(asdict(record), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            output = subprocess.check_output(
                ["tasklist", "/FI", f"PID eq {pid}"],
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            ).decode(errors="ignore")
            return str(pid) in output
        except Exception:  # noqa: BLE001
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _terminate(pid: int, timeout: float = 3.0) -> bool:
    if not _process_exists(pid):
        return True
    try:
        if sys.platform == "win32":
            subprocess.Popen(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            ).wait(timeout=timeout)
        else:
            os.kill(pid, signal.SIGTERM)
        time.sleep(0.2)
    except Exception:  # noqa: BLE001
        return False
    return not _process_exists(pid)


def _extract_port(argv: list[str]) -> int | None:
    for index, token in enumerate(argv):
        if token in {"-p", "--port"} and index + 1 < len(argv):
            try:
                return int(argv[index + 1])
            except ValueError:
                return None
        if token.startswith("--port="):
            try:
                return int(token.split("=", 1)[1])
            except ValueError:
                return None
    return None


def start_daemon(context: AppContext, name: str, args: list[str]) -> DaemonRecord:
    """启动新的守护进程。"""
    command = [sys.executable, "-m", "bykcli.main", name, *args]
    log_file = context.paths.logs_dir / f"{name}-D.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as log_handle:
        if sys.platform == "win32":
            process = subprocess.Popen(
                command,
                creationflags=(
                    getattr(subprocess, "DETACHED_PROCESS", 0)
                    | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                    | getattr(subprocess, "CREATE_NO_WINDOW", 0)
                ),
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=log_handle,
                close_fds=False,
            )
        else:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=log_handle,
                start_new_session=True,
                close_fds=True,
            )

    record = DaemonRecord(
        name=name,
        pid=process.pid,
        argv=command,
        created_at=time.time(),
        log_file=str(log_file),
        port=_extract_port(command),
    )
    _write_record(_pid_file(context, name, process.pid), record)
    return record


def list_daemons(context: AppContext) -> list[dict[str, Any]]:
    """列出所有已登记守护进程。"""
    results: list[dict[str, Any]] = []
    for path in _list_pid_files(context):
        record = _read_record(path)
        if record is None:
            path.unlink(missing_ok=True)
            continue
        alive = _process_exists(record.pid)
        if not alive:
            path.unlink(missing_ok=True)
        results.append(
            {
                "name": record.name,
                "pid": record.pid,
                "alive": alive,
                "port": record.port,
                "log_file": record.log_file,
            }
        )
    return results


def stop_by_pid(context: AppContext, pid: int) -> list[dict[str, Any]]:
    """按 PID 停止守护进程。"""
    results: list[dict[str, Any]] = []
    for path in _list_pid_files(context):
        record = _read_record(path)
        if record is None:
            path.unlink(missing_ok=True)
            continue
        if record.pid != pid:
            continue
        alive = _process_exists(pid)
        terminated = _terminate(pid) if alive else False
        status = "terminated" if terminated else ("not_running" if not alive else "alive")
        if status in {"terminated", "not_running"}:
            path.unlink(missing_ok=True)
        results.append({"name": record.name, "pid": pid, "status": status})
    return results


def kill_daemon_callback(
    ctx: click.Context,
    _param: click.Parameter,
    value: str | None,
) -> None:
    """Handle global kill option."""
    if not value or ctx.resilient_parsing:
        return

    state = getattr(ctx, "obj", None)
    context = state.context if state else build_runtime()

    if value.lower() == "all":
        daemons = list_daemons(context)
        count = 0
        for daemon in daemons:
            count += sum(
                1
                for item in stop_by_pid(context, int(daemon["pid"]))
                if item["status"] in {"terminated", "not_running"}
            )
        click.echo(f"Processed {count} daemon(s).")
        ctx.exit()

    try:
        pid = int(value)
    except ValueError as exc:
        raise click.BadParameter(f"Invalid PID: {value}") from exc

    results = stop_by_pid(context, pid)
    if not results:
        click.echo(f"No managed process found with PID={pid}.")
        ctx.exit()

    for item in results:
        click.echo(f'{item["name"]}({item["pid"]}) -> {item["status"]}')
    ctx.exit()
