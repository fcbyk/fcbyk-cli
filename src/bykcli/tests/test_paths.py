from __future__ import annotations

from unittest.mock import MagicMock

from bykcli.api.paths import (
    _PATH_PROVIDERS,
    get_path_provider,
    global_path_items,
    register_path_provider,
)


class TestRegisterPathProvider:
    def test_register_provider(self):
        def provider(context):
            return [("Test", "/test/path")]

        register_path_provider("test_cmd", provider)
        assert "test_cmd" in _PATH_PROVIDERS
        assert _PATH_PROVIDERS["test_cmd"] == provider

        del _PATH_PROVIDERS["test_cmd"]


class TestGetPathProvider:
    def test_get_existing_provider(self):
        def provider(context):
            return [("Test", "/test/path")]

        _PATH_PROVIDERS["test_cmd"] = provider
        result = get_path_provider("test_cmd")
        assert result == provider

        del _PATH_PROVIDERS["test_cmd"]

    def test_get_nonexistent_provider(self):
        result = get_path_provider("nonexistent")
        assert result is None


class TestGlobalPathItems:
    def test_returns_expected_paths(self):
        context = MagicMock()
        context.paths.root_dir = "/home/user/.fcbyk"
        context.paths.alias_file = "/home/user/.fcbyk/config/alias.byk.json"
        context.paths.logs_dir = "/home/user/.fcbyk/logs"

        result = global_path_items(context)

        assert len(result) == 3
        assert result[0] == ("CLI Home", "/home/user/.fcbyk")
        assert result[1] == ("Alias File", "/home/user/.fcbyk/config/alias.byk.json")
        assert result[2] == ("Logs Directory", "/home/user/.fcbyk/logs")
