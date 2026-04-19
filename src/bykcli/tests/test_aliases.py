from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest

from bykcli.core.errors import CliError
from bykcli.infra.aliases import (
    AliasAwareGroup,
    AliasDefinition,
    collect_alias_paths,
    get_display_width,
    get_terminal_width,
    is_dangerous_command,
    load_aliases,
    pad_display_text,
    parse_alias_arguments,
    render_alias_lines,
    resolve_nested_alias,
    wrap_text,
)


class TestAliasDefinition:
    def test_create_with_command_only(self):
        alias = AliasDefinition(command="echo hello")
        assert alias.command == "echo hello"
        assert alias.cwd is None

    def test_create_with_cwd(self):
        alias = AliasDefinition(command="echo hello", cwd="/tmp")
        assert alias.command == "echo hello"
        assert alias.cwd == "/tmp"


class TestLoadAliases:
    def test_load_global_aliases(self, tmp_path, monkeypatch):
        context = MagicMock()
        context.paths.alias_file = tmp_path / "alias.byk.json"
        (tmp_path / "alias.byk.json").write_text(json.dumps({"test": "echo test"}))

        result = load_aliases(context, merge_local=False)
        assert result == {"test": "echo test"}

    def test_load_returns_empty_dict_if_not_dict(self, tmp_path, monkeypatch):
        context = MagicMock()
        context.paths.alias_file = tmp_path / "alias.byk.json"
        (tmp_path / "alias.byk.json").write_text(json.dumps([1, 2, 3]))

        result = load_aliases(context, merge_local=False)
        assert result == {}

    def test_load_with_local_merge(self, tmp_path, monkeypatch):
        context = MagicMock()
        context.paths.alias_file = tmp_path / "global" / "alias.byk.json"
        (tmp_path / "global").mkdir(parents=True, exist_ok=True)
        (tmp_path / "global" / "alias.byk.json").write_text(json.dumps({"global": "echo global"}))

        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "project")
        (tmp_path / "project").mkdir(parents=True, exist_ok=True)
        (tmp_path / "project" / "alias.byk.json").write_text(json.dumps({"local": "echo local"}))

        result = load_aliases(context, merge_local=True)
        assert "global" in result
        assert "local" in result

    def test_load_with_script_byk_json(self, tmp_path, monkeypatch):
        context = MagicMock()
        context.paths.alias_file = tmp_path / "global" / "alias.byk.json"
        (tmp_path / "global").mkdir(parents=True, exist_ok=True)
        (tmp_path / "global" / "alias.byk.json").write_text(json.dumps({}))

        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "project")
        (tmp_path / "project").mkdir(parents=True, exist_ok=True)
        (tmp_path / "project" / "script.byk.json").write_text(json.dumps({"script": "echo script"}))

        result = load_aliases(context, merge_local=True)
        assert "script" in result


class TestResolveNestedAlias:
    def test_resolve_simple_string_alias(self):
        aliases = {"test": "echo hello"}
        result = resolve_nested_alias(aliases, "test")
        assert result is not None
        assert result.command == "echo hello"
        assert result.cwd is None

    def test_resolve_dict_alias(self):
        aliases = {"test": {"cmd": "echo hello", "cwd": "/tmp"}}
        result = resolve_nested_alias(aliases, "test")
        assert result is not None
        assert result.command == "echo hello"
        assert result.cwd == "/tmp"

    def test_resolve_nested_alias(self):
        aliases = {"group": {"sub": "echo nested"}}
        result = resolve_nested_alias(aliases, "group.sub")
        assert result is not None
        assert result.command == "echo nested"

    def test_resolve_not_found(self):
        aliases = {"test": "echo hello"}
        result = resolve_nested_alias(aliases, "missing")
        assert result is None

    def test_resolve_nested_not_dict(self):
        aliases = {"test": "echo hello"}
        result = resolve_nested_alias(aliases, "test.sub")
        assert result is None

    def test_resolve_missing_cmd(self):
        aliases = {"test": {"cwd": "/tmp"}}
        result = resolve_nested_alias(aliases, "test")
        assert result is None

    def test_resolve_cmd_not_string(self):
        aliases = {"test": {"cmd": 123}}
        result = resolve_nested_alias(aliases, "test")
        assert result is None

    def test_resolve_cwd_not_string(self):
        aliases = {"test": {"cmd": "echo hello", "cwd": 123}}
        result = resolve_nested_alias(aliases, "test")
        assert result is not None
        assert result.cwd is None


