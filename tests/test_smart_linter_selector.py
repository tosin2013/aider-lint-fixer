import pytest
from aider_lint_fixer.smart_linter_selector import SmartLinterSelector, LinterSelectionResult
from aider_lint_fixer.project_detector import ProjectInfo
from pathlib import Path

@pytest.fixture
def basic_python_project():
    return ProjectInfo(
        root_path=Path("/fake/path"),
        languages={"python"},
        source_files=[Path("main.py")],
    )

def test_select_linters_python(basic_python_project):
    selector = SmartLinterSelector(basic_python_project)
    available = {"flake8": True, "pylint": True, "black": True, "isort": True}
    result = selector.select_linters(available)
    assert isinstance(result, LinterSelectionResult)
    assert "flake8" in result.recommended_linters
    assert result.reasoning["flake8"].startswith("Selected")

def test_select_linters_max_limit(basic_python_project):
    selector = SmartLinterSelector(basic_python_project)
    available = {"flake8": True, "pylint": True, "black": True, "isort": True}
    result = selector.select_linters(available, max_linters=2)
    assert len(result.recommended_linters) == 2
    assert set(result.recommended_linters).issubset(set(available.keys()))

def test_select_linters_unavailable(basic_python_project):
    selector = SmartLinterSelector(basic_python_project)
    available = {"flake8": False, "pylint": False, "black": False, "isort": False}
    result = selector.select_linters(available)
    assert len(result.recommended_linters) == 0 or all(not available[l] for l in result.recommended_linters)

def test_select_linters_fallback():
    project = ProjectInfo(root_path=Path("/fake/path"), languages={"python"}, source_files=[Path("main.py")])
    selector = SmartLinterSelector(project)
    available = {"flake8": False, "eslint": True, "pylint": False}
    result = selector.select_linters(available)
    assert "eslint" in result.recommended_linters

def test_prioritize_linters_fast(basic_python_project):
    selector = SmartLinterSelector(basic_python_project)
    linters = {"flake8", "pylint", "black", "isort"}
    prioritized = selector._prioritize_linters(linters, prefer_fast=True)
    assert prioritized[0] == "flake8"
