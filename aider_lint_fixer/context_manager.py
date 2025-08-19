#!/usr/bin/env python3
"""
Advanced Context Management for Extended Loop Execution

This module implements intelligent context summarization and history management
to maintain AI performance across multiple iterations, addressing context window
limitations that constrain extended loop execution.

Based on research findings that context window limitations in Large Language Models
create constraints for continuous loop systems, with the existing system's 8K token
limit meaning that extended loop execution may suffer from degraded AI performance
due to context pollution.

Key Features:
- Intelligent context summarization
- Essential information preservation
- Context pollution detection and cleanup
- Adaptive context window management
- Historical context compression
- Priority-based context retention
"""

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ContextPriority(Enum):
    """Priority levels for context information."""

    CRITICAL = "critical"  # Must preserve (current errors, active fixes)
    HIGH = "high"  # Important to preserve (recent successful patterns)
    MEDIUM = "medium"  # Useful to preserve (error patterns, file context)
    LOW = "low"  # Can be summarized (old iterations, verbose logs)


@dataclass
class ContextItem:
    """Represents a piece of context information."""

    content: str
    priority: ContextPriority
    timestamp: datetime
    category: str  # error, fix, pattern, metadata, etc.
    tokens: int = 0
    iteration: Optional[int] = None
    file_path: Optional[str] = None
    error_type: Optional[str] = None
    success: Optional[bool] = None


@dataclass
class ContextSummary:
    """Summarized context information."""

    original_items: int
    summarized_content: str
    tokens_saved: int
    summary_tokens: int
    categories_included: Set[str]
    time_range: Tuple[datetime, datetime]


