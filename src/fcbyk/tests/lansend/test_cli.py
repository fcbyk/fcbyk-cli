import importlib


def test_lansend_help():
    from click.testing import CliRunner
    from fcbyk.cli import main

    r = CliRunner().invoke(main, ["lansend", "--help"])
    assert r.exit_code == 0


def test_lansend_daemon_passes_password_to_svc(monkeypatch, tmp_path):
    lansend_cli = importlib.import_module("fcbyk.commands.lansend.cli")

    d = tmp_path

    monkeypatch.setattr(
        lansend_cli,
        "get_private_networks",
        lambda: [
            {
                "iface": "localhost",
                "ips": ["127.0.0.1"],
                "type": "loopback",
                "virtual": True,
                "priority": 100,
            }
        ],
    )
    monkeypatch.setattr(lansend_cli, "copy_to_clipboard", lambda *_: None)
    monkeypatch.setattr(lansend_cli, "check_port", lambda *a, **k: True)
    monkeypatch.setattr(lansend_cli, "start_web_server", lambda *a, **k: None)
    monkeypatch.setattr(lansend_cli.webbrowser, "open", lambda *_: None)

    class _Svc:
        def __init__(self, *a, **k):
            pass

        def pick_upload_password(self, ask_password, disable_upload, click_mod):
            return "pw123"

    monkeypatch.setattr(lansend_cli, "LansendService", _Svc)

    called = {}

    def _fake_start_daemon(name, args):
        called["name"] = name
        called["args"] = list(args)

    monkeypatch.setattr(lansend_cli, "start_daemon", _fake_start_daemon)

    from click.testing import CliRunner

    r = CliRunner().invoke(
        lansend_cli.lansend,
        ["-d", str(d), "-p", "1234", "-D", "-ap", "--no-browser"],
    )

    assert r.exit_code == 0
    assert called["name"] == "lansend"
    assert "--daemon-password" in called["args"]
    assert "pw123" in called["args"]
