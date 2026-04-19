from __future__ import annotations

from bykcli.runtime import build_runtime


def test_command_store_is_isolated_per_command(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    context = build_runtime()
    hello_store = context.command_store("hello")
    pick_store = context.command_store("pick")

    hello_store.set("count", 3)
    pick_store.set("count", 9)

    assert hello_store.get("count") == 3
    assert pick_store.get("count") == 9
    assert hello_store.path != pick_store.path
    assert hello_store.path.name == "state.json"


def test_shared_store_writes_under_config_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    context = build_runtime()
    store = context.shared_store()
    store.set("theme", "light")

    assert store.get("theme") == "light"
    assert store.path.parent == context.paths.config_dir
