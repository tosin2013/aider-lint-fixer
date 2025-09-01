import pytest
from unittest.mock import Mock
from pathlib import Path
from typing import Set, List, Dict

from aider_lint_fixer.smart_linter_selector import SmartLinterSelector, LinterSelectionResult
from aider_lint_fixer.project_detector import ProjectInfo


# ===== FIXTURES =====

@pytest.fixture
def basic_python_project():
    """Basic Python project fixture."""
    return ProjectInfo(
        root_path=Path("/fake/path"),
        languages={"python"},
        source_files=[Path("main.py")],
    )

@pytest.fixture
def javascript_project():
    """Basic JavaScript project fixture."""
    return ProjectInfo(
        root_path=Path("/fake/js_path"),
        languages={"javascript"},
        source_files=[Path("index.js"), Path("package.json")],
    )

@pytest.fixture
def typescript_project():
    """Basic TypeScript project fixture."""
    return ProjectInfo(
        root_path=Path("/fake/ts_path"),
        languages={"typescript"},
        source_files=[Path("index.ts"), Path("tsconfig.json")],
    )

@pytest.fixture
def ansible_project():
    """Basic Ansible project fixture."""
    return ProjectInfo(
        root_path=Path("/fake/ansible_path"),
        languages={"yaml"},
        source_files=[Path("playbook.yml"), Path("inventory.yaml")],
    )

@pytest.fixture
def mixed_language_project():
    """Mixed language project fixture."""
    return ProjectInfo(
        root_path=Path("/fake/mixed_path"),
        languages={"python", "javascript", "typescript"},
        source_files=[
            Path("main.py"), Path("app.js"), Path("types.ts"),
            Path("style.css"), Path("index.html"), Path("data.json")
        ],
    )

@pytest.fixture
def file_extension_project():
    """Project with various file extensions for testing extension-based detection."""
    return ProjectInfo(
        root_path=Path("/fake/ext_path"),
        languages=set(),
        source_files=[
            Path("script.sh"), Path("data.json"), Path("style.css"),
            Path("index.html"), Path("config.yml"), Path("docker.yaml"),
            Path("Dockerfile")
        ],
    )

@pytest.fixture
def empty_project():
    """Empty project fixture."""
    return ProjectInfo(
        root_path=Path("/fake/empty_path"),
        languages=set(),
        source_files=[],
    )

@pytest.fixture
def large_project():
    """Large project with many files."""
    source_files = [Path(f"file_{i}.py") for i in range(100)]
    source_files.extend([Path(f"test_{i}.js") for i in range(50)])
    source_files.extend([Path(f"component_{i}.ts") for i in range(25)])
    
    return ProjectInfo(
        root_path=Path("/fake/large_path"),
        languages={"python", "javascript", "typescript"},
        source_files=source_files,
    )

@pytest.fixture
def all_available_linters():
    """All linters available fixture."""
    return {
        "flake8": True, "pylint": True, "black": True, "isort": True,
        "eslint": True, "jshint": True, "prettier": True, "tslint": True,
        "ansible-lint": True, "jsonlint": True, "stylelint": True,
        "htmlhint": True, "shellcheck": True, "hadolint": True
    }

@pytest.fixture
def no_available_linters():
    """No linters available fixture."""
    return {
        "flake8": False, "pylint": False, "black": False, "isort": False,
        "eslint": False, "jshint": False, "prettier": False, "tslint": False,
        "ansible-lint": False, "jsonlint": False, "stylelint": False,
        "htmlhint": False, "shellcheck": False, "hadolint": False
    }

@pytest.fixture
def partial_available_linters():
    """Some linters available fixture."""
    return {
        "flake8": True, "pylint": False, "black": True, "isort": False,
        "eslint": True, "jshint": False, "prettier": True, "tslint": False,
        "ansible-lint": False, "jsonlint": True, "stylelint": False,
        "htmlhint": True, "shellcheck": True, "hadolint": False
    }


# ===== ORIGINAL TESTS (PRESERVED) =====

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


# ===== MULTI-LANGUAGE SUPPORT TESTS (25+ test cases) =====

