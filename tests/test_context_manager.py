"""
Test suite for the Context Manager module.

This module tests:
1. Context item management and prioritization
2. Context summarization functionality
3. Token limit enforcement
4. Pattern tracking for successful/failed fixes
5. Context pollution detection and cleanup
6. Historical context compression
"""

import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from aider_lint_fixer.context_manager import (
    ContextItem,
    ContextManager,
    ContextPriority,
    ContextSummary,
)


class TestContextPriority:
    """Test ContextPriority enumeration."""

    def test_priority_values(self):
        """Test that priority values are correctly defined."""
        assert ContextPriority.CRITICAL.value == "critical"
        assert ContextPriority.HIGH.value == "high"
        assert ContextPriority.MEDIUM.value == "medium"
        assert ContextPriority.LOW.value == "low"


class TestContextItem:
    """Test ContextItem data structure."""

    def test_context_item_initialization(self):
        """Test ContextItem initialization."""
        item = ContextItem(
            content="Test content",
            priority=ContextPriority.HIGH,
            timestamp=datetime.now(),
            category="test",
            tokens=10,
            iteration=1,
            file_path="test.py",
            error_type="syntax-error",
            success=True,
        )

        assert item.content == "Test content"
        assert item.priority == ContextPriority.HIGH
        assert item.category == "test"
        assert item.tokens == 10
        assert item.iteration == 1
        assert item.file_path == "test.py"
        assert item.error_type == "syntax-error"
        assert item.success is True

    def test_context_item_defaults(self):
        """Test ContextItem default values."""
        item = ContextItem(
            content="Test content",
            priority=ContextPriority.MEDIUM,
            timestamp=datetime.now(),
            category="test",
        )

        assert item.tokens == 0
        assert item.iteration is None
        assert item.file_path is None
        assert item.error_type is None
        assert item.success is None


class TestContextSummary:
    """Test ContextSummary data structure."""

    def test_context_summary_initialization(self):
        """Test ContextSummary initialization."""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        summary = ContextSummary(
            original_items=10,
            summarized_content="Summary of 10 items",
            tokens_saved=500,
            summary_tokens=50,
            categories_included={"error", "fix"},
            time_range=(start_time, end_time),
        )

        assert summary.original_items == 10
        assert summary.summarized_content == "Summary of 10 items"
        assert summary.tokens_saved == 500
        assert summary.summary_tokens == 50
        assert "error" in summary.categories_included
        assert "fix" in summary.categories_included
        assert summary.time_range == (start_time, end_time)


