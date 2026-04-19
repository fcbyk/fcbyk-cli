from __future__ import annotations

import json
from pathlib import Path

import pytest

from bykcli.infra.config import JsonFileConfigStore


class TestJsonFileConfigStore:
    def test_load_existing_config(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"key": "value", "number": 42}))

        store = JsonFileConfigStore(config_file)
        result = store.load()
        assert result == {"key": "value", "number": 42}

    def test_load_nonexistent_file(self, tmp_path):
        config_file = tmp_path / "config.json"
        store = JsonFileConfigStore(config_file)
        result = store.load()
        assert result == {}

    def test_load_not_dict(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps([1, 2, 3]))

        store = JsonFileConfigStore(config_file)
        result = store.load()
        assert result == {}

    def test_save_config(self, tmp_path):
        config_file = tmp_path / "config.json"
        store = JsonFileConfigStore(config_file)

        store.save({"key": "value"})

        result = json.loads(config_file.read_text())
        assert result == {"key": "value"}

    def test_get_existing_key(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"key": "value"}))

        store = JsonFileConfigStore(config_file)
        result = store.get("key")
        assert result == "value"

    def test_get_missing_key(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"key": "value"}))

        store = JsonFileConfigStore(config_file)
        result = store.get("missing")
        assert result is None

    def test_get_with_default(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({}))

        store = JsonFileConfigStore(config_file)
        result = store.get("key", default="default_value")
        assert result == "default_value"

    def test_set_new_key(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({}))

        store = JsonFileConfigStore(config_file)
        result = store.set("key", "value")

        assert result == {"key": "value"}
        assert json.loads(config_file.read_text()) == {"key": "value"}

    def test_set_update_existing_key(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"key": "old_value"}))

        store = JsonFileConfigStore(config_file)
        result = store.set("key", "new_value")

        assert result == {"key": "new_value"}

    def test_delete_existing_key(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"key": "value", "other": "data"}))

        store = JsonFileConfigStore(config_file)
        result = store.delete("key")

        assert result == {"other": "data"}
        assert "key" not in json.loads(config_file.read_text())

    def test_delete_missing_key(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"other": "data"}))

        store = JsonFileConfigStore(config_file)
        result = store.delete("missing")

        assert result == {"other": "data"}