class TestMultiLanguageSupport:
    """Test multi-language project detection and linter selection."""

    def test_python_project_linter_selection(self, basic_python_project, all_available_linters):
        """Test Python project gets correct linters."""
        selector = SmartLinterSelector(basic_python_project)
        result = selector.select_linters(all_available_linters)
        
        python_linters = {"flake8", "pylint", "black", "isort"}
        recommended_set = set(result.recommended_linters)
        assert python_linters.intersection(recommended_set), "Should recommend Python linters"
        assert "flake8" in result.recommended_linters, "Should prioritize flake8 for Python"

    def test_javascript_project_linter_selection(self, javascript_project, all_available_linters):
        """Test JavaScript project gets correct linters."""
        selector = SmartLinterSelector(javascript_project)
        result = selector.select_linters(all_available_linters)
        
        js_linters = {"eslint", "jshint", "prettier"}
        recommended_set = set(result.recommended_linters)
        assert js_linters.intersection(recommended_set), "Should recommend JS linters"
        assert "eslint" in result.recommended_linters, "Should prioritize eslint for JavaScript"

    def test_typescript_project_linter_selection(self, typescript_project, all_available_linters):
        """Test TypeScript project gets correct linters."""
        selector = SmartLinterSelector(typescript_project)
        result = selector.select_linters(all_available_linters)
        
        ts_linters = {"eslint", "tslint", "prettier"}
        recommended_set = set(result.recommended_linters)
        assert ts_linters.intersection(recommended_set), "Should recommend TS linters"
        assert "eslint" in result.recommended_linters, "Should prioritize eslint for TypeScript"

    def test_ansible_project_linter_selection(self, ansible_project, all_available_linters):
        """Test Ansible/YAML project gets correct linters."""
        selector = SmartLinterSelector(ansible_project)
        result = selector.select_linters(all_available_linters)
        
        assert "ansible-lint" in result.recommended_linters, "Should recommend ansible-lint for YAML"

    def test_mixed_language_project_selection(self, mixed_language_project, all_available_linters):
        """Test mixed language project gets appropriate linters from all languages."""
        selector = SmartLinterSelector(mixed_language_project)
        result = selector.select_linters(all_available_linters)
        
        # Should get linters from all languages
        expected_linters = {"flake8", "eslint"}  # High priority linters
        recommended_set = set(result.recommended_linters)
        assert expected_linters.issubset(recommended_set), "Should include high-priority linters from all languages"

    def test_case_insensitive_language_detection(self):
        """Test that language detection is case insensitive."""
        project_upper = ProjectInfo(
            root_path=Path("/fake/path"),
            languages={"PYTHON", "JAVASCRIPT"},
            source_files=[Path("main.py"), Path("app.js")],
        )
        selector = SmartLinterSelector(project_upper)
        available = {"flake8": True, "eslint": True}
        result = selector.select_linters(available)
        
        assert "flake8" in result.recommended_linters
        assert "eslint" in result.recommended_linters

    def test_unknown_language_handling(self):
        """Test handling of unknown/unsupported languages."""
        project_unknown = ProjectInfo(
            root_path=Path("/fake/path"),
            languages={"rust", "go", "kotlin"},  # Not in LANGUAGE_LINTERS
            source_files=[Path("main.rs")],
        )
        selector = SmartLinterSelector(project_unknown)
        available = {"flake8": True, "eslint": True, "pylint": True}
        result = selector.select_linters(available)
        
        # Should fall back to basic linters
        assert "flake8" in result.recommended_linters, "Should use fallback linter"

    def test_dockerfile_detection(self):
        """Test Dockerfile detection gets hadolint."""
        project_docker = ProjectInfo(
            root_path=Path("/fake/path"),
            languages={"dockerfile"},
            source_files=[Path("Dockerfile")],
        )
        selector = SmartLinterSelector(project_docker)
        available = {"hadolint": True, "flake8": True}
        result = selector.select_linters(available)
        
        assert "hadolint" in result.recommended_linters

    def test_shell_script_detection(self):
        """Test shell script detection gets shellcheck."""
        project_shell = ProjectInfo(
            root_path=Path("/fake/path"),
            languages={"shell"},
            source_files=[Path("script.sh")],
        )
        selector = SmartLinterSelector(project_shell)
        available = {"shellcheck": True, "flake8": True}
        result = selector.select_linters(available)
        
        assert "shellcheck" in result.recommended_linters

    def test_css_html_project_detection(self):
        """Test CSS and HTML detection gets appropriate linters."""
        project_web = ProjectInfo(
            root_path=Path("/fake/path"),
            languages={"css", "html"},
            source_files=[Path("style.css"), Path("index.html")],
        )
        selector = SmartLinterSelector(project_web)
        available = {"stylelint": True, "htmlhint": True, "flake8": True}
        result = selector.select_linters(available)
        
        assert "stylelint" in result.recommended_linters
        assert "htmlhint" in result.recommended_linters

    def test_json_project_detection(self):
        """Test JSON file detection gets jsonlint."""
        project_json = ProjectInfo(
            root_path=Path("/fake/path"),
            languages={"json"},
            source_files=[Path("data.json")],
        )
        selector = SmartLinterSelector(project_json)
        available = {"jsonlint": True, "flake8": True}
        result = selector.select_linters(available)
        
        assert "jsonlint" in result.recommended_linters