class ContextManager:
    """Advanced context manager for extended loop execution."""

    def __init__(self, max_tokens: int = 8000, target_tokens: int = 6000):
        self.max_tokens = max_tokens
        self.target_tokens = target_tokens

        # Context storage
        self.context_items: List[ContextItem] = []
        self.summaries: List[ContextSummary] = []

        # Context tracking
        self.current_tokens = 0
        self.current_iteration = 0

        # Summarization settings
        self.summarization_threshold = 0.8  # Summarize when 80% of max tokens used
        self.critical_context_ratio = 0.4  # 40% of tokens reserved for critical context

        # Pattern tracking for intelligent preservation
        self.successful_patterns: Set[str] = set()
        self.failed_patterns: Set[str] = set()

    def add_context(
        self,
        content: str,
        priority: ContextPriority,
        category: str,
        iteration: Optional[int] = None,
        file_path: Optional[str] = None,
        error_type: Optional[str] = None,
        success: Optional[bool] = None,
    ) -> str:
        """Add context information with automatic management."""

        # Estimate token count (rough approximation: 1 token ≈ 4 characters)
        tokens = len(content) // 4

        context_item = ContextItem(
            content=content,
            priority=priority,
            timestamp=datetime.now(),
            category=category,
            tokens=tokens,
            iteration=iteration,
            file_path=file_path,
            error_type=error_type,
            success=success,
        )

        self.context_items.append(context_item)
        self.current_tokens += tokens

        # Update pattern tracking
        if success is not None:
            pattern_hash = self._extract_pattern_hash(content, error_type)
            if success:
                self.successful_patterns.add(pattern_hash)
            else:
                self.failed_patterns.add(pattern_hash)

        # Check if context management is needed
        if self.current_tokens > self.max_tokens * self.summarization_threshold:
            self._manage_context()

        return f"context_{len(self.context_items)}"

    def get_current_context(self, include_summaries: bool = True) -> str:
        """Get current context optimized for AI consumption."""

        # Sort context items by priority and recency
        sorted_items = sorted(
            self.context_items,
            key=lambda x: (x.priority.value, -x.timestamp.timestamp()),
        )

        context_parts = []
        used_tokens = 0

        # Reserve tokens for critical context
        critical_token_budget = int(self.target_tokens * self.critical_context_ratio)

        # Add critical context first
        for item in sorted_items:
            if (
                item.priority == ContextPriority.CRITICAL
                and used_tokens < critical_token_budget
            ):
                context_parts.append(self._format_context_item(item))
                used_tokens += item.tokens

        # Add other context by priority
        for priority in [
            ContextPriority.HIGH,
            ContextPriority.MEDIUM,
            ContextPriority.LOW,
        ]:
            for item in sorted_items:
                if (
                    item.priority == priority
                    and used_tokens < self.target_tokens
                    and item
                    not in [
                        i
                        for i in sorted_items
                        if i.priority == ContextPriority.CRITICAL
                    ]
                ):

                    if used_tokens + item.tokens <= self.target_tokens:
                        context_parts.append(self._format_context_item(item))
                        used_tokens += item.tokens

        # Add summaries if requested and space available
        if include_summaries and used_tokens < self.target_tokens:
            for summary in self.summaries[-3:]:  # Last 3 summaries
                if used_tokens + summary.summary_tokens <= self.target_tokens:
                    context_parts.append(self._format_summary(summary))
                    used_tokens += summary.summary_tokens

        return "\n\n".join(context_parts)

    def _manage_context(self):
        """Intelligently manage context to stay within token limits."""
        logger.info(
            f"Managing context: {self.current_tokens} tokens, {len(self.context_items)} items"
        )

        # Identify items for summarization (low priority, old items)
        items_to_summarize = []
        items_to_keep = []

        current_time = datetime.now()

        for item in self.context_items:
            age_hours = (current_time - item.timestamp).total_seconds() / 3600

            # Keep critical and recent high-priority items
            if (
                item.priority == ContextPriority.CRITICAL
                or (item.priority == ContextPriority.HIGH and age_hours < 1)
                or (item.priority == ContextPriority.MEDIUM and age_hours < 0.5)
            ):
                items_to_keep.append(item)
            else:
                items_to_summarize.append(item)

        # Summarize old items
        if items_to_summarize:
            summary = self._create_summary(items_to_summarize)
            self.summaries.append(summary)

            # Update context items and token count
            self.context_items = items_to_keep
            self.current_tokens = sum(item.tokens for item in items_to_keep)

            logger.info(
                f"Summarized {len(items_to_summarize)} items, "
                f"saved {summary.tokens_saved} tokens"
            )

    def _create_summary(self, items: List[ContextItem]) -> ContextSummary:
        """Create an intelligent summary of context items."""

        if not items:
            return ContextSummary(
                original_items=0,
                summarized_content="",
                tokens_saved=0,
                summary_tokens=0,
                categories_included=set(),
                time_range=(datetime.now(), datetime.now()),
            )

        # Group items by category
        categories = {}
        for item in items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)

        summary_parts = []

        # Summarize each category
        for category, category_items in categories.items():
            category_summary = self._summarize_category(category, category_items)
            if category_summary:
                summary_parts.append(f"## {category.title()}\n{category_summary}")

        # Create overall summary
        summarized_content = "\n\n".join(summary_parts)

        # Add key statistics
        success_count = sum(1 for item in items if item.success is True)
        failure_count = sum(1 for item in items if item.success is False)

        if success_count > 0 or failure_count > 0:
            stats = "\n\n## Summary Statistics\n"
            stats += f"- Successful operations: {success_count}\n"
            stats += f"- Failed operations: {failure_count}\n"
            stats += f"- Success rate: {success_count/(success_count+failure_count)*100:.1f}%\n"
            summarized_content += stats

        original_tokens = sum(item.tokens for item in items)
        summary_tokens = len(summarized_content) // 4

        return ContextSummary(
            original_items=len(items),
            summarized_content=summarized_content,
            tokens_saved=original_tokens - summary_tokens,
            summary_tokens=summary_tokens,
            categories_included=set(categories.keys()),
            time_range=(
                min(item.timestamp for item in items),
                max(item.timestamp for item in items),
            ),
        )

    def _summarize_category(self, category: str, items: List[ContextItem]) -> str:
        """Summarize items within a specific category."""

        if category == "error":
            return self._summarize_errors(items)
        elif category == "fix":
            return self._summarize_fixes(items)
        elif category == "pattern":
            return self._summarize_patterns(items)
        else:
            return self._summarize_generic(items)

    def _summarize_errors(self, items: List[ContextItem]) -> str:
        """Summarize error-related context items."""
        error_types = {}
        for item in items:
            error_type = item.error_type or "unknown"
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(item)

        summary_parts = []
        for error_type, error_items in error_types.items():
            files = set(item.file_path for item in error_items if item.file_path)
            summary_parts.append(
                f"- {error_type}: {len(error_items)} occurrences "
                f"across {len(files)} files"
            )

        return "\n".join(summary_parts)

    def _summarize_fixes(self, items: List[ContextItem]) -> str:
        """Summarize fix-related context items."""
        successful_fixes = [item for item in items if item.success is True]
        failed_fixes = [item for item in items if item.success is False]

        summary = f"- Successful fixes: {len(successful_fixes)}\n"
        summary += f"- Failed fixes: {len(failed_fixes)}\n"

        if successful_fixes:
            success_patterns = set()
            for item in successful_fixes:
                pattern = self._extract_pattern_hash(item.content, item.error_type)
                success_patterns.add(pattern)
            summary += f"- Unique successful patterns: {len(success_patterns)}\n"

        return summary

    def _summarize_patterns(self, items: List[ContextItem]) -> str:
        """Summarize pattern-related context items."""
        return f"- Pattern observations: {len(items)}\n"

    def _summarize_generic(self, items: List[ContextItem]) -> str:
        """Summarize generic context items."""
        return f"- Items processed: {len(items)}\n"

    def _format_context_item(self, item: ContextItem) -> str:
        """Format a context item for AI consumption."""
        header = f"[{item.priority.value.upper()}] {item.category.title()}"

        if item.iteration:
            header += f" (Iteration {item.iteration})"

        if item.file_path:
            header += f" - {item.file_path.split('/')[-1]}"

        if item.error_type:
            header += f" ({item.error_type})"

        return f"{header}:\n{item.content}"

    def _format_summary(self, summary: ContextSummary) -> str:
        """Format a summary for AI consumption."""
        time_range = f"{summary.time_range[0].strftime('%H:%M')} - {summary.time_range[1].strftime('%H:%M')}"
        header = f"[SUMMARY] {summary.original_items} items ({time_range})"
        return f"{header}:\n{summary.summarized_content}"

    def _extract_pattern_hash(self, content: str, error_type: Optional[str]) -> str:
        """Extract a pattern hash for tracking successful/failed patterns."""
        # Create a simplified pattern representation
        pattern_content = content.lower()

        # Remove variable names and specific values
        pattern_content = re.sub(r"\b\w+\b", "VAR", pattern_content)
        pattern_content = re.sub(r"\d+", "NUM", pattern_content)
        pattern_content = re.sub(r'["\'].*?["\']', "STR", pattern_content)

        # Include error type in pattern
        if error_type:
            pattern_content = f"{error_type}:{pattern_content}"

        # Create hash
        return hashlib.md5(pattern_content.encode()).hexdigest()[:8]

    def get_context_stats(self) -> Dict[str, any]:
        """Get statistics about current context usage."""
        return {
            "total_items": len(self.context_items),
            "total_tokens": self.current_tokens,
            "token_usage_percentage": (self.current_tokens / self.max_tokens) * 100,
            "summaries_created": len(self.summaries),
            "successful_patterns": len(self.successful_patterns),
            "failed_patterns": len(self.failed_patterns),
            "items_by_priority": {
                priority.value: len(
                    [item for item in self.context_items if item.priority == priority]
                )
                for priority in ContextPriority
            },
            "items_by_category": {
                category: len(
                    [item for item in self.context_items if item.category == category]
                )
                for category in set(item.category for item in self.context_items)
            },
        }

    def start_iteration(self, iteration: int):
        """Mark the start of a new iteration for context management."""
        self.current_iteration = iteration

        # Add iteration marker
        self.add_context(
            f"Starting iteration {iteration}",
            ContextPriority.HIGH,
            "iteration",
            iteration=iteration,
        )

    def preserve_successful_context(self, content: str, error_type: str):
        """Preserve context that led to successful fixes."""
        self.add_context(
            content,
            ContextPriority.HIGH,
            "successful_pattern",
            iteration=self.current_iteration,
            error_type=error_type,
            success=True,
        )
