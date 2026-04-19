from __future__ import annotations

from unittest.mock import MagicMock, patch

from bykcli.core.environment import EnvironmentInfo
from bykcli.infra.view import (
    _get_status_symbol,
    format_version_line,
    render_dashboard,
)


class TestFormatVersionLine:
    def test_format_version_line(self):
        env = EnvironmentInfo(
            app_name="testapp",
            version="1.0.0",
            python_version="3.11.0",
            platform_name="Linux",
            executable="/usr/bin/python",
        )
        result = format_version_line(env)
        from rich.text import Text
        assert isinstance(result, Text)
        plain_text = result.plain
        assert "v1.0.0" in plain_text
        assert "Python: 3.11.0" in plain_text
        assert "Platform: Linux" in plain_text


class TestGetStatusSymbol:
    def test_alive_symbol(self):
        assert _get_status_symbol(True) == "●"

    def test_dead_symbol(self):
        assert _get_status_symbol(False) == "○"


class TestRenderDashboard:
    @patch("bykcli.infra.view.render_alias_lines")
    @patch("bykcli.infra.view.list_daemons")
    def test_render_dashboard_basic(self, mock_list_daemons, mock_render_alias):
        """Test basic dashboard rendering without plugins section."""
        mock_render_alias.return_value = ["alias1: cmd1", "alias2: cmd2"]
        mock_list_daemons.return_value = []

        context = MagicMock()
        cli = MagicMock()
        cli.commands = {
            "test-cmd": MagicMock(get_short_help_str=MagicMock(return_value="Test command"))
        }

        from click.testing import CliRunner
        runner = CliRunner()

        with runner.isolation():
            render_dashboard(context, cli)

    @patch("bykcli.infra.view.render_alias_lines")
    @patch("bykcli.infra.view.list_daemons")
    def test_render_dashboard_no_aliases(self, mock_list_daemons, mock_render_alias):
        mock_render_alias.return_value = []
        mock_list_daemons.return_value = []

        context = MagicMock()
        cli = MagicMock()
        cli.commands = {}

        from click.testing import CliRunner
        runner = CliRunner()

        with runner.isolation():
            render_dashboard(context, cli)

    @patch("bykcli.infra.view.render_alias_lines")
    @patch("bykcli.infra.view.list_daemons")
    def test_render_dashboard_with_running_daemons(self, mock_list_daemons, mock_render_alias):
        mock_render_alias.return_value = []
        mock_list_daemons.return_value = [
            {"name": "test", "pid": 1234, "alive": True, "port": 8080},
        ]

        context = MagicMock()
        cli = MagicMock()
        cli.commands = {}

        from click.testing import CliRunner
        runner = CliRunner()

        with runner.isolation():
            render_dashboard(context, cli)

    @patch("bykcli.infra.view.render_alias_lines")
    @patch("bykcli.infra.view.list_daemons")
    def test_render_dashboard_with_stopped_daemons(self, mock_list_daemons, mock_render_alias):
        mock_render_alias.return_value = []
        mock_list_daemons.return_value = [
            {"name": "test", "pid": 1234, "alive": False, "port": None},
        ]

        context = MagicMock()
        cli = MagicMock()
        cli.commands = {}

        from click.testing import CliRunner
        runner = CliRunner()

        with runner.isolation():
            render_dashboard(context, cli)

    @patch("bykcli.infra.view.render_alias_lines")
    @patch("bykcli.infra.view.list_daemons")
    @patch("bykcli.infra.view.get_terminal_width")
    def test_render_dashboard_wrap_text(self, mock_get_width, mock_list_daemons, mock_render_alias):
        mock_render_alias.return_value = []
        mock_list_daemons.return_value = []
        mock_get_width.return_value = 40

        context = MagicMock()
        cli = MagicMock()
        cli.commands = {}

        from click.testing import CliRunner
        runner = CliRunner()

        with runner.isolation():
            render_dashboard(context, cli)

    @patch("bykcli.infra.view.plugin_load_errors")
    @patch("bykcli.infra.view.render_alias_lines")
    @patch("bykcli.infra.view.list_daemons")
    def test_render_dashboard_with_plugin_errors(self, mock_list_daemons, mock_render_alias, mock_plugin_errors):
        mock_plugin_errors.__iter__ = MagicMock(return_value=iter([
            ("failed-plugin", "ModuleNotFoundError: No module named 'xxx'"),
            ("another-failed", "ImportError: cannot import name 'yyy'")
        ]))
        mock_render_alias.return_value = []
        mock_list_daemons.return_value = []

        context = MagicMock()
        cli = MagicMock()
        cli.commands = {}

        from click.testing import CliRunner
        runner = CliRunner()

        with runner.isolation():
            render_dashboard(context, cli)