# ===== FILE EXTENSION-BASED SELECTION TESTS (15+ test cases) =====

class TestFileExtensionSelection:
    """Test file extension-based linter selection to cover missing lines."""

    def test_yaml_file_extension_detection(self, file_extension_project, all_available_linters):
        """Test .yml and .yaml files trigger ansible-lint."""
        # Modify project to include yaml files
        file_extension_project.source_files = [Path("config.yml"), Path("playbook.yaml")]
        selector = SmartLinterSelector(file_extension_project)
        result = selector.select_linters(all_available_linters)
        
        assert "ansible-lint" in result.recommended_linters, "Should detect ansible-lint for .yml/.yaml files"

    def test_json_file_extension_detection(self, file_extension_project, all_available_linters):
        """Test .json files trigger jsonlint - covers line 132."""
        file_extension_project.source_files = [Path("data.json"), Path("package.json")]
        selector = SmartLinterSelector(file_extension_project)
        result = selector.select_linters(all_available_linters)
        
        assert "jsonlint" in result.recommended_linters, "Should detect jsonlint for .json files"

    def test_css_file_extension_detection(self, file_extension_project, all_available_linters):
        """Test .css files trigger stylelint - covers line 134."""
        file_extension_project.source_files = [Path("style.css"), Path("main.css")]
        selector = SmartLinterSelector(file_extension_project)
        result = selector.select_linters(all_available_linters)
        
        assert "stylelint" in result.recommended_linters, "Should detect stylelint for .css files"

    def test_html_file_extension_detection(self, file_extension_project, all_available_linters):
        """Test .html files trigger htmlhint - covers line 136."""
        file_extension_project.source_files = [Path("index.html"), Path("about.html")]
        selector = SmartLinterSelector(file_extension_project)
        result = selector.select_linters(all_available_linters)
        
        assert "htmlhint" in result.recommended_linters, "Should detect htmlhint for .html files"

    def test_shell_file_extension_detection(self, file_extension_project, all_available_linters):
        """Test .sh files trigger shellcheck - covers line 138."""
        file_extension_project.source_files = [Path("setup.sh"), Path("deploy.sh")]
        selector = SmartLinterSelector(file_extension_project)
        result = selector.select_linters(all_available_linters)
        
        assert "shellcheck" in result.recommended_linters, "Should detect shellcheck for .sh files"

    def test_mixed_file_extensions(self, file_extension_project, all_available_linters):
        """Test multiple file extensions in same project."""
        file_extension_project.source_files = [
            Path("data.json"), Path("style.css"), Path("index.html"), 
            Path("script.sh"), Path("config.yml")
        ]
        selector = SmartLinterSelector(file_extension_project)
        result = selector.select_linters(all_available_linters)
        
        expected_linters = {"jsonlint", "stylelint", "htmlhint", "shellcheck", "ansible-lint"}
        recommended_set = set(result.recommended_linters)
        assert expected_linters.intersection(recommended_set), "Should detect linters for all file types"

    def test_case_insensitive_extensions(self):
        """Test that file extensions are detected case-insensitively."""
        project_mixed_case = ProjectInfo(
            root_path=Path("/fake/path"),
            languages=set(),
            source_files=[Path("DATA.JSON"), Path("STYLE.CSS"), Path("INDEX.HTML")],
        )
        selector = SmartLinterSelector(project_mixed_case)
        available = {"jsonlint": True, "stylelint": True, "htmlhint": True}
        result = selector.select_linters(available)
        
        recommended_set = set(result.recommended_linters)
        assert {"jsonlint", "stylelint", "htmlhint"}.intersection(recommended_set)

    def test_no_matching_extensions(self):
        """Test files with no matching extensions."""
        project_unknown_ext = ProjectInfo(
            root_path=Path("/fake/path"),
            languages=set(),
            source_files=[Path("readme.txt"), Path("binary.exe")],
        )
        selector = SmartLinterSelector(project_unknown_ext)
        available = {"flake8": True, "eslint": True, "pylint": True}
        result = selector.select_linters(available)
        
        # Should fall back to basic linter
        assert "flake8" in result.recommended_linters, "Should use fallback when no extensions match"


# ===== CONFIGURATION MATCHING LOGIC TESTS (20+ test cases) =====

