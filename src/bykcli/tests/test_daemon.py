from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bykcli.infra.daemon import (
    DaemonRecord,
    _daemon_dir,
    _extract_port,
    _list_pid_files,
    _pid_file,
    _process_exists,
    _read_record,
    _terminate,
    _write_record,
    kill_daemon_callback,
    list_daemons,
    start_daemon,
    stop_by_pid,
)


class TestDaemonRecord:
    def test_dataclass_creation(self):
        record = DaemonRecord(
            name="test",
            pid=1234,
            argv=["python", "test.py"],
            created_at=1234567890.0,
            log_file="/tmp/test.log",
            port=8080,
        )
        assert record.name == "test"
        assert record.pid == 1234
        assert record.port == 8080

    def test_dataclass_default_port(self):
        record = DaemonRecord(
            name="test",
            pid=1234,
            argv=["python", "test.py"],
            created_at=1234567890.0,
            log_file="/tmp/test.log",
        )
        assert record.port is None


class TestDaemonDir:
    def test_daemon_dir_creation(self, tmp_path, monkeypatch):
        context = MagicMock()
        context.paths.daemon_dir = tmp_path / "daemon"
        result = _daemon_dir(context)
        assert result == tmp_path / "daemon"
        assert result.exists()


class TestPidFile:
    def test_pid_file_path(self, tmp_path, monkeypatch):
        context = MagicMock()
        context.paths.daemon_dir = tmp_path / "daemon"
        (tmp_path / "daemon").mkdir(parents=True, exist_ok=True)
        result = _pid_file(context, "test", 1234)
        assert result == tmp_path / "daemon" / "daemon-test-1234.json"


class TestListPidFiles:
    def test_list_all_pid_files(self, tmp_path, monkeypatch):
        context = MagicMock()
        context.paths.daemon_dir = tmp_path / "daemon"
        (tmp_path / "daemon").mkdir(parents=True, exist_ok=True)
        (tmp_path / "daemon" / "daemon-test-1234.json").write_text("{}")
        (tmp_path / "daemon" / "daemon-other-5678.json").write_text("{}")
        result = _list_pid_files(context)
        assert len(result) == 2

    def test_list_filtered_by_name(self, tmp_path, monkeypatch):
        context = MagicMock()
        context.paths.daemon_dir = tmp_path / "daemon"
        (tmp_path / "daemon").mkdir(parents=True, exist_ok=True)
        (tmp_path / "daemon" / "daemon-test-1234.json").write_text("{}")
        (tmp_path / "daemon" / "daemon-other-5678.json").write_text("{}")
        result = _list_pid_files(context, name="test")
        assert len(result) == 1
        assert "daemon-test-1234.json" in str(result[0])

    def test_list_ignores_directories(self, tmp_path, monkeypatch):
        context = MagicMock()
        context.paths.daemon_dir = tmp_path / "daemon"
        (tmp_path / "daemon").mkdir(parents=True, exist_ok=True)
        (tmp_path / "daemon" / "daemon-test-1234.json").write_text("{}")
        (tmp_path / "daemon" / "not-a-file").mkdir()
        result = _list_pid_files(context)
        assert len(result) == 1


