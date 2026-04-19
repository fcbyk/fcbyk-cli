import importlib


def test_slide_help():
    from click.testing import CliRunner
    from fcbyk.cli import main

    runner = CliRunner()
    r = runner.invoke(main, ["slide", "--help"])
    assert r.exit_code == 0
    assert "PPT remote control" in r.output.lower() or "ppt" in r.output.lower()


def test_slide_cli_uses_localhost_when_no_network(monkeypatch):
    # 测试：当只有回环地址可用时，CLI 能正常工作
    slide_cli = importlib.import_module("fcbyk.commands.slide.cli")

    # prompt 返回密码
    monkeypatch.setattr("click.prompt", lambda *a, **k: "p")

    # 模拟只有回环地址的情况
    monkeypatch.setattr(slide_cli, "get_private_networks", lambda: [
        {"iface": "localhost", "ips": ["127.0.0.1"], "type": "loopback", "virtual": True, "priority": 100}
    ])

    # 避免真实剪贴板
    monkeypatch.setattr(slide_cli, "copy_to_clipboard", lambda *_: None)
    
    # 端口占用检测在测试环境可能误判，直接 mock 掉
    monkeypatch.setattr(slide_cli, "check_port", lambda *a, **k: True)

    # mock create_slide_app 返回 (app, socketio)，且 socketio.run 不做事
    run_kwargs = {}

    class MockSocketIO:
        def run(self, app, **kwargs):
            run_kwargs.update(kwargs)

    mock_socketio = MockSocketIO()
    monkeypatch.setattr(slide_cli, "create_slide_app", lambda service: (object(), mock_socketio))

    # 避免输出 URL 列表逻辑
    monkeypatch.setattr(slide_cli, "echo_network_urls", lambda *a, **k: None)

    from click.testing import CliRunner

    runner = CliRunner()
    r = runner.invoke(slide_cli.slide, ["--port", "1234"])

    assert r.exit_code == 0
    assert run_kwargs["host"] == "0.0.0.0"
    assert run_kwargs["port"] == 1234


def test_slide_daemon_passes_password_to_svc(monkeypatch):
    slide_cli = importlib.import_module("fcbyk.commands.slide.cli")

    # 避免真实交互和外部依赖
    monkeypatch.setattr("click.prompt", lambda *a, **k: "p")
    monkeypatch.setattr(slide_cli, "get_private_networks", lambda: [
        {"iface": "localhost", "ips": ["127.0.0.1"], "type": "loopback", "virtual": True, "priority": 100}
    ])
    monkeypatch.setattr(slide_cli, "copy_to_clipboard", lambda *_: None)
    monkeypatch.setattr(slide_cli, "check_port", lambda *a, **k: True)
    monkeypatch.setattr(slide_cli, "echo_network_urls", lambda *a, **k: None)

    class _DummySocketIO:
        def run(self, *a, **k):
            pass

    monkeypatch.setattr(slide_cli, "create_slide_app", lambda service: (object(), _DummySocketIO()))

    called = {}

    def _fake_start_service(name, args):
        called["name"] = name
        called["args"] = list(args)
        return {"name": name, "pid": 1}

    monkeypatch.setattr(slide_cli.svc_core, "start_service", _fake_start_service)

    from click.testing import CliRunner

    runner = CliRunner()
    r = runner.invoke(slide_cli.slide, ["--port", "1234", "-D"])

    assert r.exit_code == 0
    assert called["name"] == "slide"
    # 应该把端口和密码都传给后台进程
    assert "--port" in called["args"]
    assert "1234" in called["args"]
    assert "--daemon-password" in called["args"]
