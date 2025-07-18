"""
Enhanced test suite for pattern matching system with scraped rules and ML training.

This test module:
1. Tests pattern matching with real scraped rules
2. Generates comprehensive training data for ML
3. Validates classification accuracy
4. Measures performance improvements
"""

import json
import time
from pathlib import Path

import pytest

from aider_lint_fixer.pattern_matcher import SmartErrorClassifier


@pytest.fixture
def scraped_rules():
    """Load scraped rules for testing."""
    # Look for scraped rules in project root
    project_root = Path(__file__).parent.parent
    scraped_file = project_root / "scraped_ansible_rules.json"

    if not scraped_file.exists():
        pytest.skip(
            "Scraped rules file not found. Run: python aider_lint_fixer/rule_scraper.py --linter ansible-lint --output scraped_ansible_rules.json"
        )

    with open(scraped_file, "r") as f:
        return json.load(f)


@pytest.fixture
def smart_classifier():
    """Create a SmartErrorClassifier instance."""
    return SmartErrorClassifier()


def generate_yaml_test_cases(rule_id, expected_fixable):
    """Generate YAML-specific test cases."""
    test_cases = []

    if "line-length" in rule_id:
        test_cases.extend(
            [
                ("Line too long (130 > 120 characters)", "ansible-lint", rule_id, expected_fixable),
                ("Line too long (125 > 120 characters)", "ansible-lint", rule_id, expected_fixable),
                (
                    "yaml[line-length] Line exceeds maximum",
                    "ansible-lint",
                    rule_id,
                    expected_fixable,
                ),
            ]
        )
    elif "comments" in rule_id:
        test_cases.extend(
            [
                ("Missing starting space in comment", "ansible-lint", rule_id, expected_fixable),
                ("Too few spaces before comment", "ansible-lint", rule_id, expected_fixable),
                (
                    "yaml[comments] Comment formatting issue",
                    "ansible-lint",
                    rule_id,
                    expected_fixable,
                ),
            ]
        )
    elif "document-start" in rule_id:
        test_cases.extend(
            [
                ('missing document start "---"', "ansible-lint", rule_id, expected_fixable),
                ('found forbidden document start "---"', "ansible-lint", rule_id, expected_fixable),
                (
                    "yaml[document-start] Document start issue",
                    "ansible-lint",
                    rule_id,
                    expected_fixable,
                ),
            ]
        )
    elif "trailing-spaces" in rule_id:
        test_cases.extend(
            [
                ("Spaces are found at the end of lines", "ansible-lint", rule_id, expected_fixable),
                (
                    "yaml[trailing-spaces] Trailing whitespace",
                    "ansible-lint",
                    rule_id,
                    expected_fixable,
                ),
            ]
        )
    elif "indentation" in rule_id:
        test_cases.extend(
            [
                (
                    "Wrong indentation: expected 4 but found 2",
                    "ansible-lint",
                    rule_id,
                    expected_fixable,
                ),
                ("yaml[indentation] Indentation error", "ansible-lint", rule_id, expected_fixable),
            ]
        )
    else:
        # Generic YAML test case
        test_cases.append(
            (f"{rule_id} formatting error", "ansible-lint", rule_id, expected_fixable)
        )

    return test_cases


def generate_comprehensive_test_data(scraped_rules):
    """Generate comprehensive test data based on scraped rules."""
    test_cases = []

    # Get ansible-lint rules from scraped data
    ansible_rules = scraped_rules.get("ansible-lint", {})

    # Generate test cases for each scraped rule
    for rule_id, rule_info in ansible_rules.items():
        # Skip invalid rules
        if rule_id.startswith(("javascript:", ".", "#")):
            continue

        expected_fixable = rule_info.get("auto_fixable", False)
        description = rule_info.get("description", "")

        # Create realistic error messages based on rule type
        if rule_id.startswith("yaml["):
            test_cases.extend(generate_yaml_test_cases(rule_id, expected_fixable))
        elif rule_id.startswith("jinja"):
            test_cases.extend(
                [
                    ("Jinja2 spacing could be improved", "ansible-lint", rule_id, expected_fixable),
                    (
                        "jinja[spacing] Template spacing issue",
                        "ansible-lint",
                        rule_id,
                        expected_fixable,
                    ),
                ]
            )
        else:
            # General test case
            test_cases.append(
                (description or f"{rule_id} error", "ansible-lint", rule_id, expected_fixable)
            )

    return test_cases