class TestReadRecord:
    def test_read_valid_record(self, tmp_path):
        path = tmp_path / "test.json"
        record_data = {
            "name": "test",
            "pid": 1234,
            "argv": ["python", "test.py"],
            "created_at": 1234567890.0,
            "log_file": "/tmp/test.log",
            "port": 8080,
        }
        path.write_text(json.dumps(record_data))
        result = _read_record(path)
        assert result is not None
        assert result.name == "test"
        assert result.pid == 1234
        assert result.port == 8080

    def test_read_invalid_json(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text("not valid json")
        result = _read_record(path)
        assert result is None

    def test_read_not_dict(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text("[1, 2, 3]")
        result = _read_record(path)
        assert result is None

    def test_read_missing_name(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text(json.dumps({"pid": 1234}))
        result = _read_record(path)
        assert result is None

    def test_read_missing_pid(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text(json.dumps({"name": "test"}))
        result = _read_record(path)
        assert result is None

    def test_read_invalid_name_type(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text(json.dumps({"name": 123, "pid": 1234}))
        result = _read_record(path)
        assert result is None

    def test_read_invalid_pid_type(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text(json.dumps({"name": "test", "pid": "1234"}))
        result = _read_record(path)
        assert result is None

    def test_read_invalid_argv_type(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text(json.dumps({"name": "test", "pid": 1234, "argv": "not-list"}))
        result = _read_record(path)
        assert result is not None
        assert result.argv == []

    def test_read_argv_with_non_string_items(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text(json.dumps({"name": "test", "pid": 1234, "argv": [1, 2, 3]}))
        result = _read_record(path)
        assert result is not None
        assert result.argv == []

    def test_read_default_values(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text(json.dumps({"name": "test", "pid": 1234}))
        result = _read_record(path)
        assert result.created_at == 0.0
        assert result.log_file == ""
        assert result.port is None

    def test_read_invalid_port_type(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text(json.dumps({"name": "test", "pid": 1234, "port": "8080"}))
        result = _read_record(path)
        assert result.port is None


class TestWriteRecord:
    def test_write_record(self, tmp_path):
        path = tmp_path / "test.json"
        record = DaemonRecord(
            name="test",
            pid=1234,
            argv=["python", "test.py"],
            created_at=1234567890.0,
            log_file="/tmp/test.log",
            port=8080,
        )
        _write_record(path, record)
        data = json.loads(path.read_text())
        assert data["name"] == "test"
        assert data["pid"] == 1234
        assert data["port"] == 8080


class TestProcessExists:
    @patch("subprocess.check_output")
    def test_process_exists(self, mock_check_output, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        mock_check_output.return_value = b"python.exe 1234 Console"
        assert _process_exists(1234) is True

    @patch("os.kill")
    def test_process_not_exists_unix(self, mock_kill, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        mock_kill.side_effect = OSError()
        assert _process_exists(1234) is False

    def test_invalid_pid_zero(self):
        assert _process_exists(0) is False

    def test_invalid_pid_negative(self):
        assert _process_exists(-1) is False

    @patch("subprocess.check_output")
    def test_windows_process_exists(self, mock_check_output, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        mock_check_output.return_value = b"python.exe 1234 Console"
        assert _process_exists(1234) is True

    @patch("subprocess.check_output")
    def test_windows_process_not_exists(self, mock_check_output, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        mock_check_output.return_value = b"INFO: No tasks are running"
        assert _process_exists(1234) is False

    @patch("subprocess.check_output")
    def test_windows_check_output_exception(self, mock_check_output, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        mock_check_output.side_effect = Exception("error")
        assert _process_exists(1234) is False


class TestTerminate:
    @patch("bykcli.infra.daemon._process_exists")
    @patch("subprocess.Popen")
    @patch("time.sleep")
    def test_terminate_success_windows(self, mock_sleep, mock_popen, mock_exists, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        mock_exists.side_effect = [True, False]
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        result = _terminate(1234)
        assert result is True
        mock_popen.assert_called_once()

    @patch("bykcli.infra.daemon._process_exists")
    @patch("os.kill")
    @patch("time.sleep")
    def test_terminate_success_unix(self, mock_sleep, mock_kill, mock_exists, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        mock_exists.side_effect = [True, False]
        result = _terminate(1234)
        assert result is True
        mock_kill.assert_called_once()

    @patch("bykcli.infra.daemon._process_exists")
    def test_terminate_already_dead(self, mock_exists):
        mock_exists.return_value = False
        result = _terminate(1234)
        assert result is True

    @patch("bykcli.infra.daemon._process_exists")
    @patch("subprocess.Popen")
    @patch("time.sleep")
    def test_terminate_windows(self, mock_sleep, mock_popen, mock_exists, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        mock_exists.side_effect = [True, False]
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        result = _terminate(1234)
        assert result is True
        mock_popen.assert_called_once()

    @patch("bykcli.infra.daemon._process_exists")
    @patch("os.kill")
    @patch("time.sleep")
    def test_terminate_exception(self, mock_sleep, mock_kill, mock_exists):
        mock_exists.return_value = True
        mock_kill.side_effect = Exception("error")
        result = _terminate(1234)
        assert result is False


class TestExtractPort:
    def test_extract_port_short_flag(self):
        argv = ["-p", "8080"]
        assert _extract_port(argv) == 8080

    def test_extract_port_long_flag(self):
        argv = ["--port", "3000"]
        assert _extract_port(argv) == 3000

    def test_extract_port_equals(self):
        argv = ["--port=5000"]
        assert _extract_port(argv) == 5000

    def test_no_port_flag(self):
        argv = ["run", "server"]
        assert _extract_port(argv) is None

    def test_port_at_end(self):
        argv = ["-p"]
        assert _extract_port(argv) is None

    def test_invalid_port_value(self):
        argv = ["-p", "not-a-number"]
        assert _extract_port(argv) is None

    def test_invalid_port_equals(self):
        argv = ["--port=not-a-number"]
        assert _extract_port(argv) is None


class TestStartDaemon:
    @patch("bykcli.infra.daemon.subprocess.Popen")
    @patch("bykcli.infra.daemon._write_record")
    @patch("bykcli.infra.daemon._pid_file")
    def test_start_daemon_unix(self, mock_pid_file, mock_write, mock_popen, tmp_path):
        mock_process = MagicMock()
        mock_process.pid = 1234
        mock_popen.return_value = mock_process
        mock_pid_file.return_value = tmp_path / "daemon-test-1234.json"

        context = MagicMock()
        context.paths.logs_dir = tmp_path / "logs"

        with patch.object(sys, "platform", "linux"):
            result = start_daemon(context, "test", ["-p", "8080"])

        assert result.name == "test"
        assert result.pid == 1234
        assert result.port == 8080
        mock_write.assert_called_once()

    @patch("bykcli.infra.daemon.subprocess.Popen")
    @patch("bykcli.infra.daemon._write_record")
    @patch("bykcli.infra.daemon._pid_file")
    def test_start_daemon_windows(self, mock_pid_file, mock_write, mock_popen, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        mock_process = MagicMock()
        mock_process.pid = 1234
        mock_popen.return_value = mock_process
        mock_pid_file.return_value = tmp_path / "daemon-test-1234.json"

        context = MagicMock()
        context.paths.logs_dir = tmp_path / "logs"

        result = start_daemon(context, "test", [])

        assert result.name == "test"
        assert result.pid == 1234


class TestListDaemons:
    @patch("bykcli.infra.daemon._list_pid_files")
    @patch("bykcli.infra.daemon._read_record")
    @patch("bykcli.infra.daemon._process_exists")
    def test_list_running_daemon(self, mock_exists, mock_read, mock_list, tmp_path):
        pid_file = tmp_path / "daemon-test-1234.json"
        mock_list.return_value = [pid_file]
        mock_read.return_value = DaemonRecord(
            name="test",
            pid=1234,
            argv=["python", "test.py"],
            created_at=1234567890.0,
            log_file="/tmp/test.log",
            port=8080,
        )
        mock_exists.return_value = True

        context = MagicMock()
        result = list_daemons(context)

        assert len(result) == 1
        assert result[0]["name"] == "test"
        assert result[0]["alive"] is True
        assert result[0]["port"] == 8080

    @patch("bykcli.infra.daemon._list_pid_files")
    @patch("bykcli.infra.daemon._read_record")
    @patch("bykcli.infra.daemon._process_exists")
    def test_list_dead_daemon(self, mock_exists, mock_read, mock_list, tmp_path):
        pid_file = tmp_path / "daemon-test-1234.json"
        mock_list.return_value = [pid_file]
        mock_read.return_value = DaemonRecord(
            name="test",
            pid=1234,
            argv=["python", "test.py"],
            created_at=1234567890.0,
            log_file="/tmp/test.log",
        )
        mock_exists.return_value = False

        context = MagicMock()
        result = list_daemons(context)

        assert len(result) == 1
        assert result[0]["alive"] is False

    @patch("bykcli.infra.daemon._list_pid_files")
    @patch("bykcli.infra.daemon._read_record")
    def test_list_invalid_record(self, mock_read, mock_list, tmp_path):
        pid_file = tmp_path / "daemon-test-1234.json"
        mock_list.return_value = [pid_file]
        mock_read.return_value = None

        context = MagicMock()
        result = list_daemons(context)

        assert len(result) == 0


class TestStopByPid:
    @patch("bykcli.infra.daemon._list_pid_files")
    @patch("bykcli.infra.daemon._read_record")
    @patch("bykcli.infra.daemon._process_exists")
    @patch("bykcli.infra.daemon._terminate")
    def test_stop_running_daemon(self, mock_terminate, mock_exists, mock_read, mock_list, tmp_path):
        pid_file = tmp_path / "daemon-test-1234.json"
        mock_list.return_value = [pid_file]
        mock_read.return_value = DaemonRecord(
            name="test",
            pid=1234,
            argv=["python", "test.py"],
            created_at=1234567890.0,
            log_file="/tmp/test.log",
        )
        mock_exists.return_value = True
        mock_terminate.return_value = True

        context = MagicMock()
        result = stop_by_pid(context, 1234)

        assert len(result) == 1
        assert result[0]["status"] == "terminated"

    @patch("bykcli.infra.daemon._list_pid_files")
    @patch("bykcli.infra.daemon._read_record")
    @patch("bykcli.infra.daemon._process_exists")
    def test_stop_already_dead(self, mock_exists, mock_read, mock_list, tmp_path):
        pid_file = tmp_path / "daemon-test-1234.json"
        mock_list.return_value = [pid_file]
        mock_read.return_value = DaemonRecord(
            name="test",
            pid=1234,
            argv=["python", "test.py"],
            created_at=1234567890.0,
            log_file="/tmp/test.log",
        )
        mock_exists.return_value = False

        context = MagicMock()
        result = stop_by_pid(context, 1234)

        assert len(result) == 1
        assert result[0]["status"] == "not_running"

    @patch("bykcli.infra.daemon._list_pid_files")
    @patch("bykcli.infra.daemon._read_record")
    def test_stop_no_match(self, mock_read, mock_list, tmp_path):
        pid_file = tmp_path / "daemon-test-1234.json"
        mock_list.return_value = [pid_file]
        mock_read.return_value = DaemonRecord(
            name="test",
            pid=1234,
            argv=["python", "test.py"],
            created_at=1234567890.0,
            log_file="/tmp/test.log",
        )

        context = MagicMock()
        result = stop_by_pid(context, 5678)

        assert len(result) == 0


class TestKillDaemonCallback:
    def test_no_value(self):
        ctx = MagicMock()
        ctx.resilient_parsing = False
        result = kill_daemon_callback(ctx, None, None)
        assert result is None

    def test_resilient_parsing(self):
        ctx = MagicMock()
        ctx.resilient_parsing = True
        result = kill_daemon_callback(ctx, None, "all")
        assert result is None

    @patch("bykcli.infra.daemon.build_runtime")
    @patch("bykcli.infra.daemon.stop_by_pid")
    @patch("bykcli.infra.daemon.list_daemons")
    def test_kill_all(self, mock_list, mock_stop, mock_build_runtime):
        ctx = MagicMock()
        ctx.resilient_parsing = False
        ctx.obj = None
        mock_context = MagicMock()
        mock_build_runtime.return_value = mock_context
        mock_list.return_value = [
            {"pid": 1234, "name": "test1"},
            {"pid": 5678, "name": "test2"},
        ]
        mock_stop.return_value = [{"status": "terminated"}]
        ctx.exit.side_effect = SystemExit(0)

        with pytest.raises(SystemExit):
            kill_daemon_callback(ctx, None, "all")

    @patch("bykcli.infra.daemon.build_runtime")
    @patch("bykcli.infra.daemon.stop_by_pid")
    def test_kill_by_pid(self, mock_stop, mock_build_runtime):
        ctx = MagicMock()
        ctx.resilient_parsing = False
        ctx.obj = None
        mock_context = MagicMock()
        mock_build_runtime.return_value = mock_context
        mock_stop.return_value = [{"name": "test", "pid": 1234, "status": "terminated"}]
        ctx.exit.side_effect = SystemExit(0)

        with pytest.raises(SystemExit):
            kill_daemon_callback(ctx, None, "1234")

    def test_invalid_pid(self):
        ctx = MagicMock()
        ctx.resilient_parsing = False
        ctx.obj = MagicMock()

        from click import BadParameter
        with pytest.raises(BadParameter):
            kill_daemon_callback(ctx, None, "not-a-number")

    @patch("bykcli.infra.daemon.build_runtime")
    @patch("bykcli.infra.daemon.stop_by_pid")
    def test_kill_no_match(self, mock_stop, mock_build_runtime):
        ctx = MagicMock()
        ctx.resilient_parsing = False
        ctx.obj = None
        mock_context = MagicMock()
        mock_build_runtime.return_value = mock_context
        mock_stop.return_value = []
        ctx.exit.side_effect = SystemExit(0)

        with pytest.raises(SystemExit):
            kill_daemon_callback(ctx, None, "1234")
