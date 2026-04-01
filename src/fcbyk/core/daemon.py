import json
import os
import signal
import subprocess
import sys
import time
from typing import Any

import click
from fcbyk.utils import storage


SERVICE_REGISTRY = {
    "lansend": "lansend",
    "pick": "pick",
    "slide": "slide",
}


def _daemon_pid_dir() -> str:
    base = os.path.dirname(storage.get_path("daemon_dummy", subdir="temp"))
    path = os.path.join(base, "daemon")
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path


def _pid_file_path(name: str, pid: int) -> str:
    filename = f"daemon-{name}-{pid}.json"
    return os.path.join(_daemon_pid_dir(), filename)


def _list_pid_files(name: str | None = None) -> list[str]:
    directory = _daemon_pid_dir()
    try:
        filenames = os.listdir(directory)
    except Exception:
        return []
    result = []
    prefix = None
    if name is not None:
        prefix = f"daemon-{name}-"
    for fname in filenames:
        if not fname.endswith(".json"):
            continue
        if prefix is not None and not fname.startswith(prefix):
            continue
        result.append(os.path.join(directory, fname))
    return result


def _read_pid_file(path: str) -> dict[str, Any] | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        pid = data.get("pid")
        name = data.get("name")
        if not isinstance(pid, int) or not isinstance(name, str):
            return None
        return data
    except Exception:
        return None


def _remove_file(path: str) -> None:
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def _process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", f"PID eq {pid}"],
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            ).decode(errors="ignore")
            return str(pid) in out
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _force_terminate(pid: int, timeout: float = 3.0) -> bool:
    if not pid or not _process_exists(pid):
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
    except Exception:
        pass
    return not _process_exists(pid)


def _build_command(name: str, args: list[str]) -> list[str]:
    python_exe = sys.executable
    if sys.platform == "win32":
        try:
            base, exe_name = os.path.split(python_exe)
            if exe_name.lower() == "python.exe":
                pythonw = os.path.join(base, "pythonw.exe")
                if os.path.exists(pythonw):
                    python_exe = pythonw
        except Exception:
            pass
    cmd = [python_exe, "-m", "fcbyk.main", name]
    cmd.extend(args)
    return cmd


def _extract_port_from_argv(argv: list[str], name: str) -> int | None:
    try:
        idx = argv.index(name)
    except ValueError:
        idx = -1
    if idx >= 0:
        args = argv[idx + 1 :]
    else:
        args = list(argv)
    i = 0
    n = len(args)
    while i < n:
        token = args[i]
        if token in ("-p", "--port"):
            if i + 1 < n:
                try:
                    return int(args[i + 1])
                except Exception:
                    pass
            i += 2
            continue
        if token.startswith("--port="):
            val = token.split("=", 1)[1]
            try:
                return int(val)
            except Exception:
                return None
        i += 1
    return None


