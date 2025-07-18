"""
Community Issue Reporter for Aider Lint Fixer

This module provides functionality to create GitHub issues for successful fix patterns
that could benefit the community, integrating with the enhanced interactive mode.
"""

import json
import webbrowser
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

import click
from colorama import Fore, Style

from .enhanced_interactive import ManualFixAttempt


@dataclass
class CommunityIssue:
    """Represents a potential community issue to be created."""

    title: str
    body: str
    labels: List[str]
    error_pattern: str
    fix_pattern: str
    linter: str
    success_rate: float
    sample_count: int
    created_at: str


class CommunityIssueReporter:
    """Handles creation and management of community issues."""

    GITHUB_REPO = "aider-lint-fixer/aider-lint-fixer"  # Replace with actual repo
    MIN_SAMPLES_FOR_ISSUE = 2
    MIN_SUCCESS_RATE = 0.8  # 80%

    def __init__(self, project_root: str):
        """Initialize the community issue reporter."""
        self.project_root = project_root
        self.cache_dir = Path(project_root) / ".aider-lint-cache"
        self.cache_dir.mkdir(exist_ok=True)

        self.community_file = self.cache_dir / "community_feedback.json"
        self.issues_file = self.cache_dir / "community_issues.json"

    def analyze_for_community_issues(
        self, manual_attempts: List[ManualFixAttempt]
    ) -> List[CommunityIssue]:
        """Analyze manual fix attempts to identify potential community issues."""
        if not manual_attempts:
            return []

        # Group attempts by error pattern
        pattern_groups = {}
        for attempt in manual_attempts:
            pattern = f"{attempt.error.linter}:{attempt.error.rule_id}"
            if pattern not in pattern_groups:
                pattern_groups[pattern] = []
            pattern_groups[pattern].append(attempt)

        potential_issues = []

        for pattern, attempts in pattern_groups.items():
            # Only consider patterns with successful overrides
            successful_overrides = [a for a in attempts if a.user_attempted and a.fix_successful]

            if len(successful_overrides) >= self.MIN_SAMPLES_FOR_ISSUE:
                success_rate = len(successful_overrides) / len(attempts)

                if success_rate >= self.MIN_SUCCESS_RATE:
                    issue = self._create_community_issue(pattern, attempts, successful_overrides)
                    potential_issues.append(issue)

        return potential_issues

    def _create_community_issue(
        self,
        pattern: str,
        all_attempts: List[ManualFixAttempt],
        successful_attempts: List[ManualFixAttempt],
    ) -> CommunityIssue:
        """Create a community issue from successful fix patterns."""
        linter, rule_id = pattern.split(":", 1)
        sample_attempt = successful_attempts[0]

        # Generate issue title
        title = f"Enhancement: Improve {linter} {rule_id} fixability classification"

        # Generate issue body
        body = self._generate_issue_body(linter, rule_id, all_attempts, successful_attempts)

        # Determine labels
        labels = ["enhancement", "community-learning", f"linter-{linter.lower()}"]
        if sample_attempt.user_confidence >= 8:
            labels.append("high-confidence")

        return CommunityIssue(
            title=title,
            body=body,
            labels=labels,
            error_pattern=pattern,
            fix_pattern=successful_attempts[0].fix_description or "Manual fix applied",
            linter=linter,
            success_rate=len(successful_attempts) / len(all_attempts),
            sample_count=len(all_attempts),
            created_at=datetime.now().isoformat(),
        )

    def _generate_issue_body(
        self,
        linter: str,
        rule_id: str,
        all_attempts: List[ManualFixAttempt],
        successful_attempts: List[ManualFixAttempt],
    ) -> str:
        """Generate the GitHub issue body."""
        success_rate = len(successful_attempts) / len(all_attempts) * 100
        avg_confidence = sum(a.user_confidence for a in successful_attempts) / len(
            successful_attempts
        )

        # Get sample error details
        sample_error = successful_attempts[0].error

        body = f"""## 🎯 Enhancement Request: Improve {linter} {rule_id} Classification

### **Summary**
Users have successfully fixed errors of type `{rule_id}` that were originally classified as "unfixable" by the system. This suggests the classification algorithm could be improved.

### **Data Analysis**
- **Error Pattern**: `{linter}:{rule_id}`
- **Success Rate**: {success_rate:.1f}% ({len(successful_attempts)}/{len(all_attempts)} attempts)
- **Average User Confidence**: {avg_confidence:.1f}/10
- **Sample Error Message**: `{sample_error.message}`

### **Evidence**
"""

        # Add sample attempts
        for i, attempt in enumerate(successful_attempts[:3], 1):  # Show up to 3 examples
            body += f"""
**Attempt {i}:**
- File: `{attempt.error.file_path}:{attempt.error.line}`
- Original Classification: {"Fixable" if attempt.original_classification else "Unfixable"}
- User Override: {"Yes" if attempt.user_attempted else "No"}
- Fix Successful: {"Yes" if attempt.fix_successful else "No"}
- User Confidence: {attempt.user_confidence}/10
- Time to Fix: {attempt.time_to_fix_minutes or 'Unknown'} minutes
"""

        body += f"""
### **Recommendation**
Consider updating the error classification algorithm to mark `{linter}:{rule_id}` errors as fixable when they match similar patterns to the successful fixes above.

### **Impact**
- **Users**: Fewer manual overrides needed
- **Automation**: Higher automatic fix rate
- **Community**: Improved overall system accuracy

### **Implementation Suggestions**
1. Review the error patterns in successful fixes
2. Update classification rules for `{rule_id}` in `{linter}`
3. Add test cases to prevent regression
4. Update documentation if needed

### **Data Source**
This enhancement request was automatically generated from user feedback in the enhanced interactive mode community learning system.

**Generated on**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Aider Lint Fixer Version**: v1.8.0
"""

        return body

    def save_potential_issues(self, issues: List[CommunityIssue]) -> None:
        """Save potential community issues to cache."""
        if not issues:
            return

        # Load existing issues
        existing_issues = []
        if self.issues_file.exists():
            try:
                with open(self.issues_file, "r") as f:
                    existing_data = json.load(f)
                    existing_issues = [CommunityIssue(**item) for item in existing_data]
            except Exception:
                existing_issues = []

        # Add new issues (avoid duplicates)
        existing_patterns = {issue.error_pattern for issue in existing_issues}
        new_issues = [issue for issue in issues if issue.error_pattern not in existing_patterns]

        if new_issues:
            all_issues = existing_issues + new_issues

            # Save to file
            with open(self.issues_file, "w") as f:
                json.dump([asdict(issue) for issue in all_issues], f, indent=2)

            print(
                f"\n{Fore.GREEN}💾 Saved {len(new_issues)} potential community issues{Style.RESET_ALL}"
            )

    def list_potential_issues(self) -> List[CommunityIssue]:
        """List all potential community issues."""
        if not self.issues_file.exists():
            return []

        try:
            with open(self.issues_file, "r") as f:
                data = json.load(f)
                return [CommunityIssue(**item) for item in data]
        except Exception:
            return []

    def prompt_for_issue_creation(self) -> bool:
        """Prompt user to create community issues."""
        issues = self.list_potential_issues()

        if not issues:
            print(f"\n{Fore.YELLOW}No potential community issues found.{Style.RESET_ALL}")
            return False

        print(f"\n{Fore.CYAN}🌍 Community Issue Reporter{Style.RESET_ALL}")
        print(f"   Found {len(issues)} potential community contributions")

        for i, issue in enumerate(issues, 1):
            print(f"\n{i}. {issue.title}")
            print(f"   Pattern: {issue.error_pattern}")
            print(f"   Success Rate: {issue.success_rate:.1f}% ({issue.sample_count} samples)")
            print(f"   Labels: {', '.join(issue.labels)}")

        if click.confirm(f"\nWould you like to create GitHub issues for these improvements?"):
            return self._create_github_issues(issues)

        return False

    def _create_github_issues(self, issues: List[CommunityIssue]) -> bool:
        """Create GitHub issues (opens browser with pre-filled forms)."""
        print(f"\n{Fore.CYAN}🚀 Creating GitHub Issues{Style.RESET_ALL}")

        for i, issue in enumerate(issues, 1):
            print(f"\n{i}. Creating issue: {issue.title}")

            # Create GitHub issue URL with pre-filled content
            github_url = self._generate_github_issue_url(issue)

            print(f"   Opening browser for issue creation...")

            try:
                webbrowser.open(github_url)
                print(f"   ✅ Browser opened for issue creation")

                # Wait for user confirmation
                if not click.confirm("   Did you successfully create the issue?", default=True):
                    print(f"   ⏭️  Skipping this issue")
                    continue

            except Exception as e:
                print(f"   ❌ Failed to open browser: {e}")
                print(f"   💡 Manual URL: {github_url}")

        # Mark issues as processed
        self._mark_issues_processed(issues)

        print(f"\n{Fore.GREEN}🎉 Community issue creation process completed!{Style.RESET_ALL}")
        return True

    def _generate_github_issue_url(self, issue: CommunityIssue) -> str:
        """Generate a GitHub issue creation URL with pre-filled content."""
        base_url = f"https://github.com/{self.GITHUB_REPO}/issues/new"

        # URL encode the title and body
        title_encoded = quote(issue.title)
        body_encoded = quote(issue.body)
        labels_encoded = quote(",".join(issue.labels))

        return f"{base_url}?title={title_encoded}&body={body_encoded}&labels={labels_encoded}"

    def _mark_issues_processed(self, issues: List[CommunityIssue]) -> None:
        """Mark issues as processed (remove from pending list)."""
        try:
            # For now, we'll just clear the issues file
            # In a more sophisticated system, we'd track processed vs pending
            if self.issues_file.exists():
                self.issues_file.unlink()

            print(f"   📝 Marked {len(issues)} issues as processed")
        except Exception as e:
            print(f"   ⚠️  Warning: Could not mark issues as processed: {e}")


