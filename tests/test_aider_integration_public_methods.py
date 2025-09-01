
import os
import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from aider_lint_fixer.aider_integration import AiderIntegration, FixSession, FixResult
from aider_lint_fixer.config_manager import Config
from aider_lint_fixer.error_analyzer import FileAnalysis, ErrorAnalysis

class TestAiderIntegrationPublicMethods(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock(spec=Config)
        self.mock_config.llm = MagicMock()
        self.mock_config.llm.provider = "deepseek"
        self.mock_config.llm.model = "deepseek/deepseek-chat"
        self.integration = AiderIntegration(self.mock_config, ".", None)

    def test_fix_errors_in_file_empty(self):
        file_analysis = FileAnalysis(file_path="foo.py", total_errors=0, error_analyses=[])
        session = self.integration.fix_errors_in_file(file_analysis)
        self.assertIsInstance(session, FixSession)
        self.assertEqual(session.file_path, "foo.py")
        self.assertEqual(len(session.results), 0)

    @patch.object(AiderIntegration, "fix_errors_in_file")
    def test_fix_multiple_files(self, mock_fix_errors):
        mock_session_foo = MagicMock(spec=FixSession)
        mock_session_bar = MagicMock(spec=FixSession)
        # Return a different mock for each call
        mock_fix_errors.side_effect = [mock_session_foo, mock_session_bar]
        mock_error = MagicMock()
        file_analyses = {
            "foo.py": FileAnalysis(file_path="foo.py", total_errors=1, error_analyses=[mock_error]),
            "bar.py": FileAnalysis(file_path="bar.py", total_errors=1, error_analyses=[mock_error]),
        }
        sessions = self.integration.fix_multiple_files(file_analyses, max_files=2)
        print(f"fix_multiple_files returned {len(sessions)} sessions: {sessions}")
        self.assertEqual(len(sessions), 2)
        self.assertEqual(mock_fix_errors.call_count, 2)

    def test_execute_architect_guidance_no_dangerous(self):
        guidance = {"has_dangerous_errors": False}
        results = self.integration.execute_architect_guidance(guidance)
        self.assertEqual(results, [])

    def test_execute_safe_automation_no_plan(self):
        guidance = {"safe_automation_plan": {}}
        results = self.integration.execute_safe_automation(guidance, enabled_linters=["flake8"])
        self.assertEqual(results, [])

    def test_execute_safe_automation_no_errors(self):
        guidance = {"safe_automation_plan": {"safe_errors_count": 0}}
        results = self.integration.execute_safe_automation(guidance, enabled_linters=["flake8"])
        self.assertEqual(results, [])

if __name__ == "__main__":
    unittest.main()
