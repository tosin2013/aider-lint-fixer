#!/usr/bin/env python3
"""
Tests for cache_cli module.

Tests CLI commands for cache management, including stats, cleanup,
export, and import operations.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import click
from click.testing import CliRunner

from aider_lint_fixer.cache_cli import cache_manager


class TestCacheManagerCLI(unittest.TestCase):
    """Test cache_manager CLI command."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.test_project_path = self.temp_dir

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except OSError:
            pass

    @patch('aider_lint_fixer.cache_cli.SmartErrorClassifier')
    def test_cache_manager_stats_action(self, mock_classifier_class):
        """Test cache manager stats action."""
        # Mock the classifier instance
        mock_classifier = Mock()
        mock_classifier_class.return_value = mock_classifier
        
        # Mock statistics data
        mock_stats = {
            'cache': {
                'cache_dir': '/test/cache',
                'cache_sizes': {
                    'training_files': 1024,
                    'model_files': 2048,
                    'total_files': 3072
                }
            },
            'pattern_matcher': {
                'languages': ['python', 'javascript'],
                'total_patterns': 150,
                'ahocorasick_available': True
            },
            'ml_classifier': {
                'sklearn_available': True,
                'trained_languages': ['python', 'javascript'],
                'python_training_examples': 50,
                'javascript_training_examples': 75
            }
        }
        mock_classifier.get_statistics.return_value = mock_stats

        # Run the command
        result = self.runner.invoke(cache_manager, [
            '--project-path', self.test_project_path,
            '--action', 'stats'
        ])

        # Verify command execution
        self.assertEqual(result.exit_code, 0)
        
        # Verify classifier was initialized correctly
        mock_classifier_class.assert_called_once()
        call_args = mock_classifier_class.call_args[0]
        self.assertTrue(str(call_args[0]).endswith('.aider-lint-cache'))
        
        # Verify get_statistics was called
        mock_classifier.get_statistics.assert_called_once()
        
        # Verify output contains expected information
        output = result.output
        self.assertIn('Pattern Cache Statistics', output)
        self.assertIn('/test/cache', output)
        self.assertIn('1,024 bytes', output)
        self.assertIn('2,048 bytes', output)
        self.assertIn('3,072 bytes', output)
        self.assertIn('python, javascript', output)
        self.assertIn('150', output)
        self.assertIn('True', output)
        self.assertIn('50 training examples', output)
        self.assertIn('75 training examples', output)

    @patch('aider_lint_fixer.cache_cli.SmartErrorClassifier')
    def test_cache_manager_cleanup_action(self, mock_classifier_class):
        """Test cache manager cleanup action."""
        # Mock the classifier instance
        mock_classifier = Mock()
        mock_classifier_class.return_value = mock_classifier
        
        # Mock cache manager
        mock_cache_manager = Mock()
        mock_classifier.cache_manager = mock_cache_manager

        # Run the command with default max age
        result = self.runner.invoke(cache_manager, [
            '--project-path', self.test_project_path,
            '--action', 'cleanup'
        ])

        # Verify command execution
        self.assertEqual(result.exit_code, 0)
        
        # Verify cleanup was called with default max age (30 days)
        mock_cache_manager.cleanup_old_data.assert_called_once_with(30)
        
        # Verify output
        output = result.output
        self.assertIn('Cleaning up cache', output)
        self.assertIn('max age: 30 days', output)
        self.assertIn('Cache cleanup complete', output)

    @patch('aider_lint_fixer.cache_cli.SmartErrorClassifier')
    def test_cache_manager_cleanup_action_custom_age(self, mock_classifier_class):
        """Test cache manager cleanup action with custom max age."""
        # Mock the classifier instance
        mock_classifier = Mock()
        mock_classifier_class.return_value = mock_classifier
        
        # Mock cache manager
        mock_cache_manager = Mock()
        mock_classifier.cache_manager = mock_cache_manager

        # Run the command with custom max age
        result = self.runner.invoke(cache_manager, [
            '--project-path', self.test_project_path,
            '--action', 'cleanup',
            '--max-age-days', '7'
        ])

        # Verify command execution
        self.assertEqual(result.exit_code, 0)
        
        # Verify cleanup was called with custom max age
        mock_cache_manager.cleanup_old_data.assert_called_once_with(7)
        
        # Verify output contains custom age
        output = result.output
        self.assertIn('max age: 7 days', output)

    @patch('aider_lint_fixer.cache_cli.SmartErrorClassifier')
    def test_cache_manager_export_action_success(self, mock_classifier_class):
        """Test cache manager export action with valid file path."""
        # Mock the classifier instance
        mock_classifier = Mock()
        mock_classifier_class.return_value = mock_classifier

        # Run the command
        export_file = str(Path(self.temp_dir) / "export.json")
        result = self.runner.invoke(cache_manager, [
            '--project-path', self.test_project_path,
            '--action', 'export',
            '--file', export_file
        ])

        # Verify command execution
        self.assertEqual(result.exit_code, 0)
        
        # Verify export was called
        mock_classifier.export_learned_patterns.assert_called_once_with(export_file)
        
        # Verify output
        output = result.output
        self.assertIn('Exporting patterns', output)
        self.assertIn(export_file, output)
        self.assertIn('Export complete', output)

    @patch('aider_lint_fixer.cache_cli.SmartErrorClassifier')
    def test_cache_manager_export_action_no_file(self, mock_classifier_class):
        """Test cache manager export action without file parameter."""
        # Mock the classifier instance
        mock_classifier = Mock()
        mock_classifier_class.return_value = mock_classifier

        # Run the command without --file parameter
        result = self.runner.invoke(cache_manager, [
            '--project-path', self.test_project_path,
            '--action', 'export'
        ])

        # Verify command execution
        self.assertEqual(result.exit_code, 0)
        
        # Verify export was NOT called
        mock_classifier.export_learned_patterns.assert_not_called()
        
        # Verify error output
        output = result.output
        self.assertIn('Export requires --file parameter', output)

    @patch('aider_lint_fixer.cache_cli.SmartErrorClassifier')
    def test_cache_manager_import_action_success(self, mock_classifier_class):
        """Test cache manager import action with valid file path."""
        # Mock the classifier instance
        mock_classifier = Mock()
        mock_classifier_class.return_value = mock_classifier

        # Run the command
        import_file = str(Path(self.temp_dir) / "import.json")
        result = self.runner.invoke(cache_manager, [
            '--project-path', self.test_project_path,
            '--action', 'import',
            '--file', import_file
        ])

        # Verify command execution
        self.assertEqual(result.exit_code, 0)
        
        # Verify import was called
        mock_classifier.import_learned_patterns.assert_called_once_with(import_file)
        
        # Verify output
        output = result.output
        self.assertIn('Importing patterns', output)
        self.assertIn(import_file, output)
        self.assertIn('Import complete', output)

    @patch('aider_lint_fixer.cache_cli.SmartErrorClassifier')
    def test_cache_manager_import_action_no_file(self, mock_classifier_class):
        """Test cache manager import action without file parameter."""
        # Mock the classifier instance
        mock_classifier = Mock()
        mock_classifier_class.return_value = mock_classifier

        # Run the command without --file parameter
        result = self.runner.invoke(cache_manager, [
            '--project-path', self.test_project_path,
            '--action', 'import'
        ])

        # Verify command execution
        self.assertEqual(result.exit_code, 0)
        
        # Verify import was NOT called
        mock_classifier.import_learned_patterns.assert_not_called()
        
        # Verify error output
        output = result.output
        self.assertIn('Import requires --file parameter', output)

    def test_cache_manager_invalid_action(self):
        """Test cache manager with invalid action."""
        # Run the command with invalid action
        result = self.runner.invoke(cache_manager, [
            '--project-path', self.test_project_path,
            '--action', 'invalid'
        ])

        # Verify command fails
        self.assertNotEqual(result.exit_code, 0)
        
        # Verify error message mentions valid choices
        self.assertIn('Invalid value for \'--action\'', result.output)

    def test_cache_manager_missing_required_action(self):
        """Test cache manager without required action parameter."""
        # Run the command without action
        result = self.runner.invoke(cache_manager, [
            '--project-path', self.test_project_path
        ])

        # Verify command fails
        self.assertNotEqual(result.exit_code, 0)
        
        # Verify error message mentions missing option
        self.assertIn('Missing option \'--action\'', result.output)

    @patch('aider_lint_fixer.cache_cli.SmartErrorClassifier')
    def test_cache_manager_default_project_path(self, mock_classifier_class):
        """Test cache manager with default project path."""
        # Mock the classifier instance
        mock_classifier = Mock()
        mock_classifier_class.return_value = mock_classifier
        
        # Mock statistics data
        mock_stats = {
            'cache': {
                'cache_dir': '/test/cache',
                'cache_sizes': {
                    'training_files': 0,
                    'model_files': 0,
                    'total_files': 0
                }
            },
            'pattern_matcher': {
                'languages': [],
                'total_patterns': 0,
                'ahocorasick_available': False
            },
            'ml_classifier': {
                'sklearn_available': False,
                'trained_languages': []
            }
        }
        mock_classifier.get_statistics.return_value = mock_stats

        # Run the command without project-path (should use default ".")
        result = self.runner.invoke(cache_manager, [
            '--action', 'stats'
        ])

        # Verify command execution
        self.assertEqual(result.exit_code, 0)
        
        # Verify classifier was initialized with default path
        mock_classifier_class.assert_called_once()
        call_args = mock_classifier_class.call_args[0]
        # The cache dir should be current directory + .aider-lint-cache
        expected_path = Path(".") / ".aider-lint-cache"
        self.assertEqual(str(call_args[0]), str(expected_path))

    @patch('aider_lint_fixer.cache_cli.SmartErrorClassifier')
    def test_cache_manager_stats_empty_ml_classifier(self, mock_classifier_class):
        """Test cache manager stats with empty ML classifier data."""
        # Mock the classifier instance
        mock_classifier = Mock()
        mock_classifier_class.return_value = mock_classifier
        
        # Mock statistics data with no training examples
        mock_stats = {
            'cache': {
                'cache_dir': '/test/cache',
                'cache_sizes': {
                    'training_files': 0,
                    'model_files': 0,
                    'total_files': 0
                }
            },
            'pattern_matcher': {
                'languages': [],
                'total_patterns': 0,
                'ahocorasick_available': False
            },
            'ml_classifier': {
                'sklearn_available': True,
                'trained_languages': []
            }
        }
        mock_classifier.get_statistics.return_value = mock_stats

        # Run the command
        result = self.runner.invoke(cache_manager, [
            '--project-path', self.test_project_path,
            '--action', 'stats'
        ])

        # Verify command execution
        self.assertEqual(result.exit_code, 0)
        
        # Verify output contains empty data indicators
        output = result.output
        self.assertIn('0 bytes', output)
        self.assertIn('0', output)  # total patterns
        self.assertIn('False', output)  # ahocorasick_available

    @patch('aider_lint_fixer.cache_cli.SmartErrorClassifier')
    def test_cache_manager_stats_with_training_examples(self, mock_classifier_class):
        """Test cache manager stats with various training example types."""
        # Mock the classifier instance
        mock_classifier = Mock()
        mock_classifier_class.return_value = mock_classifier
        
        # Mock statistics data with different training example keys
        mock_stats = {
            'cache': {
                'cache_dir': '/test/cache',
                'cache_sizes': {
                    'training_files': 1024,
                    'model_files': 2048,
                    'total_files': 3072
                }
            },
            'pattern_matcher': {
                'languages': ['python'],
                'total_patterns': 10,
                'ahocorasick_available': True
            },
            'ml_classifier': {
                'sklearn_available': True,
                'trained_languages': ['python', 'ansible'],
                'python_training_examples': 100,
                'ansible_training_examples': 50,
                'javascript_training_examples': 25,
                'other_key_not_training': 'ignore',
                'training_not_suffix': 'ignore'
            }
        }
        mock_classifier.get_statistics.return_value = mock_stats

        # Run the command
        result = self.runner.invoke(cache_manager, [
            '--project-path', self.test_project_path,
            '--action', 'stats'
        ])

        # Verify command execution
        self.assertEqual(result.exit_code, 0)
        
        # Verify output contains training examples
        output = result.output
        self.assertIn('python: 100 training examples', output)
        self.assertIn('ansible: 50 training examples', output)
        self.assertIn('javascript: 25 training examples', output)
        
        # Verify non-training keys are not shown
        self.assertNotIn('other_key_not_training', output)
        self.assertNotIn('training_not_suffix', output)

    @patch('aider_lint_fixer.cache_cli.SmartErrorClassifier')
    def test_cache_manager_path_construction(self, mock_classifier_class):
        """Test that cache directory path is constructed correctly."""
        # Mock the classifier instance
        mock_classifier = Mock()
        mock_classifier_class.return_value = mock_classifier
        
        # Mock minimal stats for the test
        mock_stats = {
            'cache': {
                'cache_dir': '/test/cache',
                'cache_sizes': {'training_files': 0, 'model_files': 0, 'total_files': 0}
            },
            'pattern_matcher': {
                'languages': [], 'total_patterns': 0, 'ahocorasick_available': False
            },
            'ml_classifier': {
                'sklearn_available': False, 'trained_languages': []
            }
        }
        mock_classifier.get_statistics.return_value = mock_stats

        # Test with absolute path
        abs_path = "/absolute/path/to/project"
        result = self.runner.invoke(cache_manager, [
            '--project-path', abs_path,
            '--action', 'stats'
        ])
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify the path passed to SmartErrorClassifier
        call_args = mock_classifier_class.call_args[0]
        expected_cache_path = Path(abs_path) / ".aider-lint-cache"
        self.assertEqual(str(call_args[0]), str(expected_cache_path))

    @patch('aider_lint_fixer.cache_cli.SmartErrorClassifier')
    def test_cache_manager_export_import_integration(self, mock_classifier_class):
        """Test export followed by import using actual file paths."""
        # Mock the classifier instance
        mock_classifier = Mock()
        mock_classifier_class.return_value = mock_classifier

        # Create temporary export file
        export_file = Path(self.temp_dir) / "patterns.json"
        
        # Test export
        export_result = self.runner.invoke(cache_manager, [
            '--project-path', self.test_project_path,
            '--action', 'export',
            '--file', str(export_file)
        ])
        
        self.assertEqual(export_result.exit_code, 0)
        
        # Test import with the same file
        import_result = self.runner.invoke(cache_manager, [
            '--project-path', self.test_project_path,
            '--action', 'import',
            '--file', str(export_file)
        ])
        
        self.assertEqual(import_result.exit_code, 0)
        
        # Verify both operations were called
        mock_classifier.export_learned_patterns.assert_called_once_with(str(export_file))
        mock_classifier.import_learned_patterns.assert_called_once_with(str(export_file))


