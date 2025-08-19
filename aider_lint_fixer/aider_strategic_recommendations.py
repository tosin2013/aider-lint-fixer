#!/usr/bin/env python3
"""
Aider-Powered Strategic Recommendations System

Uses aider.chat to generate specific, actionable recommendations for cleaning up
chaotic codebases before proceeding with automated lint fixing.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .strategic_preflight_check import ChaosIndicator, ChaosLevel


@dataclass
class AiderRecommendation:
    """A specific recommendation from aider for codebase cleanup."""

    category: str
    priority: str
    title: str
    description: str
    specific_actions: List[str]
    files_affected: List[str]
    estimated_time: str
    aider_commands: List[str]


class AiderStrategicRecommendationEngine:
    """Generates strategic recommendations using aider.chat."""

    def __init__(self, project_path: str, config_manager=None):
        self.project_path = Path(project_path)
        self.config_manager = config_manager
        self.temp_dir = None

    def generate_recommendations(
        self, chaos_level: ChaosLevel, indicators: List[ChaosIndicator]
    ) -> List[AiderRecommendation]:
        """Generate strategic recommendations using aider."""

        print("\n🤖 Generating aider-powered strategic recommendations...")

        recommendations = []

        # Generate recommendations for each type of chaos indicator
        for indicator in indicators:
            if indicator.severity in ["critical", "major"]:
                rec = self._generate_indicator_recommendation(indicator, chaos_level)
                if rec:
                    recommendations.append(rec)

        # Generate overall project structure recommendations
        if chaos_level in [ChaosLevel.CHAOTIC, ChaosLevel.DISASTER]:
            structure_rec = self._generate_structure_recommendation(chaos_level, indicators)
            if structure_rec:
                recommendations.append(structure_rec)

        return recommendations

    def _generate_indicator_recommendation(
        self, indicator: ChaosIndicator, chaos_level: ChaosLevel
    ) -> Optional[AiderRecommendation]:
        """Generate recommendation for a specific chaos indicator."""

        if indicator.type == "file_organization":
            return self._generate_file_organization_recommendation(indicator)
        elif indicator.type == "code_structure":
            return self._generate_code_structure_recommendation(indicator)
        elif indicator.type == "documentation":
            return self._generate_documentation_recommendation(indicator)

        return None

    def _generate_file_organization_recommendation(
        self, indicator: ChaosIndicator
    ) -> AiderRecommendation:
        """Generate file organization recommendations."""

        # Analyze current file structure
        python_files = list(self.project_path.glob("*.py"))

        # Create aider prompt for file organization
        prompt = """
Analyze this Python project's file organization and provide specific refactoring recommendations.

Current issues detected:
- {indicator.description}
- Evidence: {', '.join(indicator.evidence[:5])}

Files in root directory: {len(python_files)}
Sample files: {', '.join([f.name for f in python_files[:10]])}

Please provide:
1. Recommended directory structure
2. Which files should be moved where
3. Specific aider commands to reorganize
4. Any files that should be deleted or consolidated