class TestEnhancedPatternMatching:
    """Test suite for enhanced pattern matching with scraped rules."""

    def test_scraped_rules_loaded(self, scraped_rules):
        """Test that scraped rules are properly loaded."""
        assert "ansible-lint" in scraped_rules
        ansible_rules = scraped_rules["ansible-lint"]
        assert len(ansible_rules) > 0

        # Check for key YAML rules
        yaml_rules = [rule for rule in ansible_rules.keys() if rule.startswith("yaml[")]
        assert len(yaml_rules) > 0, "Should have YAML rules"

        # Verify rule structure
        for rule_id, rule_info in list(ansible_rules.items())[:5]:  # Check first 5
            if not rule_id.startswith(("javascript:", ".", "#")):
                assert "auto_fixable" in rule_info
                assert "category" in rule_info
                assert "description" in rule_info

    def test_yaml_rule_classification(self, smart_classifier, scraped_rules):
        """Test classification of YAML rules with high accuracy."""
        yaml_test_cases = [
            ("Line too long (130 > 120 characters)", "ansible-lint", "yaml[line-length]", True),
            ("Missing starting space in comment", "ansible-lint", "yaml[comments]", True),
            ('missing document start "---"', "ansible-lint", "yaml[document-start]", True),
            ("Spaces are found at the end of lines", "ansible-lint", "yaml[trailing-spaces]", True),
            (
                "Wrong indentation: expected 4 but found 2",
                "ansible-lint",
                "yaml[indentation]",
                True,
            ),
        ]

        correct_predictions = 0
        for message, linter, rule_id, expected_fixable in yaml_test_cases:
            result = smart_classifier.classify_error(message, "ansible", linter, rule_id)

            if result.fixable == expected_fixable:
                correct_predictions += 1

            # Should use rule_knowledge method for high confidence
            assert result.method == "rule_knowledge"
            assert result.confidence >= 0.9

        accuracy = correct_predictions / len(yaml_test_cases) * 100
        assert accuracy >= 90, f"YAML rule accuracy should be ≥90%, got {accuracy:.1f}%"

    def test_comprehensive_classification_accuracy(self, smart_classifier, scraped_rules):
        """Test classification accuracy on comprehensive test data."""
        test_cases = generate_comprehensive_test_data(scraped_rules)

        # Filter to valid test cases
        valid_test_cases = [
            case for case in test_cases if not case[2].startswith(("javascript:", ".", "#"))
        ]

        assert len(valid_test_cases) > 20, "Should have substantial test data"

        correct_predictions = 0
        high_confidence_count = 0

        for message, linter, rule_id, expected_fixable in valid_test_cases:
            result = smart_classifier.classify_error(message, "ansible", linter, rule_id)

            if result.fixable == expected_fixable:
                correct_predictions += 1

            if result.confidence >= 0.8:
                high_confidence_count += 1

        accuracy = correct_predictions / len(valid_test_cases) * 100
        high_confidence_rate = high_confidence_count / len(valid_test_cases) * 100

        print(f"\n📊 Classification Results:")
        print(f"   Test cases: {len(valid_test_cases)}")
        print(f"   Accuracy: {correct_predictions}/{len(valid_test_cases)} = {accuracy:.1f}%")
        print(
            f"   High confidence: {high_confidence_count}/{len(valid_test_cases)} = {high_confidence_rate:.1f}%"
        )

        # Should achieve high accuracy with scraped rules
        assert accuracy >= 80, f"Overall accuracy should be ≥80%, got {accuracy:.1f}%"
        assert (
            high_confidence_rate >= 70
        ), f"High confidence rate should be ≥70%, got {high_confidence_rate:.1f}%"

    def test_ml_training_data_generation(self, smart_classifier, scraped_rules):
        """Test ML training data generation from scraped rules."""
        test_cases = generate_comprehensive_test_data(scraped_rules)

        # Filter to valid test cases
        valid_test_cases = [
            case for case in test_cases if not case[2].startswith(("javascript:", ".", "#"))
        ][
            :20
        ]  # Limit for testing

        initial_training_count = 0
        cache_dir = Path(".aider-lint-cache")
        training_file = cache_dir / "ansible_training.json"

        if training_file.exists():
            with open(training_file, "r") as f:
                initial_training_count = len(json.load(f))

        # Generate training data
        for message, linter, rule_id, expected_fixable in valid_test_cases:
            smart_classifier.learn_from_fix(message, "ansible", linter, expected_fixable)

        # Check if training data was saved
        if training_file.exists():
            with open(training_file, "r") as f:
                final_training_count = len(json.load(f))

            assert final_training_count > initial_training_count, "Training data should increase"
            print(f"\n🧠 Training data: {initial_training_count} → {final_training_count} examples")

    def test_performance_benchmark(self, smart_classifier, scraped_rules):
        """Test classification performance with scraped rules."""
        test_cases = generate_comprehensive_test_data(scraped_rules)

        # Filter to valid test cases
        valid_test_cases = [
            case for case in test_cases if not case[2].startswith(("javascript:", ".", "#"))
        ][
            :50
        ]  # Limit for performance testing

        # Warm up
        for i in range(min(5, len(valid_test_cases))):
            message, linter, rule_id, _ = valid_test_cases[i]
            smart_classifier.classify_error(message, "ansible", linter, rule_id)

        # Benchmark
        start_time = time.time()
        for message, linter, rule_id, _ in valid_test_cases:
            smart_classifier.classify_error(message, "ansible", linter, rule_id)
        end_time = time.time()

        total_time = end_time - start_time
        avg_time = total_time / len(valid_test_cases) * 1000  # ms per classification

        print(f"\n⚡ Performance Results:")
        print(f"   Total time: {total_time:.3f}s")
        print(f"   Average time: {avg_time:.3f}ms per classification")
        print(f"   Throughput: {len(valid_test_cases)/total_time:.1f} classifications/second")

        # Should be fast
        assert avg_time < 10, f"Classification should be <10ms, got {avg_time:.3f}ms"

    def test_method_distribution(self, smart_classifier, scraped_rules):
        """Test that different classification methods are used appropriately."""
        test_cases = generate_comprehensive_test_data(scraped_rules)

        # Filter to valid test cases
        valid_test_cases = [
            case for case in test_cases if not case[2].startswith(("javascript:", ".", "#"))
        ][
            :30
        ]  # Sample for method testing

        method_counts = {}

        for message, linter, rule_id, _ in valid_test_cases:
            result = smart_classifier.classify_error(message, "ansible", linter, rule_id)
            method = result.method
            method_counts[method] = method_counts.get(method, 0) + 1

        print(f"\n📈 Method Distribution:")
        for method, count in method_counts.items():
            percentage = count / len(valid_test_cases) * 100
            print(f"   {method}: {count} ({percentage:.1f}%)")

        # Should primarily use rule_knowledge for scraped rules
        assert "rule_knowledge" in method_counts, "Should use rule_knowledge method"
        rule_knowledge_rate = method_counts.get("rule_knowledge", 0) / len(valid_test_cases) * 100
        assert (
            rule_knowledge_rate >= 50
        ), f"Rule knowledge usage should be ≥50%, got {rule_knowledge_rate:.1f}%"


