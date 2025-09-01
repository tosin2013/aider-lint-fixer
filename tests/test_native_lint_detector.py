import pytest
from aider_lint_fixer.native_lint_detector import NativeLintDetector, NativeLintCommand
from pathlib import Path
import tempfile
import os

@pytest.fixture
def fake_project_root(tmp_path):
    # Create a fake project root with minimal structure
    (tmp_path / "package.json").write_text('{"scripts": {"lint": "eslint ."}}')
    (tmp_path / "pyproject.toml").write_text('[tool.poetry.scripts]\nlint = "flake8"')
    (tmp_path / "tox.ini").write_text('[testenv:lint]\ncommands = flake8')
    (tmp_path / "Makefile").write_text('lint:\n\tflake8 .')
    return str(tmp_path)

def test_detect_all_native_lint_commands(fake_project_root):
    detector = NativeLintDetector(fake_project_root)
    commands = detector.detect_all_native_lint_commands()
    assert isinstance(commands, dict)
    assert any(isinstance(cmd, NativeLintCommand) for cmd in commands.values())
    # Check that at least one expected linter is detected
    assert any(linter in commands for linter in ["eslint", "flake8", "pylint"])

def test_identify_linter_from_script():
    detector = NativeLintDetector("/")
    assert detector._identify_linter_from_script("eslint .") == "eslint"
    assert detector._identify_linter_from_script("flake8 .") == "flake8"
    assert detector._identify_linter_from_script("pylint src/") == "pylint"
    assert detector._identify_linter_from_script("unknowncmd") is None

def test_get_baseline_command(fake_project_root):
    detector = NativeLintDetector(fake_project_root)
    commands = detector.detect_all_native_lint_commands()
    for linter in ["eslint", "flake8"]:
        cmd = detector.get_baseline_command(linter)
        if cmd:
            assert isinstance(cmd, NativeLintCommand)
            assert cmd.linter_type == linter

def test_test_native_command(fake_project_root):
    detector = NativeLintDetector(fake_project_root)
    commands = detector.detect_all_native_lint_commands()
    for cmd in commands.values():
        # This will likely fail but should not crash
        success, output = detector.test_native_command(cmd)
        assert isinstance(success, bool)
        assert isinstance(output, str)
