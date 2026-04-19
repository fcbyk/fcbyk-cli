import importlib


def test_pick_help():
    from click.testing import CliRunner
    from fcbyk.cli import main

    r = CliRunner().invoke(main, ["pick", "--help"])
    assert r.exit_code == 0


def test_pick_default_starts_web(monkeypatch):
    """测试默认启动 Web 服务（端口 80）"""
    pick_cli = importlib.import_module("fcbyk.commands.pick.cli")
    
    called = {}
    
    def _start(port, no_browser, **kwargs):
        called.update({"port": port, "no_browser": no_browser, **kwargs})
    
    monkeypatch.setattr(pick_cli, "start_web_server", _start)
    monkeypatch.setattr(pick_cli, "check_port", lambda *_a, **_k: True)
    
    from click.testing import CliRunner
    
    r = CliRunner().invoke(pick_cli.pick, [])
    assert r.exit_code == 0
    assert called["port"] == 80
    assert called["no_browser"] is False


def test_pick_with_port_option(monkeypatch):
    """测试指定端口启动 Web 服务"""
    pick_cli = importlib.import_module("fcbyk.commands.pick.cli")
    
    called = {}
    
    def _start(port, no_browser, **kwargs):
        called.update({"port": port, "no_browser": no_browser, **kwargs})
    
    monkeypatch.setattr(pick_cli, "start_web_server", _start)
    monkeypatch.setattr(pick_cli, "check_port", lambda *_a, **_k: True)
    
    from click.testing import CliRunner
    
    r = CliRunner().invoke(pick_cli.pick, ["-p", "8080"])
    assert r.exit_code == 0
    assert called["port"] == 8080


def test_pick_no_browser_option(monkeypatch):
    """测试 --no-browser 选项"""
    pick_cli = importlib.import_module("fcbyk.commands.pick.cli")
    
    called = {}
    
    def _start(port, no_browser, **kwargs):
        called.update({"port": port, "no_browser": no_browser, **kwargs})
    
    monkeypatch.setattr(pick_cli, "start_web_server", _start)
    monkeypatch.setattr(pick_cli, "check_port", lambda *_a, **_k: True)
    
    from click.testing import CliRunner
    
    r = CliRunner().invoke(pick_cli.pick, ["--no-browser"])
    assert r.exit_code == 0
    assert called["no_browser"] is True


def test_pick_files_mode_prompts_password(monkeypatch, tmp_path):
    """测试文件模式提示输入密码"""
    pick_cli = importlib.import_module("fcbyk.commands.pick.cli")
    
    f = tmp_path / "a.txt"
    f.write_text("hi", encoding="utf-8")
    
    # 用户输入空 => 使用默认 123456
    monkeypatch.setattr("click.prompt", lambda *_a, **_k: "")
    
    called = {}
    
    def _start(**kwargs):
        called.update(kwargs)
    
    monkeypatch.setattr(pick_cli, "start_web_server", _start)
    monkeypatch.setattr(pick_cli, "check_port", lambda *_a, **_k: True)
    
    from click.testing import CliRunner
    
    # 显式指定高端口，避免 CI/Linux 环境下默认 80 需要 root 权限
    r = CliRunner().invoke(pick_cli.pick, ["-f", str(f), "-pw", "-p", "8888"])
    assert r.exit_code == 0
    assert called["admin_password"] == "123456"


def test_pick_files_mode_custom_password(monkeypatch, tmp_path):
    """测试文件模式自定义密码"""
    pick_cli = importlib.import_module("fcbyk.commands.pick.cli")
    
    f = tmp_path / "a.txt"
    f.write_text("hi", encoding="utf-8")
    
    # 用户输入自定义密码
    monkeypatch.setattr("click.prompt", lambda *_a, **_k: "mypassword")
    
    called = {}
    
    def _start(**kwargs):
        called.update(kwargs)
    
    monkeypatch.setattr(pick_cli, "start_web_server", _start)
    monkeypatch.setattr(pick_cli, "check_port", lambda *_a, **_k: True)
    
    from click.testing import CliRunner
    
    r = CliRunner().invoke(pick_cli.pick, ["-f", str(f), "-pw", "-p", "8888"])
    assert r.exit_code == 0
    assert called["admin_password"] == "mypassword"


def test_pick_files_daemon_passes_password_to_svc(monkeypatch, tmp_path):
    """测试后台模式下传递密码到 svc"""
    pick_cli = importlib.import_module("fcbyk.commands.pick.cli")
    
    f = tmp_path / "b.txt"
    f.write_text("hi", encoding="utf-8")
    
    monkeypatch.setattr("click.prompt", lambda *_a, **_k: "pw999")
    
    called = {}
    
    def _start_service(name, args):
        called["name"] = name
        called["args"] = list(args)
    
    monkeypatch.setattr(pick_cli.svc_core, "start_service", _start_service)
    monkeypatch.setattr(pick_cli, "check_port", lambda *_a, **_k: True)
    
    from click.testing import CliRunner
    
    r = CliRunner().invoke(
        pick_cli.pick,
        ["-f", str(f), "-pw", "-p", "8888", "-D"],
    )
    
    assert r.exit_code == 0
    assert called["name"] == "pick"
    assert "--daemon-password" in called["args"]
    assert "pw999" in called["args"]


def test_pick_daemon_mode(monkeypatch):
    """测试普通模式的后台运行"""
    pick_cli = importlib.import_module("fcbyk.commands.pick.cli")
    
    called = {}
    
    def _start_service(name, args):
        called["name"] = name
        called["args"] = list(args)
    
    monkeypatch.setattr(pick_cli.svc_core, "start_service", _start_service)
    monkeypatch.setattr(pick_cli, "check_port", lambda *_a, **_k: True)
    
    from click.testing import CliRunner
    
    r = CliRunner().invoke(pick_cli.pick, ["-p", "9000", "-D"])
    
    assert r.exit_code == 0
    assert called["name"] == "pick"
    assert "--port" in called["args"]
    assert "9000" in called["args"]
    assert "--no-browser" in called["args"]