class TestCollectAliasPaths:
    def test_collect_simple_aliases(self):
        aliases = {"a": "cmd1", "b": "cmd2"}
        result = collect_alias_paths(aliases)
        assert sorted(result) == ["a", "b"]

    def test_collect_nested_aliases(self):
        aliases = {"group": {"sub1": "cmd1", "sub2": "cmd2"}}
        result = collect_alias_paths(aliases)
        assert sorted(result) == ["group.sub1", "group.sub2"]

    def test_collect_dict_with_cmd(self):
        aliases = {"test": {"cmd": "echo hello"}}
        result = collect_alias_paths(aliases)
        assert result == ["test"]

    def test_collect_mixed(self):
        aliases = {
            "simple": "cmd1",
            "group": {
                "sub": "cmd2",
                "withcmd": {"cmd": "cmd3"},
            },
        }
        result = collect_alias_paths(aliases)
        assert sorted(result) == ["group.sub", "group.withcmd", "simple"]

    def test_collect_empty(self):
        aliases = {}
        result = collect_alias_paths(aliases)
        assert result == []


class TestParseAliasArguments:
    def test_parse_with_args_placeholder(self):
        command = "echo {args}"
        args = ["hello", "world"]
        result = parse_alias_arguments(command, args)
        assert result == "echo hello world"

    def test_parse_with_indexed_placeholders(self):
        command = "cp {0} {1}"
        args = ["file1", "file2"]
        result = parse_alias_arguments(command, args)
        assert result == "cp file1 file2"

    def test_parse_no_placeholders(self):
        command = "echo hello"
        args = ["extra"]
        result = parse_alias_arguments(command, args)
        assert result == "echo hello extra"

    def test_parse_no_args(self):
        command = "echo hello"
        args = []
        result = parse_alias_arguments(command, args)
        assert result == "echo hello"

    def test_parse_missing_placeholder(self):
        command = "cp {0} {1}"
        args = ["file1"]
        with pytest.raises(CliError) as exc_info:
            parse_alias_arguments(command, args)
        assert "缺少占位参数" in str(exc_info.value)


class TestIsDangerousCommand:
    def test_dangerous_rm_rf(self):
        assert is_dangerous_command("rm -rf /") is True

    def test_dangerous_git_force_push(self):
        assert is_dangerous_command("git push -f origin main") is True

    def test_dangerous_shutdown(self):
        assert is_dangerous_command("shutdown now") is True

    def test_dangerous_reboot(self):
        assert is_dangerous_command("reboot") is True

    def test_dangerous_format(self):
        assert is_dangerous_command("format C:") is True

    def test_dangerous_rd(self):
        assert is_dangerous_command("rd /s /q folder") is True

    def test_dangerous_del(self):
        assert is_dangerous_command("del /s /q file") is True

    def test_dangerous_dev_sd(self):
        assert is_dangerous_command("> /dev/sda") is True

    def test_safe_command(self):
        assert is_dangerous_command("echo hello") is False

    def test_case_insensitive(self):
        assert is_dangerous_command("RM -RF /") is True


class TestGetDisplayWidth:
    def test_ascii_characters(self):
        assert get_display_width("hello") == 5

    def test_chinese_characters(self):
        assert get_display_width("你好") == 4

    def test_mixed_characters(self):
        assert get_display_width("hello世界") == 9

    def test_combining_characters(self):
        assert get_display_width("caf\u0301") == 3

    def test_fullwidth_characters(self):
        assert get_display_width("ＡＢＣ") == 6


class TestPadDisplayText:
    def test_pad_shorter_text(self):
        result = pad_display_text("hi", 5)
        assert result == "hi   "

    def test_pad_equal_length(self):
        result = pad_display_text("hello", 5)
        assert result == "hello"

    def test_pad_longer_text(self):
        result = pad_display_text("hello world", 5)
        assert result == "hello world"

    def test_pad_with_min_spaces(self):
        result = pad_display_text("hi", 5, min_spaces=2)
        assert result == "hi     "

    def test_pad_chinese(self):
        result = pad_display_text("你好", 6)
        assert result == "你好  "


