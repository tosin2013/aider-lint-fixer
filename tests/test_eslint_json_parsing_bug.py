"""
Test cases that reproduce the ESLint JSON parsing bug described in issue #57.

This test file specifically tests the bug where ESLint JSON output parsing fails 
when the output contains npm script headers or trailing text.
"""

import tempfile
import json
from pathlib import Path
from aider_lint_fixer.linters.eslint_linter import ESLintLinter
from aider_lint_fixer.lint_runner import LintRunner
from aider_lint_fixer.project_detector import ProjectInfo


class TestESLintJSONParsingBug:
    """Test the specific JSON parsing bug with npm script output."""

    def test_npm_output_with_headers_and_footers_now_works_correctly(self):
        """Test that current parsing correctly handles npm output containing headers and footers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))

            # This is the exact output format that used to break the parser
            npm_output_with_footer = """
> project@1.0.0 lint:json /path/to/project
> eslint . --format json

[{"filePath":"test.js","messages":[{"ruleId":"no-unused-vars","severity":2,"message":"'x' is defined but never used.","line":1,"column":7}]}]

npm timing info execution time: 1234ms
npm notice cleanup complete
"""

            # After the fix, should extract only the JSON correctly
            json_output = linter._extract_json_from_output(npm_output_with_footer)
            
            # Should NOT include the npm timing info
            assert "npm timing info" not in json_output, "Fixed implementation should exclude trailing text"
            assert json_output == '[{"filePath":"test.js","messages":[{"ruleId":"no-unused-vars","severity":2,"message":"\'x\' is defined but never used.","line":1,"column":7}]}]'

    def test_multi_line_json_with_npm_wrapper_now_works(self):
        """Test multi-line JSON with npm wrapper text now works correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))

            # Multi-line formatted JSON with npm wrapper
            npm_output_multiline = """
> test-project@1.0.0 lint
> eslint . --format json

[
  {
    "filePath": "/path/to/file.js",
    "messages": [
      {
        "ruleId": "no-unused-vars",
        "severity": 2,
        "message": "'variable' is defined but never used.",
        "line": 10,
        "column": 5
      }
    ]
  }
]

npm timing info...
other output...
"""

            json_output = linter._extract_json_from_output(npm_output_multiline)
            
            # After fix, should extract only the JSON, excluding trailing text
            assert json_output.startswith("["), "Should start with JSON array"
            assert "npm timing info" not in json_output, "Fixed implementation should exclude trailing text"
            
            # Should be valid JSON
            data = json.loads(json_output)
            assert len(data) == 1
            assert data[0]["filePath"] == "/path/to/file.js"

    def test_nested_arrays_and_escaped_quotes_now_work(self):
        """Test JSON with nested arrays and escaped quotes now works correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))

            # JSON with nested arrays and escaped quotes
            npm_output_complex = """
> project@1.0.0 lint
> eslint . --format json

[{"filePath":"test.js","messages":[{"data":["item1","item2"],"message":"Use \\"quotes\\" properly","ruleId":"quotes","severity":1}]}]

npm timing complete
"""

            json_output = linter._extract_json_from_output(npm_output_complex)
            
            # Should NOT include the trailing npm text after fix
            assert "npm timing complete" not in json_output, "Fixed implementation should exclude trailing text"
            
            # Should correctly parse nested structures and escaped quotes
            data = json.loads(json_output)
            assert len(data) == 1
            message = data[0]["messages"][0]
            assert message["data"] == ["item1", "item2"]
            assert message["message"] == 'Use "quotes" properly'
            assert message["ruleId"] == "quotes"

    def test_lint_runner_direct_json_parsing_now_works(self):
        """Test that LintRunner._parse_eslint_json_output now works with npm output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            project_info = ProjectInfo(root_path=project_root, languages=["javascript"])
            runner = LintRunner(project_info=project_info)

            # npm output with valid JSON but extra text (empty messages for this test)
            npm_stdout = """
> project@1.0.0 lint
> eslint . --format json

[{"filePath":"test.js","messages":[]}]

npm timing info...
"""

            # After the fix, this should work correctly and return no errors/warnings
            result = runner._parse_eslint_json_output(npm_stdout, "", 0)
            
            # Should successfully parse with no errors or warnings (empty messages)
            assert len(result.errors) == 0, f"Expected no errors, got: {result.errors}"
            assert len(result.warnings) == 0, f"Expected no warnings, got: {result.warnings}"
            assert result.success == True

    def test_lint_runner_generic_json_parsing_now_works(self):
        """Test that LintRunner._parse_json_output now works with npm output for ESLint."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            project_info = ProjectInfo(root_path=project_root, languages=["javascript"])
            runner = LintRunner(project_info=project_info)

            # npm output with valid JSON but extra text (empty messages for this test)
            npm_output = """
