"""后台守护进程管理模块

提供后台服务的启动、停止、状态查询等功能。
"""
import json
import os
import signal
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

from fcbyk.utils import storage


# 服务注册表
SERVICE_REGISTRY = {
    "lansend": "lansend",
    "pick": "pick",
    "slide": "slide",
}


def _daemon_pid_dir() -> str:
    """获取 PID 文件存储目录"""
    base = os.path.dirname(storage.get_path("daemon_dummy", subdir="temp"))
    path = os.path.join(base, "daemon")
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path


def _pid_file_path(name: str, pid: int) -> str:
    """生成 PID 文件路径"""
    filename = "daemon-{0}-{1}.json".format(name, pid)
    return os.path.join(_daemon_pid_dir(), filename)


def _list_pid_files(name: Optional[str] = None) -> List[str]:
    """列出所有 PID 文件"""
    directory = _daemon_pid_dir()
    try:
        filenames = os.listdir(directory)
    except Exception:
        return []
    result = []
    prefix = None
    if name is not None:
        prefix = "daemon-{0}-".format(name)
    for fname in filenames:
        if not fname.endswith(".json"):
            continue
        if prefix is not None and not fname.startswith(prefix):
            continue
        result.append(os.path.join(directory, fname))
    return result


def _read_pid_file(path: str) -> Optional[Dict[str, Any]]:
    """读取 PID 文件内容"""
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
    """删除文件"""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def _process_exists(pid: int) -> bool:
    """检查进程是否存在"""
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", "PID eq {0}".format(pid)],
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
    """强制终止进程"""
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


def _build_command(name: str, args: List[str]) -> List[str]:
    """构建服务启动命令"""
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
    cmd = [python_exe, "-m", "fcbyk.cli", name]
    cmd.extend(args)
    return cmd


def _extract_port_from_argv(argv: List[str], name: str) -> Optional[int]:
    """从命令行参数中提取端口号"""
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


def start_daemon(name: str, args: List[str]) -> Dict[str, Any]:
    """启动后台守护进程
    
    Args:
        name: 服务名称
        args: 命令行参数列表
        
    Returns:
        包含进程信息的字典
        
    Raises:
        ValueError: 服务名称不存在
        RuntimeError: 启动失败
    """
    if name not in SERVICE_REGISTRY:
        raise ValueError("Unknown daemon name: {0}".format(name))
    cmd = _build_command(name, list(args))
    log_file = storage.get_path("fcbyk_daemon_{0}.log".format(name), subdir="log")
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
        raise RuntimeError("failed to start daemon '{0}': {1}".format(name, e))
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


def stop_daemon(name: str) -> List[Dict[str, Any]]:
    """停止指定服务的所有进程
    
    Args:
        name: 服务名称
        
    Returns:
        处理结果列表
    """
    files = _list_pid_files(name)
    results: List[Dict[str, Any]] = []
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


def status_daemon(name: str) -> List[Dict[str, Any]]:
    """查询指定服务的状态
    
    Args:
        name: 服务名称
        
    Returns:
        服务状态信息列表
    """
    files = _list_pid_files(name)
    results: List[Dict[str, Any]] = []
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


def status_all_daemons() -> List[Dict[str, Any]]:
    """查询所有后台守护进程的状态
    
    Returns:
        所有守护进程状态信息列表
    """
    files = _list_pid_files()
    results: List[Dict[str, Any]] = []
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


def stop_by_pid(pid: int) -> List[Dict[str, Any]]:
    """根据 PID 停止进程
    
    Args:
        pid: 进程 ID
        
    Returns:
        处理结果列表
    """
    if pid <= 0:
        return []
    files = _list_pid_files()
    results: List[Dict[str, Any]] = []
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