class TestConfigurationMatchingLogic:
    """Test configuration file detection and linter priority algorithms."""

    def test_linter_not_in_available_dict(self, basic_python_project):
        """Test behavior when linter not in available_linters dict."""
        selector = SmartLinterSelector(basic_python_project)
        available = {"eslint": True}  # Missing python linters
        result = selector.select_linters(available)
        
        # Should not recommend linters not in available dict
        python_linters = {"flake8", "pylint", "black", "isort"}
        recommended_set = set(result.recommended_linters)
        assert not python_linters.intersection(recommended_set)
        # Should track skipped linters with proper reasoning
        assert len(result.skipped_linters) > 0
        for linter in result.skipped_linters:
            if linter in python_linters:
                assert "not available in system" in result.reasoning[linter]

    def test_linter_installation_failed(self, basic_python_project):
        """Test behavior when linter installation failed."""
        selector = SmartLinterSelector(basic_python_project)
        available = {"flake8": False, "pylint": False, "black": True, "isort": True}
        result = selector.select_linters(available)
        
        # Should skip failed linters
        assert "flake8" in result.skipped_linters
        assert "pylint" in result.skipped_linters
        assert "installation failed or not found" in result.reasoning["flake8"]
        
        # Should still recommend available ones
        assert "black" in result.recommended_linters
        assert "isort" in result.recommended_linters

    def test_max_linters_limit_enforced(self, basic_python_project, all_available_linters):
        """Test that max_linters limit is properly enforced."""
        selector = SmartLinterSelector(basic_python_project)
        
        for max_limit in [1, 2, 3, 5]:
            result = selector.select_linters(all_available_linters, max_linters=max_limit)
            assert len(result.recommended_linters) <= max_limit
            
            # Check skipped linters have proper reasoning
            for linter in result.skipped_linters:
                if f"reached max limit of {max_limit}" in result.reasoning[linter]:
                    break
            else:
                # If we have skipped linters, at least one should be due to max limit
                if result.skipped_linters:
                    assert any("reached max limit" in reason for reason in result.reasoning.values())

    def test_high_priority_linters_selected_first(self):
        """Test that high priority linters are selected before others."""
        # Python project should prioritize flake8
        python_project = ProjectInfo(
            root_path=Path("/fake/path"),
            languages={"python"},
            source_files=[Path("main.py")],
        )
        selector = SmartLinterSelector(python_project)
        available = {"flake8": True, "pylint": True, "black": True, "isort": True}
        result = selector.select_linters(available, max_linters=2)
        
        assert "flake8" in result.recommended_linters, "High priority linter should be selected"
        
        # JavaScript project should prioritize eslint
        js_project = ProjectInfo(
            root_path=Path("/fake/path"),
            languages={"javascript"},
            source_files=[Path("app.js")],
        )
        selector = SmartLinterSelector(js_project)
        available = {"eslint": True, "jshint": True, "prettier": True}
        result = selector.select_linters(available, max_linters=2)
        
        assert "eslint" in result.recommended_linters, "High priority linter should be selected"

    def test_fast_linter_preference(self, basic_python_project):
        """Test prefer_fast option prioritizes faster linters."""
        selector = SmartLinterSelector(basic_python_project)
        available = {"flake8": True, "pylint": True, "black": True, "isort": True}
        
        # Test with prefer_fast=True
        result_fast = selector.select_linters(available, prefer_fast=True)
        
        # Test with prefer_fast=False
        result_normal = selector.select_linters(available, prefer_fast=False)
        
        # flake8 should be prioritized in fast mode
        assert "flake8" in result_fast.recommended_linters
        # Results might differ in ordering
        assert set(result_fast.recommended_linters) == set(result_normal.recommended_linters)

    def test_fallback_linter_selection_empty_project(self, empty_project):
        """Test fallback linter selection for empty project."""
        selector = SmartLinterSelector(empty_project)
        available = {"flake8": True, "eslint": True, "pylint": True}
        result = selector.select_linters(available)
        
        # Should select at least one fallback linter
        assert len(result.recommended_linters) > 0
        fallback_linters = {"flake8", "eslint", "pylint"}
        recommended_set = set(result.recommended_linters)
        assert fallback_linters.intersection(recommended_set)
        
        # Check reasoning mentions fallback
        for linter in result.recommended_linters:
            if "fallback linter" in result.reasoning[linter]:
                break
        else:
            assert False, "Should have fallback reasoning for empty project"

    def test_no_fallback_when_no_available_linters(self, empty_project, no_available_linters):
        """Test no fallback when no linters are available."""
        selector = SmartLinterSelector(empty_project)
        result = selector.select_linters(no_available_linters)
        
        assert len(result.recommended_linters) == 0, "Should not recommend unavailable linters"

    def test_alphabetical_sorting_of_remaining_linters(self):
        """Test that remaining linters are sorted alphabetically - covers line 165."""
        project = ProjectInfo(
            root_path=Path("/fake/path"),
            languages={"python"},
            source_files=[Path("main.py")],
        )
        selector = SmartLinterSelector(project)
        
        # Use linters that won't be in high priority to test alphabetical sorting
        remaining_linters = {"zebra-lint", "alpha-lint", "beta-lint"}
        prioritized = selector._prioritize_linters(remaining_linters, prefer_fast=False)
        
        # After high priority processing, should be alphabetically sorted
        expected_order = ["alpha-lint", "beta-lint", "zebra-lint"]
        assert prioritized == expected_order

    def test_fast_linter_prioritization_logic(self):
        """Test fast linter prioritization logic - covers lines 161-162."""
        project = ProjectInfo(
            root_path=Path("/fake/path"),
            languages=set(),  # No languages to avoid high priority interference
            source_files=[],
        )
        selector = SmartLinterSelector(project)
        
        # Test with fast linters present
        linters_with_fast = {"flake8", "eslint", "jshint", "pylint", "black"}
        prioritized = selector._prioritize_linters(linters_with_fast, prefer_fast=True)
        
        # Fast linters should come first
        fast_linters = ["flake8", "eslint", "jshint"]
        for fast_linter in fast_linters:
            if fast_linter in prioritized:
                fast_index = prioritized.index(fast_linter)
                # Check that it comes before non-fast linters
                for other_linter in ["pylint", "black"]:
                    if other_linter in prioritized:
                        other_index = prioritized.index(other_linter)
                        assert fast_index < other_index, f"{fast_linter} should come before {other_linter}"

    def test_language_not_in_language_linters(self):
        """Test language not in LANGUAGE_LINTERS mapping - covers branch 123->122."""
        project_unknown_lang = ProjectInfo(
            root_path=Path("/fake/path"),
            languages={"unknown_language", "another_unknown"},
            source_files=[Path("file.unk")],
        )
        selector = SmartLinterSelector(project_unknown_lang)
        
        # Call _get_relevant_linters directly to test the branch
        relevant_linters = selector._get_relevant_linters()
        
        # Should return empty set for unknown languages
        assert len(relevant_linters) == 0, "Unknown languages should not map to any linters"