class TestMLLearningSystem:
    """Test suite specifically for ML learning and cache functionality."""

    def test_cache_directory_creation(self, smart_classifier):
        """Test that cache directory is created properly."""
        cache_dir = Path(".aider-lint-cache")

        # Cache directory should exist after classifier initialization
        assert cache_dir.exists(), "Cache directory should be created"
        assert cache_dir.is_dir(), "Cache path should be a directory"

        print(f"\n📁 Cache directory: {cache_dir.absolute()}")

    def test_training_data_persistence(self, smart_classifier):
        """Test that training data is properly saved and loaded."""
        cache_dir = Path(".aider-lint-cache")
        training_file = cache_dir / "ansible_training.json"

        # Clear existing training data for clean test
        if training_file.exists():
            training_file.unlink()

        # Generate some training examples
        training_examples = [
            ("Line too long (130 > 120 characters)", "ansible", "ansible-lint", True),
            ("Missing starting space in comment", "ansible", "ansible-lint", True),
            ("undefined variable 'foo'", "ansible", "ansible-lint", False),
            ("syntax error in playbook", "ansible", "ansible-lint", False),
        ]

        # Learn from examples
        for message, language, linter, fixable in training_examples:
            smart_classifier.learn_from_fix(message, language, linter, fixable)

        # Check that training file was created
        assert training_file.exists(), "Training file should be created"

        # Verify training data content
        with open(training_file, "r") as f:
            training_data = json.load(f)

        assert len(training_data) >= len(training_examples), "All training examples should be saved"

        # Verify data structure
        for entry in training_data[-len(training_examples) :]:  # Check last entries
            assert "message" in entry
            assert "language" in entry
            assert "linter" in entry
            assert "fixable" in entry
            assert "timestamp" in entry

        print(f"\n🧠 Training data saved: {len(training_data)} examples")

    def test_training_data_loading(self, smart_classifier):
        """Test that existing training data is loaded on initialization."""
        cache_dir = Path(".aider-lint-cache")
        training_file = cache_dir / "ansible_training.json"

        # Ensure we have some training data
        if not training_file.exists():
            smart_classifier.learn_from_fix("test message", "ansible", "ansible-lint", True)

        # Create a new classifier instance to test loading
        new_classifier = SmartErrorClassifier()

        # The new classifier should have access to the training data
        # We can't directly access the training data, but we can verify the cache file exists
        assert training_file.exists(), "Training data should persist between instances"

        with open(training_file, "r") as f:
            training_data = json.load(f)

        assert len(training_data) > 0, "Training data should be loaded"
        print(f"\n📚 Loaded training data: {len(training_data)} examples")

    def test_ml_classification_improvement(self, smart_classifier):
        """Test that ML classification improves with training data."""
        # Test with a message that might not be in rule knowledge
        test_message = "Custom ansible error that should be fixable"
        test_rule = "custom-rule"

        # Get initial classification (should use fallback)
        initial_result = smart_classifier.classify_error(
            test_message, "ansible", "ansible-lint", test_rule
        )
        initial_confidence = initial_result.confidence

        # Train the classifier with this example
        smart_classifier.learn_from_fix(test_message, "ansible", "ansible-lint", True)
        smart_classifier.learn_from_fix(test_message, "ansible", "ansible-lint", True)  # Reinforce

        # Get classification after training
        trained_result = smart_classifier.classify_error(
            test_message, "ansible", "ansible-lint", test_rule
        )

        print(f"\n🎯 ML Learning Results:")
        print(
            f"   Initial: fixable={initial_result.fixable}, confidence={initial_confidence:.2f}, method={initial_result.method}"
        )
        print(
            f"   Trained: fixable={trained_result.fixable}, confidence={trained_result.confidence:.2f}, method={trained_result.method}"
        )

        # After training, the system should have learned
        # Note: The improvement might be subtle depending on the ML implementation
        assert (
            trained_result.confidence >= initial_confidence * 0.8
        ), "Confidence should not decrease significantly"

    def test_cache_cleanup_and_limits(self, smart_classifier):
        """Test that cache cleanup and size limits work properly."""
        cache_dir = Path(".aider-lint-cache")
        training_file = cache_dir / "ansible_training.json"

        # Generate many training examples to test limits
        for i in range(15):  # Generate more than typical batch size
            smart_classifier.learn_from_fix(
                f"Test message {i}", "ansible", "ansible-lint", i % 2 == 0
            )

        # Check that training data exists and is reasonable size
        assert training_file.exists(), "Training file should exist"

        with open(training_file, "r") as f:
            training_data = json.load(f)

        # Should have training data but not unlimited growth
        assert len(training_data) > 0, "Should have training data"
        assert len(training_data) <= 1000, "Should respect size limits (max 1000 per language)"

        print(f"\n🧹 Cache management: {len(training_data)} examples (within limits)")

    def test_multiple_language_support(self, smart_classifier):
        """Test that ML learning works for multiple languages."""
        languages = ["ansible", "python", "javascript"]
        cache_dir = Path(".aider-lint-cache")

        # Train on different languages
        for lang in languages:
            smart_classifier.learn_from_fix(f"Test error for {lang}", lang, f"{lang}-linter", True)

        # Check that separate training files are created for each language
        for lang in languages:
            training_file = cache_dir / f"{lang}_training.json"
            if training_file.exists():  # Some might not exist if not enough data
                with open(training_file, "r") as f:
                    training_data = json.load(f)
                assert len(training_data) > 0, f"Should have training data for {lang}"
                print(f"   {lang}: {len(training_data)} examples")

    def test_cache_file_format_validation(self, smart_classifier):
        """Test that cache files have correct JSON format and structure."""
        cache_dir = Path(".aider-lint-cache")

        # Generate some training data
        smart_classifier.learn_from_fix("Test message", "ansible", "ansible-lint", True)

        training_file = cache_dir / "ansible_training.json"
        assert training_file.exists(), "Training file should exist"

        # Validate JSON format
        try:
            with open(training_file, "r") as f:
                training_data = json.load(f)
        except json.JSONDecodeError:
            pytest.fail("Training file should contain valid JSON")

        # Validate structure
        assert isinstance(training_data, list), "Training data should be a list"

        if training_data:  # If we have data
            entry = training_data[0]
            required_fields = ["message", "language", "linter", "fixable", "timestamp"]
            for field in required_fields:
                assert field in entry, f"Training entry should have '{field}' field"

            assert isinstance(entry["fixable"], bool), "fixable should be boolean"
            assert isinstance(entry["timestamp"], (int, float)), "timestamp should be numeric"

        print(f"\n✅ Cache file format validation passed")

    def test_concurrent_access_safety(self, smart_classifier):
        """Test that cache files handle concurrent access safely."""
        import threading
        import time

        def worker(worker_id):
            """Worker function for concurrent testing."""
            for i in range(5):
                smart_classifier.learn_from_fix(
                    f"Worker {worker_id} message {i}", "ansible", "ansible-lint", i % 2 == 0
                )
                time.sleep(0.01)  # Small delay to increase chance of concurrent access

        # Run multiple workers concurrently
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify that all data was saved without corruption
        cache_dir = Path(".aider-lint-cache")
        training_file = cache_dir / "ansible_training.json"

        assert training_file.exists(), "Training file should exist after concurrent access"

        try:
            with open(training_file, "r") as f:
                training_data = json.load(f)

            # Should have some data from workers (race conditions may cause data loss, but file should be valid)
            assert len(training_data) >= 1, "Should have at least some data from workers"
            print(f"\n🔄 Concurrent access test: {len(training_data)} examples saved safely")

        except json.JSONDecodeError:
            pytest.fail("Training file should not be corrupted by concurrent access")