> project@1.0.0 lint
> eslint . --format json

[{"filePath":"test.js","messages":[]}]

npm timing info...
"""

            # After the fix, this should work correctly  
            errors, warnings = runner._parse_json_output("eslint", npm_output)
            
            # Should successfully parse with no errors or warnings (empty messages)
            assert len(errors) == 0, f"Expected no errors, got: {errors}"
            assert len(warnings) == 0, f"Expected no warnings, got: {warnings}"


class TestExpectedBehaviorAfterFix:
    """Test cases that define the expected behavior after the bug is fixed."""

    def test_should_extract_clean_json_from_npm_output(self):
        """Test that JSON extraction should only include the JSON array, not trailing text."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))
            
            npm_output = """
> project@1.0.0 lint
> eslint . --format json

[{"filePath":"test.js","messages":[]}]

npm timing info...
other text...
"""
            
            # After the fix, this should return only the JSON array
            json_output = linter._extract_json_from_output(npm_output)
            expected_json = '[{"filePath":"test.js","messages":[]}]'
            
            # Should extract only the JSON, not the trailing text
            assert json_output == expected_json, f"Expected: {expected_json}, Got: {json_output}"
            
            # Should be valid JSON that can be parsed
            data = json.loads(json_output)
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["filePath"] == "test.js"

    def test_should_handle_multiline_json_correctly(self):
        """Test that multi-line JSON extraction should work correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))
            
            npm_output = """
> project@1.0.0 lint
> eslint . --format json

[
  {
    "filePath": "test.js",
    "messages": []
  }
]

npm timing complete
"""
            
            # After the fix, should extract only the JSON part
            json_output = linter._extract_json_from_output(npm_output)
            
            # Should not contain the npm timing text
            assert "npm timing complete" not in json_output
            
            # The JSON should parse successfully with json.loads()
            data = json.loads(json_output)
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["filePath"] == "test.js"

    def test_should_handle_nested_structures(self):
        """Test that nested arrays and objects should be handled correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            linter = ESLintLinter(project_root=str(project_root))
            
            npm_output = """
> project@1.0.0 lint
> eslint . --format json

[{"filePath":"test.js","messages":[{"data":["item1","item2"],"nested":{"key":"value"}}]}]

npm complete
"""
            
            # After the fix, should extract only the JSON and parse successfully
            json_output = linter._extract_json_from_output(npm_output)
            
            # Should not contain the npm text
            assert "npm complete" not in json_output
            
            # Should parse complex nested structures correctly
            data = json.loads(json_output)
            assert isinstance(data, list)
            assert len(data) == 1
            message = data[0]["messages"][0]
            assert message["data"] == ["item1", "item2"]
            assert message["nested"]["key"] == "value"

    def test_lint_runner_parse_eslint_json_should_work_with_npm_output(self):
        """Test that LintRunner._parse_eslint_json_output works with npm output after fix."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            project_info = ProjectInfo(root_path=project_root, languages=["javascript"])
            runner = LintRunner(project_info=project_info)

            # npm output with valid JSON and extra text
            npm_stdout = """
> project@1.0.0 lint
> eslint . --format json

[{"filePath":"test.js","messages":[{"ruleId":"no-unused-vars","severity":2,"message":"'x' is defined but never used.","line":1,"column":7}]}]

npm timing info...
"""

            # After the fix, this should work correctly
            result = runner._parse_eslint_json_output(npm_stdout, "", 1)
            
            # Should successfully parse the error
            assert len(result.errors) == 1
            assert result.errors[0].rule_id == "no-unused-vars"
            assert result.errors[0].message == "'x' is defined but never used."
            assert result.errors[0].file_path == "test.js"
            assert result.errors[0].line == 1
            assert result.errors[0].column == 7

    def test_lint_runner_generic_json_should_work_with_npm_output(self):
        """Test that LintRunner._parse_json_output works with npm output for ESLint after fix."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            project_info = ProjectInfo(root_path=project_root, languages=["javascript"])
            runner = LintRunner(project_info=project_info)

            # npm output with valid JSON but extra text
            npm_output = """
> project@1.0.0 lint
> eslint . --format json

[{"filePath":"test.js","messages":[{"ruleId":"quotes","severity":1,"message":"Strings must use single quotes.","line":2,"column":5}]}]

npm timing info...
"""

            # After the fix, this should work correctly
            errors, warnings = runner._parse_json_output("eslint", npm_output)
            
            # Should successfully parse the warning
            assert len(errors) == 0
            assert len(warnings) == 1
            assert warnings[0].rule_id == "quotes"
            assert warnings[0].message == "Strings must use single quotes."
            assert warnings[0].file_path == "test.js"
            assert warnings[0].line == 2
            assert warnings[0].column == 5