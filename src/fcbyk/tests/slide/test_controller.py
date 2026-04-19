import importlib

import pytest

slide_controller = importlib.import_module("fcbyk.commands.slide.controller")
slide_service = importlib.import_module("fcbyk.commands.slide.service")
SlideService = slide_service.SlideService


@pytest.fixture
def app_and_client(monkeypatch):
    # 避免依赖真实模板，直接用一个最小 Flask app
    from flask import Flask

    monkeypatch.setattr(slide_controller, "create_spa", lambda *_: Flask(__name__))

    service = SlideService(password="p")
    app, _socketio = slide_controller.create_slide_app(service)
    app.config["TESTING"] = True

    with app.test_client() as c:
        yield app, c, service


def test_login_and_check_auth(app_and_client):
    app, client, _service = app_and_client

    # 初始未登录
    r = client.get("/api/check_auth")
    assert r.status_code == 200
    assert r.json["code"] == 200
    assert r.json["data"]["authenticated"] is False

    # 登录失败
    r = client.post("/api/login", json={"password": "x"})
    assert r.status_code == 401
    assert r.json["code"] == 401

    # 登录成功
    r = client.post("/api/login", json={"password": "p"})
    assert r.status_code == 200
    assert r.json["code"] == 200

    # 登录后 check_auth
    r = client.get("/api/check_auth")
    assert r.status_code == 200
    assert r.json["code"] == 200
    assert r.json["data"]["authenticated"] is True


def test_require_auth_blocks_actions(app_and_client, monkeypatch):
    _app, client, service = app_and_client

    # 未认证调用 next 应 401
    r = client.post("/api/next")
    assert r.status_code == 401

    # 登录后再调用
    client.post("/api/login", json={"password": "p"})

    monkeypatch.setattr(service, "next_slide", lambda: (True, None))
    r = client.post("/api/next")
    assert r.status_code == 200
    assert r.json["code"] == 200
    assert r.json["data"]["action"] == "next"


def test_action_error_returns_500(app_and_client, monkeypatch):
    _app, client, service = app_and_client
    client.post("/api/login", json={"password": "p"})

    monkeypatch.setattr(service, "prev_slide", lambda: (False, "boom"))
    r = client.post("/api/prev")
    assert r.status_code == 500
    assert r.json["code"] == 500
    assert r.json["message"] == "boom"


def test_mouse_move_endpoint(app_and_client, monkeypatch):
    _app, client, service = app_and_client
    client.post("/api/login", json={"password": "p"})

    called = {}

    def _move(dx, dy):
        called.update({"dx": dx, "dy": dy})
        return True, None

    monkeypatch.setattr(service, "move_mouse", _move)

    r = client.post("/api/mouse/move", json={"dx": 1, "dy": -2})
    assert r.status_code == 200
    assert r.json["code"] == 200
    assert r.json["data"]["action"] == "move"
    assert called == {"dx": 1, "dy": -2}


def test_mouse_other_endpoints(app_and_client, monkeypatch):
    _app, client, service = app_and_client
    client.post("/api/login", json={"password": "p"})

    monkeypatch.setattr(service, "click_mouse", lambda: (True, None))
    monkeypatch.setattr(service, "mouse_down", lambda: (True, None))
    monkeypatch.setattr(service, "mouse_up", lambda: (True, None))
    monkeypatch.setattr(service, "right_click_mouse", lambda: (True, None))
    monkeypatch.setattr(service, "scroll_mouse", lambda dx, dy: (True, None))

    r = client.post("/api/mouse/down")
    assert r.status_code == 200
    assert r.json["data"]["action"] == "down"

    r = client.post("/api/mouse/up")
    assert r.status_code == 200
    assert r.json["data"]["action"] == "up"

    r = client.post("/api/mouse/click")
    assert r.status_code == 200
    assert r.json["data"]["action"] == "click"

    r = client.post("/api/mouse/rightclick")
    assert r.status_code == 200
    assert r.json["data"]["action"] == "rightclick"

    r = client.post("/api/mouse/scroll", json={"dx": 1, "dy": 2})
    assert r.status_code == 200
    assert r.json["data"]["action"] == "scroll"


def test_require_socketio_auth_wrapper_returns_none_when_unauthenticated(app_and_client):
    app, _client, _service = app_and_client

    decorated = slide_controller.require_socketio_auth(lambda: "ok")

    class _Sess(dict):
        pass

    old = slide_controller.session
    try:
        slide_controller.session = _Sess(authenticated=False)
        assert decorated() is None

        slide_controller.session = _Sess(authenticated=True)
        assert decorated() == "ok"
    finally:
        slide_controller.session = old


def test_require_auth_wrapper_blocks_when_unauthenticated(app_and_client):
    app, _client, _service = app_and_client

    decorated = slide_controller.require_auth(lambda: ("ok", 200))

    class _Sess(dict):
        pass

    old = slide_controller.session
    try:
        slide_controller.session = _Sess(authenticated=False)
        with app.app_context():
            resp, status = decorated()
        assert status == 401
        assert resp.json["code"] == 401
        assert resp.json["message"] == "Unauthorized"

        slide_controller.session = _Sess(authenticated=True)
        with app.app_context():
            assert decorated() == ("ok", 200)
    finally:
        slide_controller.session = old


def test_qr_info_only_available_for_local_and_auto_login(app_and_client, monkeypatch):
    _app, client, _service = app_and_client

    r = client.get("/internal/qr/info", environ_base={"REMOTE_ADDR": "192.168.0.2"})
    assert r.status_code == 404

    monkeypatch.setattr(slide_controller, "_get_wifi_name", lambda: "TestWiFi")

    r = client.get("/internal/qr/info", environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert r.status_code == 200
    assert r.json["code"] == 200
    login_url = r.json["data"]["login_url"]
    assert r.json["data"]["wifi_name"] == "TestWiFi"
    assert "/auto-login?token=" in login_url

    token = login_url.split("token=", 1)[-1]

    r = client.get(
        "/internal/qr/status",
        query_string={"token": token},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
    )
    assert r.status_code == 200
    assert r.json["code"] == 200
    assert r.json["data"]["valid"] is True

    path_and_query = login_url.split("://", 1)[-1]
    _, _, path_with_query = path_and_query.partition("/")
    path = "/" + path_with_query

    r = client.get(path)
    assert r.status_code in (301, 302)

    r = client.get(
        "/internal/qr/status",
        query_string={"token": token},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
    )
    assert r.status_code == 200
    assert r.json["code"] == 200
    assert r.json["data"]["valid"] is False

    r = client.get("/api/check_auth")
    assert r.status_code == 200
    assert r.json["data"]["authenticated"] is True
