#!/usr/bin/env python3
"""
Community Learning System Prototype

This demonstrates how we could create a dual-purpose learning system that:
1. Improves local project classification through manual fix feedback
2. Generates GitHub issues to share successful fix patterns with the community
"""

import json
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from aider_lint_fixer.error_analyzer import ErrorAnalysis
from aider_lint_fixer.lint_runner import LintError


@dataclass
class ManualFixAttempt:
    """Record of a user's manual fix attempt."""

    error: LintError
    original_classification: bool  # Was it originally classified as fixable?
    user_attempted: bool
    fix_successful: bool
    fix_description: str
    fix_diff: Optional[str] = None
    time_to_fix_minutes: Optional[int] = None
    user_confidence: int = 5  # 1-10 scale
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class CommunityContribution:
    """Potential contribution to the community."""

    error_pattern: str
    fix_pattern: str
    linter: str
    language: str
    success_rate: float
    sample_count: int
    github_issue_title: str
    github_issue_body: str


class CommunityLearningSystem:
    """System for learning from manual fixes and contributing to community."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.learning_cache = self.project_root / ".aider-lint-cache"
        self.manual_fixes_file = self.learning_cache / "manual_fixes.json"
        self.community_contributions = (
            self.learning_cache / "community_contributions.json"
        )

        # Ensure cache directory exists
        self.learning_cache.mkdir(exist_ok=True)

    def record_manual_fix_attempt(self, attempt: ManualFixAttempt):
        """Record a manual fix attempt for learning."""
        # Load existing attempts
        attempts = self._load_manual_fixes()

        # Convert to JSON-serializable format
        attempt_dict = asdict(attempt)
        # Convert enum to string
        if "error" in attempt_dict and "severity" in attempt_dict["error"]:
            attempt_dict["error"]["severity"] = attempt_dict["error"]["severity"].value

        # Add new attempt
        attempts.append(attempt_dict)

        # Save updated attempts
        with open(self.manual_fixes_file, "w") as f:
            json.dump(attempts, f, indent=2)

        # Update local learning
        self._update_local_learning(attempt)

        # Check if this could be a community contribution
        if attempt.fix_successful and not attempt.original_classification:
            self._evaluate_community_contribution(attempt)

    def _load_manual_fixes(self) -> List[Dict[str, Any]]:
        """Load existing manual fix attempts."""
        if not self.manual_fixes_file.exists():
            return []

        try:
            with open(self.manual_fixes_file, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _update_local_learning(self, attempt: ManualFixAttempt):
        """Update local learning system with manual fix results."""
        # This would integrate with the existing SmartErrorClassifier
        print(
            f"🧠 Local Learning: Recording {attempt.error.rule_id} -> {attempt.fix_successful}"
        )

        # Example: Update pattern matching for similar errors
        if attempt.fix_successful and not attempt.original_classification:
            print(
                f"   📈 Upgrading classification for pattern: {attempt.error.message[:50]}..."
            )
        elif not attempt.fix_successful and attempt.original_classification:
            print(
                f"   📉 Downgrading classification for pattern: {attempt.error.message[:50]}..."
            )

    def _evaluate_community_contribution(self, attempt: ManualFixAttempt):
        """Evaluate if this fix could benefit the community."""
        # Analyze if this is a pattern worth sharing
        similar_attempts = self._find_similar_attempts(attempt)

        if len(similar_attempts) >= 2:  # Need multiple successful fixes
            success_rate = sum(
                1 for a in similar_attempts if a["fix_successful"]
            ) / len(similar_attempts)

            if success_rate >= 0.8:  # 80% success rate threshold
                contribution = self._create_community_contribution(
                    attempt, similar_attempts
                )
                self._save_community_contribution(contribution)
                print(
                    f"🌟 Community Contribution Identified: {contribution.github_issue_title}"
                )

    def _find_similar_attempts(self, attempt: ManualFixAttempt) -> List[Dict[str, Any]]:
        """Find similar manual fix attempts."""
        attempts = self._load_manual_fixes()

        similar = []
        for existing in attempts:
            if (
                existing["error"]["rule_id"] == attempt.error.rule_id
                and existing["error"]["linter"] == attempt.error.linter
            ):
                similar.append(existing)

        return similar

    def _create_community_contribution(
        self, attempt: ManualFixAttempt, similar_attempts: List[Dict]
    ) -> CommunityContribution:
        """Create a community contribution from successful fix patterns."""
        error = attempt.error
        success_count = sum(1 for a in similar_attempts if a["fix_successful"])

        # Generate GitHub issue content
        title = f"Enhancement: Improve {error.linter} {error.rule_id} classification"

        body = f"""## 🎯 Enhancement Request

