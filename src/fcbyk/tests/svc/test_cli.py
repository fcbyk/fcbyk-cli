from click.testing import CliRunner

from fcbyk.cli import main


def test_svc_help():
    runner = CliRunner()
    result = runner.invoke(main, ["svc", "--help"])
    assert result.exit_code == 0
    assert "Manage background services" in result.output


def test_svc_status_empty():
    runner = CliRunner()
    result = runner.invoke(main, ["svc", "status"])
    assert result.exit_code == 0


def test_svc_kill_uses_pid(monkeypatch):
    import fcbyk.svc as svc_core

    called = {}

    def _fake_stop(pid):
        called["pid"] = pid
        return [{"pid": pid, "name": "lansend", "status": "terminated"}]

    monkeypatch.setattr(svc_core, "stop_by_pid", _fake_stop)

    runner = CliRunner()
    result = runner.invoke(main, ["svc", "kill", "1234"])

    assert result.exit_code == 0
    assert called["pid"] == 1234
