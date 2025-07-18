"""
Test suite for new features added in recent releases.

This module tests:
1. Web scraping infrastructure
2. Enhanced pattern matching with scraped rules
3. CLI stats flag
4. Learning integration improvements
5. Multi-linter rule coverage
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from aider_lint_fixer.pattern_matcher import SmartErrorClassifier
from aider_lint_fixer.rule_scraper import RuleScraper, RuleInfo


class TestWebScrapingInfrastructure:
    """Test the web scraping system for linter rules."""
    
    def test_rule_scraper_initialization(self):
        """Test that RuleScraper initializes correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            scraper = RuleScraper(cache_dir)
            
            assert scraper.cache_dir == cache_dir
            assert "ansible-lint" in scraper.documentation_urls
            assert "eslint" in scraper.documentation_urls
            assert "flake8" in scraper.documentation_urls
    
    def test_rule_info_structure(self):
        """Test RuleInfo data structure."""
        rule = RuleInfo(
            rule_id="test-rule",
            category="formatting",
            auto_fixable=True,
            complexity="trivial",
            description="Test rule description",
            fix_strategy="formatting_fix",
            source_url="https://example.com/rule"
        )
        
        assert rule.rule_id == "test-rule"
        assert rule.auto_fixable is True
        assert rule.complexity == "trivial"
        assert rule.category == "formatting"
    
    @patch('requests.get')
    def test_scraper_handles_network_errors(self, mock_get):
        """Test that scraper handles network errors gracefully."""
        mock_get.side_effect = Exception("Network error")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            scraper = RuleScraper(cache_dir)
            
            # Should not raise exception
            result = scraper._scrape_url("https://example.com", "test-linter")
            assert isinstance(result, dict)
            assert len(result) == 0  # Empty result on error
    
    def test_scraped_rules_integration(self):
        """Test that scraped rules integrate with pattern matcher."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            
            # Create mock scraped rules file
            scraped_rules = {
                "ansible-lint": {
                    "yaml[line-length]": {
                        "rule_id": "yaml[line-length]",
                        "category": "formatting",
                        "auto_fixable": True,
                        "complexity": "trivial",
                        "description": "Line too long",
                        "fix_strategy": "formatting_fix",
                        "source_url": "https://example.com"
                    }
                }
            }
            
            scraped_file = cache_dir / "scraped_rules.json"
            with open(scraped_file, 'w') as f:
                json.dump(scraped_rules, f)
            
            # Test that classifier loads scraped rules
            classifier = SmartErrorClassifier(cache_dir)
            
            # Should have loaded the scraped rule
            assert "ansible-lint" in classifier.rule_knowledge.rule_database
            assert "yaml[line-length]" in classifier.rule_knowledge.rule_database["ansible-lint"]


class TestEnhancedPatternMatching:
    """Test enhanced pattern matching with comprehensive rule coverage."""
    
    def test_comprehensive_rule_coverage(self):
        """Test that pattern matcher handles multiple linter types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            classifier = SmartErrorClassifier(cache_dir)
            
            # Test ansible-lint classification
            result = classifier.classify_error(
                "Line too long (130 > 120 characters)",
                "ansible",
                "ansible-lint",
                "yaml[line-length]"
            )
            
            assert result.fixable is True
            assert result.confidence > 0.5
            assert result.method in ["rule_knowledge", "pattern_matching", "ml_classification"]
    
    def test_multi_language_support(self):
        """Test that classifier supports multiple languages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            classifier = SmartErrorClassifier(cache_dir)
            
            # Test different languages
            languages = ["python", "javascript", "ansible", "go", "rust"]
            
            for language in languages:
                result = classifier.classify_error(
                    f"Test error for {language}",
                    language,
                    f"{language}-linter",
                    "test-rule"
                )
                
                assert result is not None
                assert isinstance(result.fixable, bool)
                assert isinstance(result.confidence, float)
                assert 0.0 <= result.confidence <= 1.0
    
    def test_learning_integration_fix(self):
        """Test that the learning integration bug is fixed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            classifier = SmartErrorClassifier(cache_dir)
            
            # Test that ansible-lint errors are correctly mapped to "ansible" language
            initial_count = 0
            training_file = cache_dir / "ansible_training.json"
            
            if training_file.exists():
                with open(training_file, 'r') as f:
                    initial_count = len(json.load(f))
            
            # Learn from an ansible-lint error
            classifier.learn_from_fix(
                "Line too long (130 > 120 characters)",
                "ansible",  # Should be mapped correctly
                "ansible-lint",
                True
            )
            
            # Check that training data was saved to ansible_training.json
            assert training_file.exists()
            
            with open(training_file, 'r') as f:
                training_data = json.load(f)
            
            assert len(training_data) > initial_count
            
            # Verify the data structure
            latest_entry = training_data[-1]
            assert latest_entry["language"] == "ansible"
            assert latest_entry["linter"] == "ansible-lint"
            assert latest_entry["fixable"] is True