class TestGetTerminalWidth:
    @patch("shutil.get_terminal_size")
    def test_get_terminal_size_success(self, mock_get_size):
        mock_size = MagicMock()
        mock_size.columns = 120
        mock_get_size.return_value = mock_size
        assert get_terminal_width() == 120

    @patch("shutil.get_terminal_size")
    def test_get_terminal_size_default(self, mock_get_size):
        mock_size = MagicMock()
        mock_size.columns = None
        mock_get_size.return_value = mock_size
        assert get_terminal_width() == 80

    @patch("shutil.get_terminal_size")
    def test_get_terminal_size_exception(self, mock_get_size):
        mock_get_size.side_effect = Exception("error")
        assert get_terminal_width() == 80


class TestWrapText:
    def test_wrap_short_text(self):
        result = wrap_text("hello world", 20)
        assert result == ["hello world"]

    def test_wrap_long_text(self):
        result = wrap_text("hello world this is a long text", 10)
        assert result == ["hello", "world this", "is a long", "text"]

    def test_wrap_exact_width(self):
        result = wrap_text("hello world", 11)
        assert result == ["hello world"]

    def test_wrap_empty_text(self):
        result = wrap_text("", 10)
        assert result == []

    def test_wrap_whitespace_only(self):
        result = wrap_text("   ", 10)
        assert result == []

    def test_wrap_max_width_zero(self):
        result = wrap_text("hello", 0)
        assert result == ["hello"]

    def test_wrap_max_width_negative(self):
        result = wrap_text("hello", -1)
        assert result == ["hello"]

    def test_wrap_single_long_word(self):
        result = wrap_text("supercalifragilisticexpialidocious", 10)
        assert result == ["supercalifragilisticexpialidocious"]


class TestRenderAliasLines:
    def test_render_empty_aliases(self, tmp_path, monkeypatch):
        context = MagicMock()
        context.paths.alias_file = tmp_path / "alias.byk.json"
        (tmp_path / "alias.byk.json").write_text(json.dumps({}))
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        result = render_alias_lines(context)
        assert result == []

    def test_render_simple_aliases(self, tmp_path, monkeypatch):
        context = MagicMock()
        context.paths.alias_file = tmp_path / "alias.byk.json"
        (tmp_path / "alias.byk.json").write_text(json.dumps({"test": "echo hello"}))
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        result = render_alias_lines(context)
        assert len(result) == 1
        assert "test" in result[0]
        assert "echo hello" in result[0]

    def test_render_with_cwd(self, tmp_path, monkeypatch):
        context = MagicMock()
        context.paths.alias_file = tmp_path / "alias.byk.json"
        (tmp_path / "alias.byk.json").write_text(
            json.dumps({"test": {"cmd": "echo hello", "cwd": "/tmp"}})
        )
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        result = render_alias_lines(context)
        assert len(result) == 1
        assert "(cwd: /tmp)" in result[0]


