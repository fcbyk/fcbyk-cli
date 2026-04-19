from __future__ import annotations

import json

from click.testing import CliRunner

from bykcli.app import create_cli


def build_cli():
    return create_cli()


def test_dashboard_shows_registered_commands(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    runner = CliRunner()
    result = runner.invoke(build_cli(), [])

    assert result.exit_code == 0
    assert "Commands:" in result.output
    assert "paths" in result.output


def test_version_option(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    runner = CliRunner()
    result = runner.invoke(build_cli(), ["--version"])

    assert result.exit_code == 0
    assert "Version:" in result.output


def test_paths_command(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    runner = CliRunner()
    result = runner.invoke(build_cli(), ["paths"])

    assert result.exit_code == 0
    assert "CLI Home:" in result.output
    assert "Alias File:" in result.output
    assert "Logs Directory:" in result.output


def test_alias_command_resolution(tmp_path, monkeypatch):

    from pathlib import Path
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    
    alias_dir = tmp_path / ".bykcli" / "config"
    alias_dir.mkdir(parents=True, exist_ok=True)
    (alias_dir / "alias.byk.json").write_text(
        json.dumps({"测试别名": {"命令": "echo alias-ok"}}, ensure_ascii=False),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(build_cli(), ["测试别名.命令"])

    assert result.exit_code == 0
    assert "run: echo alias-ok" in result.output