def start_daemon(name: str, args: list[str]) -> dict[str, Any]:
    if name not in SERVICE_REGISTRY:
        raise ValueError(f"Unknown daemon name: {name}")
    cmd = _build_command(name, list(args))
    log_file = storage.get_path(f"fcbyk_daemon_{name}.log", subdir="log")
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        log_fp = open(log_file, "a", encoding="utf-8")
    except Exception:
        log_fp = None
    try:
        if sys.platform == "win32":
            detached = getattr(subprocess, "DETACHED_PROCESS", 0)
            new_group = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            creationflags = detached | new_group | no_window
            proc = subprocess.Popen(
                cmd,
                creationflags=creationflags,
                stdin=subprocess.DEVNULL,
                stdout=log_fp or subprocess.DEVNULL,
                stderr=log_fp or subprocess.DEVNULL,
                close_fds=False,
            )
        else:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=log_fp or subprocess.DEVNULL,
                stderr=log_fp or subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
            )
    except Exception as e:
        if log_fp:
            try:
                log_fp.flush()
            except Exception:
                pass
        raise RuntimeError(f"failed to start daemon '{name}': {e}")
    pid = proc.pid
    pid_path = _pid_file_path(name, pid)
    port = _extract_port_from_argv(cmd, name)
    data = {
        "name": name,
        "pid": pid,
        "argv": cmd,
        "created_at": time.time(),
        "log_file": log_file,
        "port": port,
    }
    try:
        with open(pid_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass
    return data


def stop_daemon(name: str) -> list[dict[str, Any]]:
    files = _list_pid_files(name)
    results: list[dict[str, Any]] = []
    for path in files:
        info = _read_pid_file(path)
        if not info:
            _remove_file(path)
            continue
        pid = info.get("pid")
        if not isinstance(pid, int):
            _remove_file(path)
            continue
        exists = _process_exists(pid)
        terminated = _force_terminate(pid) if exists else False
        status = "terminated" if terminated else ("not_running" if not exists else "alive")
        if status == "terminated" or status == "not_running":
            _remove_file(path)
        result = {
            "name": info.get("name"),
            "pid": pid,
            "status": status,
            "pid_file": path,
            "log_file": info.get("log_file"),
        }
        results.append(result)
    return results


def status_daemon(name: str) -> list[dict[str, Any]]:
    files = _list_pid_files(name)
    results: list[dict[str, Any]] = []
    for path in files:
        info = _read_pid_file(path)
        if not info:
            _remove_file(path)
            continue
        pid = info.get("pid")
        if not isinstance(pid, int):
            _remove_file(path)
            continue
        alive = _process_exists(pid)
        if not alive:
            _remove_file(path)
        port = info.get("port")
        if port is None:
            argv = info.get("argv") or []
            if isinstance(argv, list):
                port = _extract_port_from_argv(argv, name)
        result = {
            "name": info.get("name"),
            "pid": pid,
            "alive": alive,
            "pid_file": path,
            "log_file": info.get("log_file"),
            "argv": info.get("argv"),
            "created_at": info.get("created_at"),
            "port": port,
        }
        results.append(result)
    return results


def status_all_daemons() -> list[dict[str, Any]]:
    files = _list_pid_files()
    results: list[dict[str, Any]] = []
    for path in files:
        info = _read_pid_file(path)
        if not info:
            _remove_file(path)
            continue
        pid = info.get("pid")
        if not isinstance(pid, int):
            _remove_file(path)
            continue
        alive = _process_exists(pid)
        if not alive:
            _remove_file(path)
        name = info.get("name")
        port = info.get("port")
        if port is None:
            argv = info.get("argv") or []
            if isinstance(argv, list) and isinstance(name, str):
                port = _extract_port_from_argv(argv, name)
        result = {
            "name": info.get("name"),
            "pid": pid,
            "alive": alive,
            "pid_file": path,
            "log_file": info.get("log_file"),
            "argv": info.get("argv"),
            "created_at": info.get("created_at"),
            "port": port,
        }
        results.append(result)
    return results


def stop_by_pid(pid: int) -> list[dict[str, Any]]:
    if pid <= 0:
        return []
    files = _list_pid_files()
    results: list[dict[str, Any]] = []
    for path in files:
        info = _read_pid_file(path)
        if not info:
            _remove_file(path)
            continue
        ipid = info.get("pid")
        if not isinstance(ipid, int):
            _remove_file(path)
            continue
        if ipid != pid:
            continue
        exists = _process_exists(ipid)
        terminated = _force_terminate(ipid) if exists else False
        status = "terminated" if terminated else ("not_running" if not exists else "alive")
        if status == "terminated" or status == "not_running":
            _remove_file(path)
        result = {
            "name": info.get("name"),
            "pid": ipid,
            "status": status,
            "pid_file": path,
            "log_file": info.get("log_file"),
        }
        results.append(result)
    return results


def kill_daemon_callback(ctx: click.Context, param: click.Parameter, value: str | None) -> None:
    if not value or ctx.resilient_parsing:
        return
    
    console = None
    try:
        from rich.console import Console
        console = Console()
    except ImportError:
        pass
    
    if value.lower() == 'all':
        daemons = status_all_daemons()
        if not daemons:
            click.echo("No background daemons running.")
            ctx.exit()
        
        killed_count = 0
        for daemon in daemons:
            pid = daemon.get('pid')
            if pid:
                results = stop_by_pid(pid)
                for result in results:
                    if result.get('status') in ('terminated', 'not_running'):
                        killed_count += 1
        
        click.echo(f"Terminated {killed_count} daemon process(es).")
    else:
        try:
            pid = int(value)
        except ValueError:
            if console:
                console.print(f"[red]Error: Invalid PID '{value}'[/red]")
            else:
                click.echo(f"Error: Invalid PID '{value}'")
            ctx.exit(1)
        
        results = stop_by_pid(pid)
        if not results:
            click.echo(f"No tracked process with PID {pid}.")
        else:
            for item in results:
                status = item.get('status')
                name = item.get('name') or 'unknown'
                ipid = item.get('pid')
                if status == 'terminated':
                    click.echo(f"PID {ipid} ({name}) terminated.")
                elif status == 'not_running':
                    click.echo(f"PID {ipid} ({name}) already not running.")
                else:
                    click.echo(f"PID {ipid} ({name}) could not be terminated.", err=True)
                    ctx.exit(1)
    
    ctx.exit()


def print_daemons() -> None:
    try:
        from rich.console import Console
        
        daemons = status_all_daemons()
        
        if daemons:
            console = Console()
            console.print("[bold]Background Daemons:[/bold]")
            
            for daemon in daemons:
                alive = bool(daemon.get('alive'))
                status = 'running' if alive else 'stopped'
                status_color = 'green' if alive else 'red'
                status_symbol = '●'
                port = daemon.get('port')
                port_str = '?' if not port else str(port)
                
                console.print(
                    f'[{status_color}]{status_symbol}[/{status_color}] {daemon.get("name")}: PID {daemon.get("pid")} (port {port_str}) [[{status_color}]{status}[/{status_color}]]',
                    highlight=False,
                )
            
            console.print()
            console.print("Use 'fcbyk --kill <PID|all>' to stop daemons.")
            console.print()
    except Exception:
        pass