class TestAliasAwareGroup:
    def test_resolve_command_super_success(self):
        group = AliasAwareGroup()
        mock_cmd = MagicMock()
        group.add_command(mock_cmd, name="test")

        ctx = MagicMock()
        result = group.resolve_command(ctx, ["test"])
        assert result[1] == mock_cmd

    def test_resolve_alias_command(self, tmp_path, monkeypatch):
        group = AliasAwareGroup()
        group.runtime_provider = None

        context = MagicMock()
        context.app_name = "testapp"
        context.version = "1.0.0"
        context.paths.alias_file = tmp_path / "alias.byk.json"
        (tmp_path / "alias.byk.json").write_text(json.dumps({"myalias": "echo hello"}))
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        ctx = MagicMock()
        ctx.obj = MagicMock()
        ctx.obj.context = context

        with patch.object(click.Group, "resolve_command") as mock_super:
            mock_super.side_effect = click.UsageError("not found")
            with pytest.raises(SystemExit) as exc_info:
                with patch("bykcli.infra.aliases.subprocess.run") as mock_run:
                    group.resolve_command(ctx, ["myalias"])
            assert exc_info.value.code == 0

    def test_resolve_unknown_alias(self, tmp_path, monkeypatch):
        group = AliasAwareGroup()

        context = MagicMock()
        context.paths.alias_file = tmp_path / "alias.byk.json"
        (tmp_path / "alias.byk.json").write_text(json.dumps({}))
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        ctx = MagicMock()
        ctx.obj = MagicMock()
        ctx.obj.context = context

        with patch.object(click.Group, "resolve_command") as mock_super:
            mock_super.side_effect = click.UsageError("not found")
            with pytest.raises(click.UsageError) as exc_info:
                group.resolve_command(ctx, ["unknown"])
            assert "Unknown command or alias" in str(exc_info.value)

    def test_resolve_with_suggestions(self, tmp_path, monkeypatch):
        group = AliasAwareGroup()

        context = MagicMock()
        context.paths.alias_file = tmp_path / "alias.byk.json"
        (tmp_path / "alias.byk.json").write_text(json.dumps({"group.sub": "echo hello"}))
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        ctx = MagicMock()
        ctx.obj = MagicMock()
        ctx.obj.context = context

        with patch.object(click.Group, "resolve_command") as mock_super:
            mock_super.side_effect = click.UsageError("not found")
            with pytest.raises(click.UsageError) as exc_info:
                group.resolve_command(ctx, ["group"])
            assert "Did you mean" in str(exc_info.value)

    def test_get_context_from_ctx_obj(self):
        group = AliasAwareGroup()
        ctx = MagicMock()
        ctx.obj = MagicMock()
        ctx.obj.context = MagicMock()

        result = group._get_context(ctx)
        assert result == ctx.obj.context

    def test_get_context_from_runtime_provider(self):
        group = AliasAwareGroup()
        group.runtime_provider = lambda: MagicMock()

        ctx = MagicMock()
        ctx.obj = None

        result = group._get_context(ctx)
        assert result is not None

    def test_get_context_raises_when_no_context(self):
        group = AliasAwareGroup()
        group.runtime_provider = None

        ctx = MagicMock()
        ctx.obj = None

        with pytest.raises(click.ClickException) as exc_info:
            group._get_context(ctx)
        assert "Runtime context not yet initialized" in str(exc_info.value)

    def test_invoke_click_exception(self):
        group = AliasAwareGroup()
        ctx = MagicMock()
        ctx.obj.context.paths.app_log_file = "/tmp/log"

        with patch.object(click.Group, "invoke") as mock_invoke:
            mock_invoke.side_effect = click.ClickException("click error")
            with pytest.raises(click.ClickException):
                group.invoke(ctx)

    def test_invoke_cli_error(self):
        group = AliasAwareGroup()
        ctx = MagicMock()
        ctx.obj.context.paths.app_log_file = "/tmp/log"

        with patch.object(click.Group, "invoke") as mock_invoke:
            mock_invoke.side_effect = CliError("cli error")
            with pytest.raises(click.ClickException) as exc_info:
                group.invoke(ctx)
            assert "cli error" in str(exc_info.value)

    def test_invoke_system_exit(self):
        group = AliasAwareGroup()
        ctx = MagicMock()

        with patch.object(click.Group, "invoke") as mock_invoke:
            mock_invoke.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                group.invoke(ctx)

    def test_invoke_click_exit(self):
        group = AliasAwareGroup()
        ctx = MagicMock()

        with patch.object(click.Group, "invoke") as mock_invoke:
            mock_invoke.side_effect = click.exceptions.Exit(0)
            with pytest.raises(click.exceptions.Exit):
                group.invoke(ctx)

    def test_invoke_unexpected_exception(self):
        group = AliasAwareGroup()
        ctx = MagicMock()
        ctx.obj.context.paths.app_log_file = "/tmp/log"

        with patch.object(click.Group, "invoke") as mock_invoke:
            mock_invoke.side_effect = Exception("unexpected")
            with pytest.raises(click.ClickException) as exc_info:
                group.invoke(ctx)
            assert "Unexpected error occurred" in str(exc_info.value)
