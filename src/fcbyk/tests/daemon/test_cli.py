from click.testing import CliRunner

from fcbyk.cli import main


def test_kill_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    # --kill is an option, should appear in help
    assert result.exit_code == 0
    assert "--kill" in result.output or "-k" in result.output


def test_kill_all_daemons(monkeypatch):
    import fcbyk.core.daemon as daemon_core

    def _fake_status():
        return [
            {"pid": 1234, "name": "lansend", "alive": True, "port": 8000},
            {"pid": 5678, "name": "pick", "alive": True, "port": 8001},
        ]

    killed_pids = []

    def _fake_stop(pid):
        killed_pids.append(pid)
        return [{"pid": pid, "name": "test", "status": "terminated"}]

    # Mock the functions in the daemon module
    monkeypatch.setattr(daemon_core, "status_all_daemons", _fake_status)
    monkeypatch.setattr(daemon_core, "stop_by_pid", _fake_stop)

    runner = CliRunner()
    result = runner.invoke(main, ["--kill", "all"])

    assert result.exit_code == 0
    assert len(killed_pids) == 2


def test_kill_by_pid(monkeypatch):
    import fcbyk.core.daemon as daemon_core

    called = {}

    def _fake_stop(pid):
        called["pid"] = pid
        return [{"pid": pid, "name": "lansend", "status": "terminated"}]

    # Mock the function in the daemon module
    monkeypatch.setattr(daemon_core, "stop_by_pid", _fake_stop)

    runner = CliRunner()
    result = runner.invoke(main, ["--kill", "1234"])

    assert result.exit_code == 0
    assert called["pid"] == 1234


def test_kill_invalid_pid(monkeypatch):
    runner = CliRunner()
    result = runner.invoke(main, ["--kill", "abc"])

    # Should exit with error code due to invalid PID
    assert result.exit_code != 0 or "Invalid PID" in result.output