def integrate_community_issue_reporting(
    community_learning, manual_attempts: List[ManualFixAttempt]
) -> None:
    """Integrate community issue reporting with the enhanced interactive mode."""
    if not manual_attempts:
        return

    # Check if there are any successful overrides worth reporting
    successful_overrides = [a for a in manual_attempts if a.user_attempted and a.fix_successful]

    if not successful_overrides:
        return

    print(f"\n{Fore.CYAN}🌍 Community Learning Analysis{Style.RESET_ALL}")

    # Create issue reporter
    reporter = CommunityIssueReporter(community_learning.project_root)

    # Analyze for potential issues
    potential_issues = reporter.analyze_for_community_issues(manual_attempts)

    if potential_issues:
        print(f"   Found {len(potential_issues)} patterns that could benefit the community")

        # Save potential issues
        reporter.save_potential_issues(potential_issues)

        # Prompt for issue creation
        if click.confirm(
            "   Would you like to help improve the system by creating community issues?"
        ):
            reporter.prompt_for_issue_creation()
    else:
        print(f"   No patterns identified for community contribution yet")
        print(
            f"   (Need {reporter.MIN_SAMPLES_FOR_ISSUE}+ successful fixes with {reporter.MIN_SUCCESS_RATE*100}%+ success rate)"
        )
