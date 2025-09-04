"""
JSON Parsing Robustness Tests - Critical Priority
=================================================

This test suite addresses the critical JSON parsing failures identified
during MCP framework testing where ESLint output parsing failed.

Key Issues to Test:
1. npm run lint output prefixes before JSON
2. Malformed JSON responses from linters
3. Mixed content with warnings and JSON
4. Empty responses and error conditions
5. Unicode and encoding issues
6. Large JSON responses and streaming

Coverage Target: Fixes the lint_runner.py module (currently 37.4% coverage)
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from aider_lint_fixer.lint_runner import LintRunner
from aider_lint_fixer.linters.eslint_linter import ESLintLinter
from aider_lint_fixer.linters.flake8_linter import Flake8Linter


class TestJSONParsingRobustness:
    """Test robust JSON parsing for various linter output formats."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock ProjectInfo for LintRunner
        from unittest.mock import Mock
        import tempfile
        
        mock_project_info = Mock()
        mock_project_info.languages = ['javascript', 'typescript']
        
        self.temp_dir = tempfile.mkdtemp()
        self.lint_runner = LintRunner(project_info=mock_project_info)
        self.eslint_linter = ESLintLinter(project_root=self.temp_dir)

    def test_eslint_npm_script_output_parsing(self):
        """Test parsing ESLint output with npm script prefix (MCP framework issue)."""
        # Exact output format that caused failure in MCP testing
        npm_prefix = (
            "> mcp-url-knowledge-graph@0.1.0 lint\n"
            "> eslint src/**/*.ts\n\n"
        )
        payload = [{
            "filePath": "/test/file.ts",
            "messages": [{
                "ruleId": "no-undef",
                "severity": 2,
                "message": "'process' is not defined",
                "line": 1,
                "column": 1,
                "nodeType": "Identifier",
                "messageId": "undef",
                "endLine": 1,
                "endColumn": 8
            }],
            "suppressedMessages": [],
            "errorCount": 1,
            "fatalErrorCount": 0,
            "warningCount": 0,
            "fixableErrorCount": 0,
            "fixableWarningCount": 0,
            "source": "process.env.NODE_ENV"
        }]
        npm_output = npm_prefix + json.dumps(payload)
        
        errors, warnings = self.eslint_linter._parse_json_output(npm_output)
        
        # Should successfully extract JSON despite npm prefix
        assert errors is not None
        assert len(errors) == 1
        assert errors[0].file_path == '/test/file.ts'
        assert errors[0].rule_id == 'no-undef'
        assert errors[0].message == "'process' is not defined"

    def test_eslint_json_with_warnings_and_errors(self):
        """Test parsing complex ESLint JSON with multiple issue types."""
        complex_output = """
> project@1.0.0 lint
> eslint src/**/*.ts

[
  {
    "filePath": "/test/file1.ts",
    "messages": [
      {
        "ruleId": "no-undef",
        "severity": 2,
        "message": "'process' is not defined",
        "line": 1,
        "column": 1,
        "nodeType": "Identifier",
        "messageId": "undef"
      },
      {
        "ruleId": "@typescript-eslint/no-explicit-any",
        "severity": 1,
        "message": "Unexpected any. Specify a different type",
        "line": 5,
        "column": 10
      }
    ],
    "errorCount": 1,
    "warningCount": 1
  },
  {
    "filePath": "/test/file2.ts", 
    "messages": [],
    "errorCount": 0,
    "warningCount": 0
  }
]
        """
        
        result = self.eslint_linter._parse_json_output(complex_output)
        
        assert result is not None
        assert len(result) == 2
        
        # First file with issues
        assert result[0]['errorCount'] == 1
        assert result[0]['warningCount'] == 1
        assert len(result[0]['messages']) == 2
        
        # Second file clean
        assert result[1]['errorCount'] == 0
        assert result[1]['warningCount'] == 0
        assert len(result[1]['messages']) == 0

    def test_malformed_json_handling(self):
        """Test handling of completely malformed JSON output."""
        malformed_outputs = [
            "Error: ENOENT: no such file or directory",
            "npm ERR! Missing script: 'lint'",
            "SyntaxError: Unexpected token in JSON",
            "",  # Empty output
            "null",  # Null JSON
            "[{incomplete json",  # Incomplete JSON
            "Not JSON at all - just error text",
            "\n\n   \n",  # Whitespace only
        ]
        
        for malformed_output in malformed_outputs:
            result = self.eslint_linter._parse_json_output(malformed_output)
            
            # Should return empty list or None, but not crash
            assert result == [] or result is None

    def test_json_with_unicode_and_special_characters(self):
        """Test parsing JSON with Unicode and special characters."""
        unicode_output = """
> project@1.0.0 lint  
> eslint src/**/*.ts

[{"filePath":"/test/файл.ts","messages":[{"ruleId":"no-console","severity":1,"message":"Unexpected console statement 🚨","line":1,"column":1,"nodeType":"MemberExpression"}],"errorCount":0,"warningCount":1}]
        """
        
        result = self.eslint_linter._parse_json_output(unicode_output)
        
        assert result is not None
        assert len(result) == 1
        assert result[0]['filePath'] == '/test/файл.ts'
        assert '🚨' in result[0]['messages'][0]['message']

    def test_large_json_output_performance(self):
        """Test performance with large JSON outputs."""
        # Create large JSON structure (simulating many files with many errors)
        large_files = []
        for i in range(100):  # 100 files
            messages = []
            for j in range(50):  # 50 errors per file
                messages.append({
                    "ruleId": f"rule-{j}",
                    "severity": 2,
                    "message": f"Error message {j} in file {i}",
                    "line": j + 1,
                    "column": 1
                })
            
            large_files.append({
                "filePath": f"/test/file{i}.ts",
                "messages": messages,
                "errorCount": 50,
                "warningCount": 0
            })
        
        large_json = json.dumps(large_files, indent=2)
        npm_prefix = "> project@1.0.0 lint\n> eslint src/**/*.ts\n\n"
        large_output = npm_prefix + large_json
        
        # Should handle large output without timeout or memory issues
        import time
        start_time = time.time()
        result = self.eslint_linter._parse_json_output(large_output)
        parse_time = time.time() - start_time
        
        assert result is not None
        assert len(result) == 100
        assert parse_time < 5.0  # Should parse within 5 seconds

    def test_nested_json_structure_parsing(self):
        """Test parsing deeply nested JSON structures."""
        nested_output = """
> project@1.0.0 lint
> eslint src/**/*.ts

[
  {
    "filePath": "/test/file.ts",
    "messages": [
      {
        "ruleId": "complex-rule",
        "severity": 2,
        "message": "Complex error with nested data",
        "line": 1,
        "column": 1,
        "nodeType": "Identifier",
        "messageId": "complex",
        "fix": {
          "range": [0, 10],
          "text": "replacement"
        },
        "suggestions": [
          {
            "desc": "Suggestion 1",
            "fix": {
              "range": [0, 5],
              "text": "fix1"
            }
          },
          {
            "desc": "Suggestion 2", 
            "fix": {
              "range": [5, 10],
              "text": "fix2"
            }
          }
        ]
      }
    ],
    "errorCount": 1,
    "warningCount": 0,
    "fatalErrorCount": 0,
    "fixableErrorCount": 1,
    "fixableWarningCount": 0,
    "source": "original source code here"
  }
]
        """
        
        result = self.eslint_linter._parse_json_output(nested_output)
        
        assert result is not None
        assert len(result) == 1
        message = result[0]['messages'][0]
        assert 'fix' in message
        assert 'suggestions' in message
        assert len(message['suggestions']) == 2
        assert message['suggestions'][0]['desc'] == 'Suggestion 1'

    def test_streaming_json_parsing(self):
        """Test parsing JSON that comes in chunks (streaming scenario)."""
        # Simulate chunked JSON data
        json_chunks = [
            '> project@1.0.0 lint\n',
            '> eslint src/**/*.ts\n\n',
            '[{"filePath":"/test/file.ts",',
            '"messages":[{"ruleId":"no-undef",',
            '"severity":2,"message":"Error",',
            '"line":1,"column":1}],',
            '"errorCount":1,"warningCount":0}]'
        ]
        
        # Concatenate chunks to simulate complete output
        complete_output = ''.join(json_chunks)
        result = self.eslint_linter._parse_json_output(complete_output)
        
        assert result is not None
        assert len(result) == 1
        assert result[0]['errorCount'] == 1

    def test_json_with_escaped_characters(self):
        """Test parsing JSON with escaped characters in messages."""
        escaped_output = r"""
> project@1.0.0 lint
> eslint src/**/*.ts

[{"filePath":"/test/file.ts","messages":[{"ruleId":"quotes","severity":2,"message":"Strings must use \"double quotes\", not 'single quotes'","line":1,"column":1}],"errorCount":1,"warningCount":0}]
        """
        
        result = self.eslint_linter._parse_json_output(escaped_output)
        
        assert result is not None
        assert len(result) == 1
        assert 'double quotes' in result[0]['messages'][0]['message']

    def test_multiple_json_arrays_handling(self):
        """Test handling output with multiple JSON arrays (edge case)."""
        multiple_arrays = """
> project@1.0.0 lint
> eslint src/**/*.ts

[{"filePath":"/test/file1.ts","messages":[],"errorCount":0}]
[{"filePath":"/test/file2.ts","messages":[],"errorCount":0}]
        """
        
        # Should handle the first valid JSON array
        result = self.eslint_linter._parse_json_output(multiple_arrays)
        
        # Should not crash and return some valid result
        assert result is not None or result == []

    def test_json_parsing_with_comments(self):
        """Test parsing JSON-like output with comments (invalid JSON)."""
        json_with_comments = """
> project@1.0.0 lint
> eslint src/**/*.ts

// ESLint results
[
  // File results
  {
    "filePath": "/test/file.ts", /* File path */
    "messages": [], // No messages
    "errorCount": 0
  }
]
        """
        
        # Should handle gracefully (comments make this invalid JSON)
        result = self.eslint_linter._parse_json_output(json_with_comments)
        
        # Should return empty or None due to invalid JSON
        assert result == [] or result is None