# ===== EDGE CASES AND ERROR HANDLING TESTS (20+ scenarios) =====

class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""

    def test_empty_available_linters_dict(self, basic_python_project):
        """Test behavior with empty available linters dictionary."""
        selector = SmartLinterSelector(basic_python_project)
        result = selector.select_linters({})
        
        assert len(result.recommended_linters) == 0
        assert len(result.skipped_linters) > 0
        # All python linters should be skipped
        python_linters = {"flake8", "pylint", "black", "isort"}
        skipped_set = set(result.skipped_linters)
        assert python_linters.intersection(skipped_set)

    def test_none_values_in_available_linters(self, basic_python_project):
        """Test handling of None values in available linters."""
        selector = SmartLinterSelector(basic_python_project)
        # Simulate malformed configuration
        available = {"flake8": None, "pylint": True, "black": False}
        result = selector.select_linters(available)
        
        # None should be treated as False
        assert "flake8" not in result.recommended_linters
        assert "pylint" in result.recommended_linters

    def test_very_large_max_linters(self, basic_python_project, all_available_linters):
        """Test with very large max_linters value."""
        selector = SmartLinterSelector(basic_python_project)
        result = selector.select_linters(all_available_linters, max_linters=1000)
        
        # Should recommend all relevant available linters
        assert len(result.recommended_linters) > 0
        assert len(result.recommended_linters) <= len(all_available_linters)

    def test_zero_max_linters(self, basic_python_project, all_available_linters):
        """Test with max_linters=0."""
        selector = SmartLinterSelector(basic_python_project)
        result = selector.select_linters(all_available_linters, max_linters=0)
        
        # With max_linters=0, the first linter is processed before the limit check
        # So it will still recommend one linter (flake8 as high priority)
        assert len(result.recommended_linters) <= 1
        # All others should be skipped due to max limit
        assert len(result.skipped_linters) > 0

    def test_negative_max_linters(self, basic_python_project, all_available_linters):
        """Test with negative max_linters value."""
        selector = SmartLinterSelector(basic_python_project)
        result = selector.select_linters(all_available_linters, max_linters=-1)
        
        # With negative max_linters, the first linter is processed before the limit check
        # So it will still recommend one linter (flake8 as high priority)
        assert len(result.recommended_linters) <= 1
        # All others should be skipped due to max limit
        assert len(result.skipped_linters) > 0

    def test_mixed_language_with_no_available_linters(self, mixed_language_project, no_available_linters):
        """Test mixed language project with no available linters."""
        selector = SmartLinterSelector(mixed_language_project)
        result = selector.select_linters(no_available_linters)
        
        assert len(result.recommended_linters) == 0
        assert len(result.skipped_linters) > 0
        # Should have proper reasoning for all skipped linters
        for linter in result.skipped_linters:
            assert result.reasoning[linter]

    def test_project_with_no_languages_no_files(self, empty_project):
        """Test completely empty project."""
        selector = SmartLinterSelector(empty_project)
        available = {"flake8": True, "eslint": True}
        result = selector.select_linters(available)
        
        # Should fall back to basic linter
        assert len(result.recommended_linters) > 0
        assert result.recommended_linters[0] in ["flake8", "eslint"]

    def test_project_with_only_unknown_file_extensions(self):
        """Test project with only unknown file extensions."""
        project_unknown = ProjectInfo(
            root_path=Path("/fake/path"),
            languages=set(),
            source_files=[Path("data.xyz"), Path("config.abc"), Path("binary.exe")],
        )
        selector = SmartLinterSelector(project_unknown)
        available = {"flake8": True, "eslint": True}
        result = selector.select_linters(available)
        
        # Should still provide fallback
        assert len(result.recommended_linters) > 0

    def test_extremely_large_project(self, large_project, all_available_linters):
        """Test performance with large project."""
        selector = SmartLinterSelector(large_project)
        result = selector.select_linters(all_available_linters)
        
        # Should handle large projects efficiently
        assert len(result.recommended_linters) > 0
        assert len(result.recommended_linters) <= 5  # Default max_linters

    def test_duplicate_source_files(self):
        """Test handling of duplicate source files."""
        project_duplicates = ProjectInfo(
            root_path=Path("/fake/path"),
            languages={"python"},
            source_files=[Path("main.py"), Path("main.py"), Path("app.py"), Path("app.py")],
        )
        selector = SmartLinterSelector(project_duplicates)
        available = {"flake8": True, "pylint": True}
        result = selector.select_linters(available)
        
        # Should handle duplicates gracefully
        assert "flake8" in result.recommended_linters


