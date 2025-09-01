#!/usr/bin/env python3
"""
Tests for aider_strategic_recommendations module.

Tests the AiderStrategicRecommendationEngine for generating
strategic cleanup recommendations for chaotic codebases.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from aider_lint_fixer.aider_strategic_recommendations import (
    AiderRecommendation,
    AiderStrategicRecommendationEngine,
    demonstrate_aider_recommendations,
)
from aider_lint_fixer.strategic_preflight_check import ChaosIndicator, ChaosLevel


class TestAiderRecommendation(unittest.TestCase):
    """Test AiderRecommendation dataclass."""

    def test_aider_recommendation_creation(self):
        """Test creating AiderRecommendation objects."""
        recommendation = AiderRecommendation(
            category="Test Category",
            priority="high",
            title="Test Title",
            description="Test description",
            specific_actions=["action1", "action2"],
            files_affected=["file1.py", "file2.py"],
            estimated_time="30 minutes",
            aider_commands=["cmd1", "cmd2"],
        )

        self.assertEqual(recommendation.category, "Test Category")
        self.assertEqual(recommendation.priority, "high")
        self.assertEqual(recommendation.title, "Test Title")
        self.assertEqual(recommendation.description, "Test description")
        self.assertEqual(recommendation.specific_actions, ["action1", "action2"])
        self.assertEqual(recommendation.files_affected, ["file1.py", "file2.py"])
        self.assertEqual(recommendation.estimated_time, "30 minutes")
        self.assertEqual(recommendation.aider_commands, ["cmd1", "cmd2"])

    def test_aider_recommendation_defaults(self):
        """Test AiderRecommendation with minimal fields."""
        recommendation = AiderRecommendation(
            category="Test",
            priority="low",
            title="Title",
            description="Description",
            specific_actions=[],
            files_affected=[],
            estimated_time="5 minutes",
            aider_commands=[],
        )

        self.assertEqual(recommendation.category, "Test")
        self.assertEqual(len(recommendation.specific_actions), 0)
        self.assertEqual(len(recommendation.files_affected), 0)
        self.assertEqual(len(recommendation.aider_commands), 0)


class TestAiderStrategicRecommendationEngine(unittest.TestCase):
    """Test AiderStrategicRecommendationEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.engine = AiderStrategicRecommendationEngine(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except OSError:
            pass

    def test_engine_initialization(self):
        """Test engine initialization."""
        self.assertEqual(str(self.engine.project_path), self.temp_dir)
        self.assertIsNone(self.engine.config_manager)
        self.assertIsNone(self.engine.temp_dir)

    def test_engine_initialization_with_config(self):
        """Test engine initialization with config manager."""
        mock_config = Mock()
        engine = AiderStrategicRecommendationEngine(self.temp_dir, mock_config)
        
        self.assertEqual(str(engine.project_path), self.temp_dir)
        self.assertEqual(engine.config_manager, mock_config)

    @patch('builtins.print')
    def test_generate_recommendations_empty_indicators(self, mock_print):
        """Test generating recommendations with no indicators."""
        recommendations = self.engine.generate_recommendations(ChaosLevel.CLEAN, [])
        
        self.assertEqual(len(recommendations), 0)
        mock_print.assert_called_once_with("\n🤖 Generating aider-powered strategic recommendations...")

    @patch('builtins.print')
    def test_generate_recommendations_low_severity(self, mock_print):
        """Test generating recommendations with low severity indicators."""
        indicators = [
            ChaosIndicator(
                type="test_type",
                severity="minor",
                description="Minor issue",
                evidence=["test.py"],
                impact="Low impact",
            )
        ]
        
        recommendations = self.engine.generate_recommendations(ChaosLevel.MESSY, indicators)
        
        # Should not generate recommendations for minor severity
        self.assertEqual(len(recommendations), 0)
        mock_print.assert_called_once()

    @patch('builtins.print')
    def test_generate_recommendations_file_organization(self, mock_print):
        """Test generating file organization recommendations."""
        # Create some test files
        test_files = ["test1.py", "test2.py", "demo.py"]
        for filename in test_files:
            (Path(self.temp_dir) / filename).write_text("# test file")
        
        indicators = [
            ChaosIndicator(
                type="file_organization",
                severity="major",
                description="Too many files in root",
                evidence=test_files,
                impact="Project structure unclear",
            )
        ]
        
        recommendations = self.engine.generate_recommendations(ChaosLevel.CHAOTIC, indicators)
        
        self.assertEqual(len(recommendations), 2)  # file org + structure rec
        
        # Check file organization recommendation
        file_org_rec = next((r for r in recommendations if r.category == "File Organization"), None)
        self.assertIsNotNone(file_org_rec)
        self.assertEqual(file_org_rec.priority, "high")
        self.assertEqual(file_org_rec.title, "Reorganize Root Directory Structure")
        self.assertIn("Create src/ directory", file_org_rec.specific_actions[0])
        self.assertIn("mkdir -p src/", file_org_rec.aider_commands[0])

    @patch('builtins.print')
    def test_generate_recommendations_code_structure(self, mock_print):
        """Test generating code structure recommendations."""
        # Create experimental files
        experimental_files = ["demo_test.py", "debug_script.py", "experimental_feature.py"]
        for filename in experimental_files:
            (Path(self.temp_dir) / filename).write_text("# experimental file")
        
        indicators = [
            ChaosIndicator(
                type="code_structure",
                severity="critical",
                description="Too many experimental files",
                evidence=experimental_files,
                impact="Unclear which code is production",
            )
        ]
        
        recommendations = self.engine.generate_recommendations(ChaosLevel.DISASTER, indicators)
        
        self.assertEqual(len(recommendations), 2)  # code structure + overall structure
        
        # Check code structure recommendation
        code_rec = next((r for r in recommendations if r.category == "Code Structure"), None)
        self.assertIsNotNone(code_rec)
        self.assertEqual(code_rec.priority, "high")
        self.assertEqual(code_rec.title, "Separate Production from Experimental Code")
        self.assertIn("Review each experimental file", code_rec.specific_actions[0])
        self.assertIn("mkdir -p experiments/", code_rec.aider_commands[0])

    @patch('builtins.print')
    def test_generate_recommendations_documentation(self, mock_print):
        """Test generating documentation recommendations."""
        indicators = [
            ChaosIndicator(
                type="documentation",
                severity="major",
                description="Documentation out of sync",
                evidence=["README.md", "docs/"],
                impact="Users confused about project",
            )
        ]
        
        recommendations = self.engine.generate_recommendations(ChaosLevel.CHAOTIC, indicators)
        
        self.assertEqual(len(recommendations), 2)  # documentation + structure rec
        
        # Check documentation recommendation
        doc_rec = next((r for r in recommendations if r.category == "Documentation"), None)
        self.assertIsNotNone(doc_rec)
        self.assertEqual(doc_rec.priority, "medium")
        self.assertEqual(doc_rec.title, "Align Documentation with Reality")
        self.assertIn("Review README.md", doc_rec.specific_actions[0])
        self.assertIn("README.md", doc_rec.files_affected)

    @patch('builtins.print')
    def test_generate_recommendations_unknown_type(self, mock_print):
        """Test generating recommendations with unknown indicator type."""
        indicators = [
            ChaosIndicator(
                type="unknown_type",
                severity="critical",
                description="Unknown issue",
                evidence=["unknown.py"],
                impact="Unknown impact",
            )
        ]
        
        recommendations = self.engine.generate_recommendations(ChaosLevel.CHAOTIC, indicators)
        
        # Should only generate structure recommendation for chaotic level
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0].category, "Project Structure")

    def test_generate_indicator_recommendation_file_organization(self):
        """Test generating specific file organization recommendation."""
        # Create test files
        for i in range(5):
            (Path(self.temp_dir) / f"test{i}.py").write_text("# test")
        
        indicator = ChaosIndicator(
            type="file_organization",
            severity="major",
            description="Too many files",
            evidence=["test0.py", "test1.py"],
            impact="Messy structure",
        )
        
        recommendation = self.engine._generate_indicator_recommendation(indicator, ChaosLevel.CHAOTIC)
        
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation.category, "File Organization")
        self.assertEqual(recommendation.priority, "high")
        self.assertIn("5 Python files", recommendation.description)

    def test_generate_indicator_recommendation_code_structure(self):
        """Test generating specific code structure recommendation."""
        # Create experimental files
        experimental_files = ["demo_test.py", "debug_script.py"]
        for filename in experimental_files:
            (Path(self.temp_dir) / filename).write_text("# experimental")
        
        indicator = ChaosIndicator(
            type="code_structure",
            severity="major",
            description="Too many experimental files",
            evidence=experimental_files,
            impact="Unclear code purpose",
        )
        
        recommendation = self.engine._generate_indicator_recommendation(indicator, ChaosLevel.CHAOTIC)
        
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation.category, "Code Structure")
        self.assertEqual(recommendation.priority, "high")
        self.assertIn("experimental/demo files", recommendation.description)

    def test_generate_indicator_recommendation_documentation(self):
        """Test generating specific documentation recommendation."""
        indicator = ChaosIndicator(
            type="documentation",
            severity="major",
            description="Docs out of sync",
            evidence=["README.md"],
            impact="User confusion",
        )
        
        recommendation = self.engine._generate_indicator_recommendation(indicator, ChaosLevel.CHAOTIC)
        
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation.category, "Documentation")
        self.assertEqual(recommendation.priority, "medium")

    def test_generate_indicator_recommendation_unknown(self):
        """Test generating recommendation for unknown indicator type."""
        indicator = ChaosIndicator(
            type="unknown",
            severity="major",
            description="Unknown issue",
            evidence=["file.py"],
            impact="Unknown impact",
        )
        
        recommendation = self.engine._generate_indicator_recommendation(indicator, ChaosLevel.CHAOTIC)
        
        self.assertIsNone(recommendation)

    def test_generate_file_organization_recommendation_no_files(self):
        """Test file organization recommendation with no Python files."""
        indicator = ChaosIndicator(
            type="file_organization",
            severity="major",
            description="File organization issues",
            evidence=["some_file.txt"],
            impact="Poor organization",
        )
        
        recommendation = self.engine._generate_file_organization_recommendation(indicator)
        
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation.category, "File Organization")
        self.assertIn("0 Python files", recommendation.description)

    def test_generate_file_organization_recommendation_many_files(self):
        """Test file organization recommendation with many Python files."""
        # Create many test files
        for i in range(15):
            (Path(self.temp_dir) / f"file{i}.py").write_text("# test")
        
        indicator = ChaosIndicator(
            type="file_organization",
            severity="major",
            description="Too many files in root",
            evidence=["file0.py", "file1.py"],
            impact="Project structure unclear",
        )
        
        recommendation = self.engine._generate_file_organization_recommendation(indicator)
        
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation.category, "File Organization")
        self.assertIn("15 Python files", recommendation.description)
        self.assertEqual(len(recommendation.files_affected), 6)  # 5 + "..."
        self.assertEqual(recommendation.files_affected[-1], "...")

    def test_generate_code_structure_recommendation_no_experimental(self):
        """Test code structure recommendation with no experimental files."""
        # Create regular files (not experimental)
        for filename in ["regular.py", "normal.py"]:
            (Path(self.temp_dir) / filename).write_text("# regular file")
        
        indicator = ChaosIndicator(
            type="code_structure",
            severity="major",
            description="Code structure issues",
            evidence=["regular.py"],
            impact="Poor structure",
        )
        
        recommendation = self.engine._generate_code_structure_recommendation(indicator)
        
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation.category, "Code Structure")
        self.assertIn("0 experimental/demo files", recommendation.description)

    def test_generate_code_structure_recommendation_with_experimental(self):
        """Test code structure recommendation with experimental files."""
        experimental_files = ["demo_app.py", "test_script.py", "debug_tool.py", "temp_fix.py"]
        for filename in experimental_files:
            (Path(self.temp_dir) / filename).write_text("# experimental")
        
        indicator = ChaosIndicator(
            type="code_structure",
            severity="major",
            description="Too many experimental files",
            evidence=experimental_files,
            impact="Unclear code purpose",
        )
        
        recommendation = self.engine._generate_code_structure_recommendation(indicator)
        
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation.category, "Code Structure")
        self.assertIn("4 experimental/demo files", recommendation.description)
        # Should have first 5 files + "..." if more than 5
        self.assertEqual(len(recommendation.files_affected), 5)  # 4 + ["..."]

    def test_generate_documentation_recommendation(self):
        """Test documentation recommendation generation."""
        indicator = ChaosIndicator(
            type="documentation",
            severity="major",
            description="Documentation issues",
            evidence=["README.md", "outdated_doc.md"],
            impact="User confusion",
        )
        
        recommendation = self.engine._generate_documentation_recommendation(indicator)
        
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation.category, "Documentation")
        self.assertEqual(recommendation.priority, "medium")
        self.assertEqual(recommendation.title, "Align Documentation with Reality")
        self.assertIn("README.md", recommendation.files_affected)
        self.assertIn("outdated_doc.md", recommendation.files_affected)

    def test_generate_structure_recommendation(self):
        """Test overall structure recommendation generation."""
        indicators = [
            ChaosIndicator(
                type="file_organization",
                severity="major",
                description="File org issues",
                evidence=["file.py"],
                impact="Poor organization",
            )
        ]
        
        recommendation = self.engine._generate_structure_recommendation(ChaosLevel.CHAOTIC, indicators)
        
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation.category, "Project Structure")
        self.assertEqual(recommendation.priority, "critical")
        self.assertEqual(recommendation.title, "Establish Clear Project Architecture")
        self.assertIn("entire project", recommendation.files_affected)
        self.assertIn("2-4 hours", recommendation.estimated_time)

    def test_query_aider(self):
        """Test _query_aider method."""
        prompt = "Test prompt for aider"
        context = "test_context"
        
        result = self.engine._query_aider(prompt, context)
        
        self.assertIsInstance(result, str)
        self.assertIn("Aider recommendation for test_context", result)
        self.assertIn("Test prompt for aider", result)

    @patch('builtins.print')
    def test_display_recommendations_empty(self, mock_print):
        """Test displaying empty recommendations."""
        self.engine.display_recommendations([])
        
        mock_print.assert_called_once_with("✅ No strategic recommendations needed - codebase structure looks good!")

    @patch('builtins.print')
    def test_display_recommendations_single(self, mock_print):
        """Test displaying single recommendation."""
        recommendation = AiderRecommendation(
            category="Test",
            priority="high",
            title="Test Recommendation",
            description="Test description",
            specific_actions=["action1", "action2"],
            files_affected=["file1.py"],
            estimated_time="30 minutes",
            aider_commands=["cmd1", "cmd2"],
        )
        
        self.engine.display_recommendations([recommendation])
        
        # Check that print was called multiple times with expected content
        print_calls = [call.args[0] for call in mock_print.call_args_list if call.args]
        
        # Should print header
        header_found = any("Strategic Cleanup Recommendations (1 items)" in str(call) for call in print_calls)
        self.assertTrue(header_found)
        
        # Should print priority section
        priority_found = any("HIGH PRIORITY (1 items)" in str(call) for call in print_calls)
        self.assertTrue(priority_found)
        
        # Should print recommendation details
        title_found = any("Test Recommendation" in str(call) for call in print_calls)
        self.assertTrue(title_found)

    @patch('builtins.print')
    def test_display_recommendations_multiple_priorities(self, mock_print):
        """Test displaying recommendations with different priorities."""
        recommendations = [
            AiderRecommendation(
                category="Critical", priority="critical", title="Critical Issue",
                description="Critical desc", specific_actions=["critical_action"],
                files_affected=["critical.py"], estimated_time="1 hour",
                aider_commands=["critical_cmd"]
            ),
            AiderRecommendation(
                category="High", priority="high", title="High Issue",
                description="High desc", specific_actions=["high_action"],
                files_affected=["high.py"], estimated_time="30 min",
                aider_commands=["high_cmd"]
            ),
            AiderRecommendation(
                category="Medium", priority="medium", title="Medium Issue",
                description="Medium desc", specific_actions=["med_action"],
                files_affected=["med.py"], estimated_time="15 min",
                aider_commands=["med_cmd"]
            ),
        ]
        
        self.engine.display_recommendations(recommendations)
        
        print_calls = [call.args[0] for call in mock_print.call_args_list if call.args]
        
        # Should print all priority sections
        critical_found = any("CRITICAL (1 items)" in str(call) for call in print_calls)
        high_found = any("HIGH PRIORITY (1 items)" in str(call) for call in print_calls)
        medium_found = any("MEDIUM PRIORITY (1 items)" in str(call) for call in print_calls)
        
        self.assertTrue(critical_found)
        self.assertTrue(high_found)
        self.assertTrue(medium_found)

    @patch('builtins.print')
    def test_display_recommendations_long_lists(self, mock_print):
        """Test displaying recommendations with long action/command lists."""
        recommendation = AiderRecommendation(
            category="Test",
            priority="high",
            title="Test with Long Lists",
            description="Test description",
            specific_actions=["action1", "action2", "action3", "action4", "action5"],
            files_affected=["file1.py"],
            estimated_time="60 minutes",
            aider_commands=["cmd1", "cmd2", "cmd3", "cmd4"],
        )
        
        self.engine.display_recommendations([recommendation])
        
        print_calls = [call.args[0] for call in mock_print.call_args_list if call.args]
        
        # Should truncate long lists
        more_actions_found = any("and 2 more" in str(call) for call in print_calls)
        more_commands_found = any("and 2 more commands" in str(call) for call in print_calls)
        
        self.assertTrue(more_actions_found)
        self.assertTrue(more_commands_found)

    @patch('builtins.print')
    def test_display_recommendations_next_steps(self, mock_print):
        """Test that next steps are displayed."""
        recommendation = AiderRecommendation(
            category="Test", priority="high", title="Test",
            description="Test", specific_actions=["action"],
            files_affected=["file.py"], estimated_time="30 min",
            aider_commands=["cmd"]
        )
        
        self.engine.display_recommendations([recommendation])
        
        print_calls = [call.args[0] for call in mock_print.call_args_list if call.args]
        
        # Should print next steps
        next_steps_found = any("Next Steps:" in str(call) for call in print_calls)
        pro_tip_found = any("Pro Tip:" in str(call) for call in print_calls)
        
        self.assertTrue(next_steps_found)
        self.assertTrue(pro_tip_found)