### **Issue Description**
Users are successfully fixing errors that are currently classified as "unfixable" by the learning system.

### **Error Pattern**
- **Linter**: {error.linter}
- **Rule ID**: {error.rule_id}
- **Message Pattern**: `{error.message}`
- **Current Classification**: Not automatically fixable

### **Evidence from Real Usage**
- **Success Rate**: {success_count}/{len(similar_attempts)} attempts successful ({success_count/len(similar_attempts)*100:.1f}%)
- **User Confidence**: Average {sum(a.get('user_confidence', 5) for a in similar_attempts)/len(similar_attempts):.1f}/10

### **Example Fix Description**
{attempt.fix_description}

### **Suggested Enhancement**
Update the error classification logic to recognize this pattern as automatically fixable:

```python
# Add to pattern matcher
if error.linter == "{error.linter}" and "{error.rule_id}" in error.rule_id:
    if "{error.message.lower()[:30]}" in error.message.lower():
        return True  # This pattern is actually fixable
```

### **Benefits**
- Improve fixability rate for {error.linter} projects
- Reduce manual intervention needed for common issues
- Better user experience for similar error patterns

### **Data Source**
This enhancement request was automatically generated from user feedback in the community learning system.
"""

        return CommunityContribution(
            error_pattern=f"{error.linter}:{error.rule_id}",
            fix_pattern=attempt.fix_description,
            linter=error.linter,
            language="ansible" if error.linter == "ansible-lint" else "unknown",
            success_rate=success_count / len(similar_attempts),
            sample_count=len(similar_attempts),
            github_issue_title=title,
            github_issue_body=body,
        )

    def _save_community_contribution(self, contribution: CommunityContribution):
        """Save a potential community contribution."""
        contributions = []
        if self.community_contributions.exists():
            try:
                with open(self.community_contributions, "r") as f:
                    contributions = json.load(f)
            except Exception:
                pass

        contributions.append(asdict(contribution))

        with open(self.community_contributions, "w") as f:
            json.dump(contributions, f, indent=2)

    def generate_github_issues(
        self, auto_create: bool = False
    ) -> List[CommunityContribution]:
        """Generate GitHub issues for community contributions."""
        if not self.community_contributions.exists():
            return []

        with open(self.community_contributions, "r") as f:
            contributions_data = json.load(f)

        contributions = [CommunityContribution(**data) for data in contributions_data]

        print(f"📋 Found {len(contributions)} potential community contributions:")

        for i, contrib in enumerate(contributions, 1):
            print(f"\n{i}. {contrib.github_issue_title}")
            print(f"   Pattern: {contrib.error_pattern}")
            print(
                f"   Success Rate: {contrib.success_rate:.1f}% ({contrib.sample_count} samples)"
            )

            if auto_create:
                # This would integrate with GitHub API
                print(f"   🚀 Would create GitHub issue automatically")
            else:
                print(f"   💡 Run with --create-issues to submit to GitHub")

        return contributions


def demonstrate_community_learning():
    """Demonstrate the community learning system."""
    print("🌍 Community Learning System Demo")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as temp_dir:
        system = CommunityLearningSystem(temp_dir)

        # Simulate user fixing an "unfixable" error
        from aider_lint_fixer.lint_runner import ErrorSeverity, LintError

        error = LintError(
            file_path="roles/test/tasks/main.yml",
            line=10,
            column=1,
            rule_id="yaml[trailing-spaces]",
            message="Trailing spaces",
            severity=ErrorSeverity.ERROR,
            linter="ansible-lint",
            context="",
            fix_suggestion="",
        )

        # Record multiple successful manual fixes
        for i in range(3):
            attempt = ManualFixAttempt(
                error=error,
                original_classification=False,  # Was classified as unfixable
                user_attempted=True,
                fix_successful=True,
                fix_description="Removed trailing whitespace from YAML file",
                time_to_fix_minutes=1,
                user_confidence=9,
            )

            system.record_manual_fix_attempt(attempt)

        # Generate community contributions
        contributions = system.generate_github_issues()

        print(
            f"\n🎯 Result: System identified {len(contributions)} patterns for community contribution!"
        )


if __name__ == "__main__":
    demonstrate_community_learning()
