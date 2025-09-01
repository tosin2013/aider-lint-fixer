import pytest
from click.testing import CliRunner
from aider_lint_fixer.main import main

def test_main_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output.lower() or result.output.strip() != ""