class TestDemonstrateAiderRecommendations(unittest.TestCase):
    """Test demonstrate_aider_recommendations function."""

    @patch('aider_lint_fixer.aider_strategic_recommendations.AiderStrategicRecommendationEngine')
    @patch('builtins.print')
    def test_demonstrate_aider_recommendations(self, mock_print, mock_engine_class):
        """Test the demonstration function."""
        # Mock the engine instance
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        
        # Mock recommendations
        mock_recommendations = [
            AiderRecommendation(
                category="Demo", priority="high", title="Demo Recommendation",
                description="Demo description", specific_actions=["demo_action"],
                files_affected=["demo.py"], estimated_time="30 min",
                aider_commands=["demo_cmd"]
            )
        ]
        mock_engine.generate_recommendations.return_value = mock_recommendations
        
        # Run the demonstration
        demonstrate_aider_recommendations()
        
        # Verify engine was created with current directory
        mock_engine_class.assert_called_once_with(".")
        
        # Verify generate_recommendations was called
        mock_engine.generate_recommendations.assert_called_once()
        call_args = mock_engine.generate_recommendations.call_args
        self.assertEqual(call_args[0][0], ChaosLevel.CHAOTIC)
        self.assertEqual(len(call_args[0][1]), 2)  # 2 indicators
        
        # Verify display_recommendations was called
        mock_engine.display_recommendations.assert_called_once_with(mock_recommendations)
        
        # Verify print was called for demo header
        print_calls = [call.args[0] for call in mock_print.call_args_list if call.args]
        header_found = any("Aider-Powered Strategic Recommendations Demo" in str(call) for call in print_calls)
        self.assertTrue(header_found)

    @patch('aider_lint_fixer.aider_strategic_recommendations.AiderStrategicRecommendationEngine')
    def test_demonstrate_chaos_indicators(self, mock_engine_class):
        """Test that demonstration creates proper chaos indicators."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.generate_recommendations.return_value = []
        
        demonstrate_aider_recommendations()
        
        # Check the indicators passed to generate_recommendations
        call_args = mock_engine.generate_recommendations.call_args[0]
        indicators = call_args[1]
        
        self.assertEqual(len(indicators), 2)
        
        # Check first indicator (file organization)
        file_org_indicator = indicators[0]
        self.assertEqual(file_org_indicator.type, "file_organization")
        self.assertEqual(file_org_indicator.severity, "major")
        self.assertIn("Python files in root", file_org_indicator.description)
        
        # Check second indicator (code structure)
        code_struct_indicator = indicators[1]
        self.assertEqual(code_struct_indicator.type, "code_structure")
        self.assertEqual(code_struct_indicator.severity, "major")
        self.assertIn("experimental/demo files", code_struct_indicator.description)


class TestMainExecution(unittest.TestCase):
    """Test main execution functionality."""

    def test_main_execution(self):
        """Test that main execution works correctly."""
        # Test that the main block executes without error
        import subprocess
        import sys
        
        # Run the module as a script to test main execution
        result = subprocess.run([
            sys.executable, '-c', 
            'from aider_lint_fixer.aider_strategic_recommendations import demonstrate_aider_recommendations; demonstrate_aider_recommendations()'
        ], capture_output=True, text=True)
        
        # Verify it runs successfully
        self.assertEqual(result.returncode, 0)
        self.assertIn('Aider-Powered Strategic Recommendations Demo', result.stdout)


if __name__ == "__main__":
    unittest.main()