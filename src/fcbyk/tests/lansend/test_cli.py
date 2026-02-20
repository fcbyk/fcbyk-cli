import importlib


def test_lansend_help():
    from click.testing import CliRunner
    from fcbyk.cli import main

    r = CliRunner().invoke(main, ["lansend", "--help"])
    assert r.exit_code == 0