class TestFlake8ParsingRobustness:
    """Test Flake8 output parsing robustness."""

    def setup_method(self):
        """Set up test fixtures."""
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.flake8_linter = Flake8Linter(project_root=self.temp_dir)

    def test_flake8_standard_output_parsing(self):
        """Test parsing standard Flake8 output format."""
        flake8_output = """
/test/file.py:1:1: E302 expected 2 blank lines, found 1
/test/file.py:5:80: E501 line too long (85 > 79 characters)
/test/file.py:10:1: F401 'os' imported but unused
        """
        
        result = self.flake8_linter._parse_output(flake8_output)
        
        assert result is not None
        assert len(result) == 3
        assert result[0]['line'] == 1
        assert result[0]['rule_id'] == 'E302'
        assert result[1]['line'] == 5
        assert result[1]['rule_id'] == 'E501'

    def test_flake8_json_format_parsing(self):
        """Test parsing Flake8 JSON format output."""
        flake8_json = """
{
  "/test/file.py": [
    {
      "code": "E302",
      "filename": "/test/file.py",
      "line_number": 1,
      "column_number": 1,
      "text": "expected 2 blank lines, found 1",
      "physical_line": "def function():"
    }
  ]
}
        """
        
        result = self.flake8_linter._parse_json_output(flake8_json)
        
        assert result is not None
        assert '/test/file.py' in result
        assert len(result['/test/file.py']) == 1
        assert result['/test/file.py'][0]['code'] == 'E302'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