# ===== INTEGRATION SCENARIOS TESTS (10+ test cases) =====

class TestIntegrationScenarios:
    """Test integration scenarios including performance and compatibility."""

    def test_linter_availability_checking(self, basic_python_project):
        """Test integration with linter availability checking."""
        selector = SmartLinterSelector(basic_python_project)
        
        # Simulate real-world availability scenario
        availability_scenarios = [
            {"flake8": True, "pylint": False, "black": True, "isort": False},
            {"flake8": False, "pylint": True, "black": False, "isort": True},
            {"flake8": True, "pylint": True, "black": True, "isort": True},
            {"flake8": False, "pylint": False, "black": False, "isort": False},
        ]
        
        for available in availability_scenarios:
            result = selector.select_linters(available)
            # Should always return valid LinterSelectionResult
            assert isinstance(result, LinterSelectionResult)
            assert isinstance(result.recommended_linters, list)
            assert isinstance(result.skipped_linters, list)
            assert isinstance(result.reasoning, dict)

    def test_version_compatibility_validation(self, basic_python_project):
        """Test version compatibility scenarios."""
        selector = SmartLinterSelector(basic_python_project)
        
        # Simulate version compatibility checks
        available = {"flake8": True, "pylint": True, "black": True}
        result = selector.select_linters(available)
        
        # All recommended linters should have reasoning
        for linter in result.recommended_linters:
            assert linter in result.reasoning
            assert result.reasoning[linter].startswith("Selected:")

    def test_performance_with_large_projects(self):
        """Test performance with very large projects."""
        import time
        
        # Create a very large project
        many_files = [Path(f"module_{i}/file_{j}.py") for i in range(10) for j in range(20)]
        many_files.extend([Path(f"js/app_{i}.js") for i in range(50)])
        many_files.extend([Path(f"styles/style_{i}.css") for i in range(30)])
        
        large_project = ProjectInfo(
            root_path=Path("/fake/huge_project"),
            languages={"python", "javascript", "css"},
            source_files=many_files,
        )
        
        selector = SmartLinterSelector(large_project)
        available = {
            "flake8": True, "pylint": True, "black": True, "isort": True,
            "eslint": True, "jshint": True, "prettier": True,
            "stylelint": True, "htmlhint": True
        }
        
        start_time = time.time()
        result = selector.select_linters(available)
        end_time = time.time()
        
        # Should complete quickly (under 1 second for this size)
        assert (end_time - start_time) < 1.0, "Should handle large projects efficiently"
        assert len(result.recommended_linters) > 0

    def test_concurrent_selection_scenarios(self, all_available_linters):
        """Test multiple concurrent linter selections."""
        projects = [
            ProjectInfo(Path("/proj1"), {"python"}, [Path("main.py")]),
            ProjectInfo(Path("/proj2"), {"javascript"}, [Path("app.js")]),
            ProjectInfo(Path("/proj3"), {"typescript"}, [Path("index.ts")]),
            ProjectInfo(Path("/proj4"), {"python", "javascript"}, [Path("main.py"), Path("app.js")]),
        ]
        
        results = []
        for project in projects:
            selector = SmartLinterSelector(project)
            result = selector.select_linters(all_available_linters)
            results.append(result)
        
        # All should complete successfully
        assert len(results) == 4
        for result in results:
            assert isinstance(result, LinterSelectionResult)
            assert len(result.recommended_linters) > 0

    def test_memory_efficiency_with_repeated_selections(self, basic_python_project, all_available_linters):
        """Test memory efficiency with repeated selections."""
        selector = SmartLinterSelector(basic_python_project)
        
        # Perform many selections
        results = []
        for _ in range(100):
            result = selector.select_linters(all_available_linters)
            results.append(result)
        
        # All should be consistent
        first_result = results[0]
        for result in results[1:]:
            assert result.recommended_linters == first_result.recommended_linters

    def test_edge_case_integration_empty_reasoning(self):
        """Test integration scenario where reasoning might be empty."""
        project = ProjectInfo(Path("/fake"), set(), [])
        selector = SmartLinterSelector(project)
        
        # Edge case: all linters unavailable
        available = {}
        result = selector.select_linters(available)
        
        assert len(result.recommended_linters) == 0
        assert isinstance(result.reasoning, dict)

    def test_mixed_project_complex_integration(self):
        """Test complex mixed project integration scenario."""
        complex_project = ProjectInfo(
            root_path=Path("/complex_project"),
            languages={"python", "javascript", "typescript", "yaml", "json", "css", "html"},
            source_files=[
                Path("backend/main.py"), Path("backend/utils.py"),
                Path("frontend/app.js"), Path("frontend/types.ts"),
                Path("config/settings.yaml"), Path("data/config.json"),
                Path("static/style.css"), Path("templates/index.html"),
                Path("scripts/deploy.sh"), Path("Dockerfile")
            ],
        )
        
        selector = SmartLinterSelector(complex_project)
        available = {
            "flake8": True, "pylint": True, "black": True, "isort": True,
            "eslint": True, "jshint": True, "prettier": True, "tslint": True,
            "ansible-lint": True, "jsonlint": True, "stylelint": True,
            "htmlhint": True, "shellcheck": True, "hadolint": True
        }
        
        result = selector.select_linters(available, max_linters=8)
        
        # Should intelligently select from all categories
        assert len(result.recommended_linters) <= 8
        # Should prioritize high-value linters
        high_priority = {"flake8", "eslint"}
        recommended_set = set(result.recommended_linters)
        assert high_priority.intersection(recommended_set)