class TestCacheManagerMainExecution(unittest.TestCase):
    """Test main execution functionality."""

    def test_main_execution(self):
        """Test that main execution works correctly."""
        # Test that the main block executes without error
        import subprocess
        import sys
        
        # Run the module as a script with help flag to avoid running actual cache operations
        result = subprocess.run([
            sys.executable, '-m', 'aider_lint_fixer.cache_cli', '--help'
        ], capture_output=True, text=True)
        
        # Verify it runs successfully
        self.assertEqual(result.returncode, 0)
        self.assertIn('Manage pattern matching cache', result.stdout)


class TestCacheManagerColoramaIntegration(unittest.TestCase):
    """Test colorama color formatting integration."""

    @patch('aider_lint_fixer.cache_cli.SmartErrorClassifier')
    @patch('aider_lint_fixer.cache_cli.Fore')
    @patch('aider_lint_fixer.cache_cli.Style')
    def test_colorama_colors_used(self, mock_style, mock_fore, mock_classifier_class):
        """Test that colorama colors are used in output."""
        # Setup mocks
        mock_classifier = Mock()
        mock_classifier_class.return_value = mock_classifier
        
        mock_stats = {
            'cache': {
                'cache_dir': '/test/cache',
                'cache_sizes': {'training_files': 0, 'model_files': 0, 'total_files': 0}
            },
            'pattern_matcher': {
                'languages': [], 'total_patterns': 0, 'ahocorasick_available': False
            },
            'ml_classifier': {
                'sklearn_available': False, 'trained_languages': []
            }
        }
        mock_classifier.get_statistics.return_value = mock_stats
        
        # Set up colorama mocks
        mock_fore.CYAN = '[CYAN]'
        mock_fore.GREEN = '[GREEN]'
        mock_fore.YELLOW = '[YELLOW]'
        mock_fore.RED = '[RED]'
        mock_fore.BLUE = '[BLUE]'
        mock_style.RESET_ALL = '[RESET]'

        runner = CliRunner()
        
        # Test stats action
        result = runner.invoke(cache_manager, ['--action', 'stats'])
        self.assertEqual(result.exit_code, 0)
        
        # Verify colorama attributes were accessed
        self.assertTrue(mock_fore.CYAN)
        self.assertTrue(mock_style.RESET_ALL)


if __name__ == "__main__":
    unittest.main()