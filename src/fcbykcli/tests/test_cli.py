from __future__ import annotations

import json

from click.testing import CliRunner

from fcbykcli.app import create_cli


def build_cli():
    return create_cli()


def test_dashboard_shows_registered_commands(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    runner = CliRunner()
    result = runner.invoke(build_cli(), [])

    assert result.exit_code == 0
    assert "Plugins:" in result.output
    assert "hello" in result.output
    assert "paths" in result.output


def test_version_option(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    runner = CliRunner()
    result = runner.invoke(build_cli(), ["--version"])

    assert result.exit_code == 0
    assert "fcbyk-cli" in result.output


def test_paths_command(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    runner = CliRunner()
    result = runner.invoke(build_cli(), ["paths"])

    assert result.exit_code == 0
    assert "CLI Home:" in result.output
    assert "Alias File:" in result.output
    assert "Logs Directory:" in result.output


def test_paths_command_for_subcommand(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    runner = CliRunner()
    result = runner.invoke(build_cli(), ["paths", "hello"])

    assert result.exit_code == 0
    assert "Data File:" in result.output
    assert "CLI Home:" not in result.output
    assert "Alias File:" not in result.output
    assert "Logs Directory:" not in result.output


def test_hello_command(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    runner = CliRunner()
    result = runner.invoke(build_cli(), ["hello", "--name", "codex"])

    assert result.exit_code == 0
    assert "hello codex" in result.output
    assert "run count: 1" in result.output


def test_hello_command_persists_state(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    runner = CliRunner()
    first = runner.invoke(build_cli(), ["hello", "--name", "codex"])
    second = runner.invoke(build_cli(), ["hello", "--name", "codex"])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "run count: 2" in second.output


def test_alias_command_resolution(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    alias_dir = tmp_path / ".fcbyk-cli" / "config"
    alias_dir.mkdir(parents=True, exist_ok=True)
    (alias_dir / "alias.byk.json").write_text(
        json.dumps({"测试别名": {"命令": "echo alias-ok"}}, ensure_ascii=False),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(build_cli(), ["测试别名.命令"])

    assert result.exit_code == 0
    assert "run: echo alias-ok" in result.output