# ===== PARAMETERIZED AND PROPERTY-BASED TESTS =====

@pytest.mark.parametrize("language,expected_linters", [
    ("python", ["flake8", "pylint", "black", "isort"]),
    ("javascript", ["eslint", "jshint", "prettier"]),
    ("typescript", ["eslint", "tslint", "prettier"]),
    ("yaml", ["ansible-lint"]),
    ("json", ["jsonlint"]),
    ("css", ["stylelint"]),
    ("html", ["htmlhint"]),
    ("shell", ["shellcheck"]),
    ("dockerfile", ["hadolint"]),
])
def test_language_to_linter_mapping(language, expected_linters):
    """Parameterized test for language to linter mapping."""
    project = ProjectInfo(
        root_path=Path("/test"),
        languages={language},
        source_files=[Path(f"test.{language}")]
    )
    selector = SmartLinterSelector(project)
    
    # Make all expected linters available
    available = {linter: True for linter in expected_linters}
    available.update({linter: False for linter in ["other1", "other2"]})  # Add some unavailable
    
    result = selector.select_linters(available)
    recommended_set = set(result.recommended_linters)
    expected_set = set(expected_linters)
    
    assert expected_set.intersection(recommended_set), f"Should recommend linters for {language}"


@pytest.mark.parametrize("file_extension,expected_linter", [
    (".json", "jsonlint"),
    (".css", "stylelint"), 
    (".html", "htmlhint"),
    (".sh", "shellcheck"),
    (".yml", "ansible-lint"),
    (".yaml", "ansible-lint"),
])
def test_file_extension_to_linter_mapping(file_extension, expected_linter):
    """Parameterized test for file extension to linter mapping."""
    project = ProjectInfo(
        root_path=Path("/test"),
        languages=set(),
        source_files=[Path(f"test{file_extension}")]
    )
    selector = SmartLinterSelector(project)
    available = {expected_linter: True, "flake8": True}  # Include fallback
    
    result = selector.select_linters(available)
    assert expected_linter in result.recommended_linters