class TestCLIStatsFlag:
    """Test the new --stats flag in the main CLI."""
    
    def test_stats_flag_exists(self):
        """Test that --stats flag is available in CLI."""
        from click.testing import CliRunner
        from aider_lint_fixer.main import main
        
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert '--stats' in result.output
        assert 'Show learning statistics and exit' in result.output
    
    def test_stats_flag_functionality(self):
        """Test that --stats flag works correctly."""
        from click.testing import CliRunner
        from aider_lint_fixer.main import main
        
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = CliRunner()
            result = runner.invoke(main, ['--stats', temp_dir])
            
            assert result.exit_code == 0
            assert 'Pattern Cache Statistics' in result.output
            assert 'Pattern Matching' in result.output
            assert 'Machine Learning' in result.output
    
    def test_stats_json_output(self):
        """Test that --stats works with JSON output format."""
        from click.testing import CliRunner
        from aider_lint_fixer.main import main
        
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = CliRunner()
            result = runner.invoke(main, ['--stats', '--output-format', 'json', temp_dir])
            
            assert result.exit_code == 0
            
            # Should be valid JSON
            try:
                stats_data = json.loads(result.output)
                assert 'pattern_matcher' in stats_data
                assert 'ml_classifier' in stats_data
                assert 'cache' in stats_data
            except json.JSONDecodeError:
                pytest.fail("Stats output is not valid JSON")


class TestPerformanceImprovements:
    """Test performance improvements and optimizations."""
    
    def test_classification_speed(self):
        """Test that classification is fast enough for production use."""
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            classifier = SmartErrorClassifier(cache_dir)
            
            # Test classification speed
            test_cases = [
                ("Line too long", "python", "flake8", "E501"),
                ("Missing semicolon", "javascript", "eslint", "semi"),
                ("Indentation error", "ansible", "ansible-lint", "yaml[indentation]"),
            ]
            
            start_time = time.time()
            
            for message, language, linter, rule_id in test_cases:
                result = classifier.classify_error(message, language, linter, rule_id)
                assert result is not None
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / len(test_cases)
            
            # Should be very fast (less than 10ms per classification)
            assert avg_time < 0.01, f"Classification too slow: {avg_time:.3f}s per error"
    
    def test_cache_efficiency(self):
        """Test that caching improves performance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            classifier = SmartErrorClassifier(cache_dir)
            
            # Get cache statistics
            stats = classifier.get_statistics()
            
            assert 'cache' in stats
            assert 'cache_sizes' in stats['cache']
            
            # Cache should be reasonably sized (not too large)
            total_size = stats['cache']['cache_sizes']['total_files']
            assert total_size < 10 * 1024 * 1024  # Less than 10MB


class TestRegressionPrevention:
    """Test to prevent regressions in existing functionality."""
    
    def test_backward_compatibility(self):
        """Test that existing functionality still works."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            classifier = SmartErrorClassifier(cache_dir)
            
            # Test basic classification still works
            result = classifier.classify_error(
                "undefined variable 'foo'",
                "python",
                "pylint",
                "undefined-variable"
            )
            
            assert result is not None
            assert isinstance(result.fixable, bool)
            assert isinstance(result.confidence, float)
    
    def test_error_handling_robustness(self):
        """Test that system handles errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            classifier = SmartErrorClassifier(cache_dir)
            
            # Test with invalid inputs
            result = classifier.classify_error("", "", "", "")
            assert result is not None
            
            result = classifier.classify_error(None, None, None, None)
            assert result is not None
            
            # Should not raise exceptions
            try:
                classifier.learn_from_fix("test", "invalid-language", "invalid-linter", True)
            except Exception as e:
                pytest.fail(f"Learning should handle invalid inputs gracefully: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
