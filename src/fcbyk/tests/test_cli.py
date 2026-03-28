import pytest
from click.testing import CliRunner
from fcbyk.cli_support.output import get_display_width

from fcbyk.cli import main


def test_version_command():
    runner = CliRunner()
    result = runner.invoke(main, ['--version'])
    assert result.exit_code == 0
    assert 'v' in result.output


def test_lansend_command_help():
    runner = CliRunner()
    result = runner.invoke(main, ['lansend', '--help'])
    assert result.exit_code == 0
    assert 'Start a local web server for sharing files over LAN' in result.output


def test_config_command_lists_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    runner = CliRunner()
    result = runner.invoke(main, ['config'])

    assert result.exit_code == 0
    assert "数据目录:" in result.output
    assert "日志目录:" in result.output
    assert "配置文件:" in result.output


def test_run_command_list_aligns_mixed_language_names(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    scripts_file = tmp_path / "scripts.byk.json"
    scripts_file.write_text(
        (
            "{\n"
            '  "后端测试": "pytest -q",\n'
            '  "build": "python -m build",\n'
            '  "生成日志": "cz changelog --incremental"\n'
            "}\n"
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(main, ["run"])

    assert result.exit_code == 0

    script_lines = [line for line in result.output.splitlines() if "->" in line]
    assert len(script_lines) == 3

    arrow_columns = [get_display_width(line.split("->")[0]) for line in script_lines]
    assert len(set(arrow_columns)) == 1