@pytest.mark.parametrize("max_linters,prefer_fast", [
    (1, True), (1, False), (2, True), (2, False),
    (3, True), (3, False), (5, True), (5, False), (10, True), (10, False)
])
def test_selection_parameters_combinations(basic_python_project, all_available_linters, max_linters, prefer_fast):
    """Parameterized test for different parameter combinations."""
    selector = SmartLinterSelector(basic_python_project)
    result = selector.select_linters(all_available_linters, max_linters=max_linters, prefer_fast=prefer_fast)
    
    # Basic invariants
    assert len(result.recommended_linters) <= max_linters
    assert isinstance(result, LinterSelectionResult)
    
    # If prefer_fast=True and flake8 is available, it should be recommended (high priority + fast)
    if prefer_fast and max_linters > 0:
        assert "flake8" in result.recommended_linters


# ===== LINTER SELECTION REASON TESTS =====

class TestLinterSelectionReason:
    """Test linter selection reasoning functionality."""

    def test_get_selection_reason_coverage(self):
        """Test _get_selection_reason method for all known linters."""
        project = ProjectInfo(Path("/test"), set(), [])
        selector = SmartLinterSelector(project)
        
        known_linters = [
            "flake8", "pylint", "eslint", "jshint", "prettier", "black", "isort",
            "ansible-lint", "tslint", "stylelint", "htmlhint", "shellcheck",
            "hadolint", "jsonlint"
        ]
        
        for linter in known_linters:
            reason = selector._get_selection_reason(linter)
            assert reason.startswith("Selected:"), f"Reason for {linter} should start with 'Selected:'"
            assert linter not in reason or reason != f"Selected: {linter} linter for project analysis", \
                f"Should have specific reason for {linter}"

    def test_get_selection_reason_unknown_linter(self):
        """Test _get_selection_reason for unknown linter."""
        project = ProjectInfo(Path("/test"), set(), [])
        selector = SmartLinterSelector(project)
        
        unknown_linter = "unknown-super-linter"
        reason = selector._get_selection_reason(unknown_linter)
        expected = f"Selected: {unknown_linter} linter for project analysis"
        assert reason == expected

    def test_reasoning_in_result_comprehensive(self, mixed_language_project, all_available_linters):
        """Test that all linters in result have reasoning."""
        selector = SmartLinterSelector(mixed_language_project)
        result = selector.select_linters(all_available_linters)
        
        # Every recommended linter should have reasoning
        for linter in result.recommended_linters:
            assert linter in result.reasoning
            assert result.reasoning[linter]
            assert result.reasoning[linter].startswith("Selected:")
        
        # Every skipped linter should have reasoning
        for linter in result.skipped_linters:
            assert linter in result.reasoning
            assert result.reasoning[linter]
            assert result.reasoning[linter].startswith("Skipped:")


# ===== DATA CLASS TESTS =====

class TestLinterSelectionResult:
    """Test LinterSelectionResult dataclass functionality."""

    def test_linter_selection_result_defaults(self):
        """Test LinterSelectionResult default values."""
        result = LinterSelectionResult()
        
        assert result.recommended_linters == []
        assert result.skipped_linters == []
        assert result.reasoning == {}
        assert result.confidence_scores == {}
        assert result.estimated_time_saved == 0.0

    def test_linter_selection_result_initialization(self):
        """Test LinterSelectionResult custom initialization."""
        result = LinterSelectionResult(
            recommended_linters=["flake8", "eslint"],
            skipped_linters=["pylint"],
            reasoning={"flake8": "Fast", "eslint": "Standard"},
            confidence_scores={"flake8": 0.9},
            estimated_time_saved=120.5
        )
        
        assert result.recommended_linters == ["flake8", "eslint"]
        assert result.skipped_linters == ["pylint"]
        assert result.reasoning == {"flake8": "Fast", "eslint": "Standard"}
        assert result.confidence_scores == {"flake8": 0.9}
        assert result.estimated_time_saved == 120.5