Focus on creating a clean, maintainable structure that follows Python best practices.
"""

        # Get aider's recommendation (placeholder for now)
        self._query_aider(prompt, "file_organization")

        return AiderRecommendation(
            category="File Organization",
            priority="high",
            title="Reorganize Root Directory Structure",
            description=f"Move {len(python_files)} Python files from root into organized modules",
            specific_actions=[
                "Create src/ directory for main application code",
                "Move related files into logical modules",
                "Update import statements after reorganization",
                "Move experimental files to experiments/ directory",
            ],
            files_affected=[f.name for f in python_files[:5]] + ["..."],
            estimated_time="30-60 minutes",
            aider_commands=[
                "mkdir -p src/",
                "mkdir -p experiments/",
                f"# Move {len(python_files)} files to appropriate directories",
                "# Update imports after moving files",
            ],
        )

    def _generate_code_structure_recommendation(
        self, indicator: ChaosIndicator
    ) -> AiderRecommendation:
        """Generate code structure recommendations."""

        experimental_files = [
            f
            for f in self.project_path.glob("*.py")
            if any(
                keyword in f.stem.lower()
                for keyword in ["demo", "test", "debug", "experimental", "temp"]
            )
        ]

        return AiderRecommendation(
            category="Code Structure",
            priority="high",
            title="Separate Production from Experimental Code",
            description=f"Identify and organize {len(experimental_files)} experimental/demo files",
            specific_actions=[
                "Review each experimental file for production value",
                "Move valuable experiments to experiments/ directory",
                "Delete obsolete demo/debug files",
                "Document which files are production-ready",
            ],
            files_affected=[f.name for f in experimental_files[:5]] + ["..."],
            estimated_time="45-90 minutes",
            aider_commands=[
                "mkdir -p experiments/",
                "# Review and categorize experimental files",
                "# Move or delete as appropriate",
                "# Update documentation",
            ],
        )

    def _generate_documentation_recommendation(
        self, indicator: ChaosIndicator
    ) -> AiderRecommendation:
        """Generate documentation recommendations."""

        return AiderRecommendation(
            category="Documentation",
            priority="medium",
            title="Align Documentation with Reality",
            description="Update README and docs to match actual codebase structure",
            specific_actions=[
                "Review README.md for outdated information",
                "Update file structure documentation",
                "Fix references to non-existent files",
                "Add clear project purpose and scope",
            ],
            files_affected=["README.md"] + indicator.evidence,
            estimated_time="20-30 minutes",
            aider_commands=[
                "# Review and update README.md",
                "# Fix file references",
                "# Add project structure documentation",
            ],
        )

    def _generate_structure_recommendation(
        self, chaos_level: ChaosLevel, indicators: List[ChaosIndicator]
    ) -> AiderRecommendation:
        """Generate overall project structure recommendation."""

        return AiderRecommendation(
            category="Project Structure",
            priority="critical",
            title="Establish Clear Project Architecture",
            description="Create a well-organized project structure with clear separation of concerns",
            specific_actions=[
                "Define clear project purpose and scope",
                "Establish standard directory structure",
                "Separate production, test, and experimental code",
                "Create development guidelines",
                "Set up proper package structure",
            ],
            files_affected=["entire project"],
            estimated_time="2-4 hours",
            aider_commands=[
                "# Create standard Python project structure",
                "mkdir -p src/ tests/ docs/ experiments/",
                "# Reorganize all files into appropriate directories",
                "# Update setup.py/pyproject.toml",
                "# Create __init__.py files for proper packages",
            ],
        )

    def _query_aider(self, prompt: str, context: str) -> str:
        """Query aider for recommendations (simplified for now)."""

        # For now, return a placeholder response
        # In full implementation, this would actually call aider
        return f"Aider recommendation for {context}: {prompt[:100]}..."

    def display_recommendations(self, recommendations: List[AiderRecommendation]):
        """Display recommendations in a user-friendly format."""

        if not recommendations:
            print("✅ No strategic recommendations needed - codebase structure looks good!")
            return

        print(f"\n🎯 Strategic Cleanup Recommendations ({len(recommendations)} items)")
        print("=" * 70)

        # Group by priority
        critical = [r for r in recommendations if r.priority == "critical"]
        high = [r for r in recommendations if r.priority == "high"]
        medium = [r for r in recommendations if r.priority == "medium"]

        for priority_group, title, emoji in [
            (critical, "CRITICAL", "🚨"),
            (high, "HIGH PRIORITY", "⚠️"),
            (medium, "MEDIUM PRIORITY", "💡"),
        ]:
            if priority_group:
                print(f"\n{emoji} {title} ({len(priority_group)} items)")
                print("-" * 50)

                for i, rec in enumerate(priority_group, 1):
                    print(f"\n{i}. {rec.title}")
                    print(f"   Category: {rec.category}")
                    print(f"   Time Estimate: {rec.estimated_time}")
                    print(f"   Description: {rec.description}")

                    if rec.specific_actions:
                        print("   Actions:")
                        for action in rec.specific_actions[:3]:
                            print(f"     • {action}")
                        if len(rec.specific_actions) > 3:
                            print(f"     • ... and {len(rec.specific_actions) - 3} more")

                    if rec.aider_commands:
                        print("   Aider Commands:")
                        for cmd in rec.aider_commands[:2]:
                            print(f"     $ {cmd}")
                        if len(rec.aider_commands) > 2:
                            print(f"     $ ... and {len(rec.aider_commands) - 2} more commands")

        print("\n🔄 Next Steps:")
        print("1. Address CRITICAL items first")
        print("2. Work through HIGH PRIORITY items")
        print("3. Re-run: aider-lint-fixer . --force-strategic-recheck")
        print("4. Once strategic check passes, proceed with lint fixing")

        print("\n💡 Pro Tip:")
        print("Use aider.chat directly to implement these recommendations:")
        print("$ aider --message 'Help me reorganize this project structure'")


def demonstrate_aider_recommendations():
    """Demonstrate the aider-powered recommendations system."""

    print("🤖 Aider-Powered Strategic Recommendations Demo")
    print("=" * 60)

    # Simulate chaos indicators
    indicators = [
        ChaosIndicator(
            type="file_organization",
            severity="major",
            description="Too many Python files in root directory",
            evidence=["demo_test.py", "debug_script.py", "temp_file.py", "..."],
            impact="Makes project structure unclear",
        ),
        ChaosIndicator(
            type="code_structure",
            severity="major",
            description="Too many experimental/demo files",
            evidence=["demo_*.py", "test_*.py", "debug_*.py", "..."],
            impact="Unclear which files are production code",
        ),
    ]

    # Generate recommendations
    engine = AiderStrategicRecommendationEngine(".")
    recommendations = engine.generate_recommendations(ChaosLevel.CHAOTIC, indicators)

    # Display recommendations
    engine.display_recommendations(recommendations)


if __name__ == "__main__":
    demonstrate_aider_recommendations()