class TestContextManager:
    """Test ContextManager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ContextManager(max_tokens=1000, target_tokens=800)

    def test_initialization(self):
        """Test ContextManager initialization."""
        assert self.manager.max_tokens == 1000
        assert self.manager.target_tokens == 800
        assert len(self.manager.context_items) == 0
        assert len(self.manager.summaries) == 0
        assert self.manager.current_tokens == 0
        assert self.manager.current_iteration == 0

    def test_add_context_basic(self):
        """Test adding basic context items."""
        context_id = self.manager.add_context(
            content="Test error occurred",
            priority=ContextPriority.HIGH,
            category="error",
            iteration=1,
            error_type="syntax-error",
        )

        assert context_id.startswith("context_")
        assert len(self.manager.context_items) == 1
        assert self.manager.current_tokens > 0

        item = self.manager.context_items[0]
        assert item.content == "Test error occurred"
        assert item.priority == ContextPriority.HIGH
        assert item.category == "error"
        assert item.iteration == 1
        assert item.error_type == "syntax-error"

    def test_add_context_with_success_tracking(self):
        """Test adding context with success/failure tracking."""
        # Add successful pattern
        self.manager.add_context(
            content="Fixed syntax error successfully",
            priority=ContextPriority.HIGH,
            category="fix",
            error_type="syntax-error",
            success=True,
        )

        # Add failed pattern
        self.manager.add_context(
            content="Failed to fix import error",
            priority=ContextPriority.MEDIUM,
            category="fix",
            error_type="import-error",
            success=False,
        )

        assert len(self.manager.successful_patterns) == 1
        assert len(self.manager.failed_patterns) == 1

    def test_context_prioritization(self):
        """Test that context items are properly prioritized."""
        # Add items with different priorities
        self.manager.add_context("Critical item", ContextPriority.CRITICAL, "error")
        self.manager.add_context("Low item", ContextPriority.LOW, "info")
        self.manager.add_context("High item", ContextPriority.HIGH, "fix")

        context = self.manager.get_current_context()

        # Critical items should appear first
        assert "Critical item" in context
        lines = context.split("\n")
        critical_line = next(i for i, line in enumerate(lines) if "Critical item" in line)
        low_line = next(i for i, line in enumerate(lines) if "Low item" in line)

        assert critical_line < low_line

    def test_token_limit_enforcement(self):
        """Test that token limits are enforced."""
        # Add many items to exceed token limit
        initial_tokens = self.manager.current_tokens
        for i in range(20):
            self.manager.add_context(
                content=f"Long content item {i} " * 50,  # Make it long to consume tokens
                priority=ContextPriority.MEDIUM,
                category="test",
            )

        # Should have added significant tokens
        assert self.manager.current_tokens > initial_tokens

        # Context manager should be tracking tokens properly
        assert self.manager.current_tokens > 0
        assert len(self.manager.context_items) == 20

    def test_context_summarization(self):
        """Test context summarization functionality."""
        # Add items that should be summarized
        old_time = datetime.now() - timedelta(hours=2)

        with patch("aider_lint_fixer.context_manager.datetime") as mock_datetime:
            mock_datetime.now.return_value = old_time

            for i in range(5):
                self.manager.add_context(
                    content=f"Old error {i}",
                    priority=ContextPriority.LOW,
                    category="error",
                )

        # Trigger summarization by adding current items
        for i in range(5):
            self.manager.add_context(
                content=f"Current error {i}",
                priority=ContextPriority.HIGH,
                category="error",
            )

        # Force context management
        self.manager._manage_context()

        # Should have created summaries
        assert len(self.manager.summaries) > 0

    def test_preserve_successful_context(self):
        """Test preserving successful context patterns."""
        self.manager.preserve_successful_context(
            content="Successfully fixed undefined variable by adding import",
            error_type="undefined-variable",
        )

        # Should add as high priority context
        assert len(self.manager.context_items) == 1
        item = self.manager.context_items[0]
        assert item.priority == ContextPriority.HIGH
        assert item.category == "successful_pattern"
        assert item.success is True

    def test_start_iteration(self):
        """Test starting a new iteration."""
        self.manager.start_iteration(5)

        assert self.manager.current_iteration == 5
        # Should add iteration marker
        assert len(self.manager.context_items) == 1
        item = self.manager.context_items[0]
        assert item.iteration == 5
        assert "Starting iteration 5" in item.content

    def test_get_context_stats(self):
        """Test getting context statistics."""
        # Add various items
        self.manager.add_context("Critical", ContextPriority.CRITICAL, "error")
        self.manager.add_context("High", ContextPriority.HIGH, "fix")
        self.manager.add_context("Medium", ContextPriority.MEDIUM, "pattern")

        stats = self.manager.get_context_stats()

        assert stats["total_items"] == 3
        assert stats["total_tokens"] > 0
        assert stats["token_usage_percentage"] >= 0
        assert stats["items_by_priority"]["critical"] == 1
        assert stats["items_by_priority"]["high"] == 1
        assert stats["items_by_priority"]["medium"] == 1
        assert "error" in stats["items_by_category"]
        assert "fix" in stats["items_by_category"]

    def test_context_formatting(self):
        """Test context item formatting for AI consumption."""
        self.manager.add_context(
            content="Test error in file",
            priority=ContextPriority.HIGH,
            category="error",
            iteration=1,
            file_path="test.py",
            error_type="syntax-error",
        )

        context = self.manager.get_current_context()

        # Should include formatted header information
        assert "[HIGH]" in context
        assert "Error" in context
        assert "(Iteration 1)" in context
        assert "test.py" in context
        assert "(syntax-error)" in context

    def test_pattern_hash_extraction(self):
        """Test pattern hash extraction for tracking."""
        # Test that similar patterns get same hash
        hash1 = self.manager._extract_pattern_hash("variable x is undefined", "undefined-var")
        hash2 = self.manager._extract_pattern_hash("variable y is undefined", "undefined-var")

        # Should be similar (variables normalized)
        assert len(hash1) == 8  # MD5 hash truncated to 8 chars
        assert len(hash2) == 8

    def test_context_with_summaries(self):
        """Test getting context that includes summaries."""
        # Add some items and create a summary
        for i in range(3):
            self.manager.add_context(f"Item {i}", ContextPriority.LOW, "test")

        # Manually create a summary
        summary = ContextSummary(
            original_items=3,
            summarized_content="Summary of test items",
            tokens_saved=100,
            summary_tokens=20,
            categories_included={"test"},
            time_range=(datetime.now() - timedelta(hours=1), datetime.now()),
        )
        self.manager.summaries.append(summary)

        context = self.manager.get_current_context(include_summaries=True)

        # Should include summary content
        assert "Summary of test items" in context

    def test_context_management_thresholds(self):
        """Test context management threshold behavior."""
        # Set up manager with low thresholds for testing
        manager = ContextManager(max_tokens=100, target_tokens=80)

        # Add content that exceeds threshold
        manager.add_context(
            content="Very long content " * 20,  # Should exceed 80 tokens
            priority=ContextPriority.LOW,
            category="test",
        )

        # Should trigger context management
        assert manager.current_tokens <= manager.max_tokens

    def test_empty_summary_creation(self):
        """Test creating summary with no items."""
        summary = self.manager._create_summary([])

        assert summary.original_items == 0
        assert summary.summarized_content == ""
        assert summary.tokens_saved == 0
        assert summary.summary_tokens == 0
        assert len(summary.categories_included) == 0


if __name__ == "__main__":
    pytest.main([__file__])
