#!/usr/bin/env python3
"""
Strategic Pre-Flight Check System

Integrates messy codebase analysis into aider-lint-fixer as a mandatory
pre-flight check. Stops execution and provides strategic guidance for
chaotic codebases before attempting automated fixes.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class ChaosLevel(Enum):
    """Levels of codebase chaos."""

    CLEAN = "clean"
    MESSY = "messy"
    CHAOTIC = "chaotic"
    DISASTER = "disaster"


@dataclass
class ChaosIndicator:
    """Indicator of codebase chaos."""

    type: str
    severity: str
    description: str
    evidence: List[str]
    impact: str


@dataclass
class PreFlightResult:
    """Result of pre-flight strategic analysis."""

    chaos_level: str
    should_proceed: bool
    blocking_issues: List[str]
    strategic_questions: List[Dict]
    recommended_actions: List[str]
    analysis_timestamp: str
    bypass_available: bool = False


class MessyCodebaseAnalyzer:
    """Simplified analyzer for codebase chaos detection."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)

    def analyze_chaos_level(self) -> ChaosLevel:
        """Analyze the overall chaos level of the codebase."""
        indicators = self._detect_chaos_indicators()

        chaos_score = 0
        for indicator in indicators:
            if indicator.severity == "critical":
                chaos_score += 3
            elif indicator.severity == "major":
                chaos_score += 2
            elif indicator.severity == "minor":
                chaos_score += 1

        if chaos_score >= 8:
            return ChaosLevel.DISASTER
        elif chaos_score >= 4:
            return ChaosLevel.CHAOTIC
        elif chaos_score >= 2:
            return ChaosLevel.MESSY
        else:
            return ChaosLevel.CLEAN

    def _detect_chaos_indicators(self) -> List[ChaosIndicator]:
        """Detect various indicators of codebase chaos."""
        indicators = []

        # File organization chaos
        root_files = [f for f in self.project_path.iterdir() if f.is_file()]
        python_files_in_root = [f for f in root_files if f.suffix == ".py"]

        if len(python_files_in_root) > 10:
            indicators.append(
                ChaosIndicator(
                    type="file_organization",
                    severity="major",
                    description="Too many Python files in root directory",
                    evidence=[f.name for f in python_files_in_root[:5]] + ["..."],
                    impact="Makes project structure unclear and hard to navigate",
                )
            )

        # Check for experimental/demo files
        experimental_files = []
        for file in self.project_path.glob("*.py"):
            name = file.stem.lower()
            if any(
                keyword in name
                for keyword in ["demo", "test", "debug", "experimental", "temp"]
            ):
                experimental_files.append(file.name)

        if len(experimental_files) > 5:
            indicators.append(
                ChaosIndicator(
                    type="code_structure",
                    severity="major",
                    description="Too many experimental/demo files",
                    evidence=experimental_files[:5] + ["..."],
                    impact="Unclear which files are production code vs experiments",
                )
            )

        # Check README vs reality mismatch
        readme_path = self.project_path / "README.md"
        if readme_path.exists():
            mismatch = self._check_readme_reality_mismatch(readme_path)
            if mismatch:
                indicators.append(mismatch)

        return indicators

    def _check_readme_reality_mismatch(
        self, readme_path: Path
    ) -> Optional[ChaosIndicator]:
        """Check if README describes a different project than what exists."""
        try:
            readme_content = readme_path.read_text().lower()

            # Check if README mentions files that don't exist
            mentioned_files = []
            if "aider_test_fixer_clean.py" in readme_content:
                mentioned_files.append("aider_test_fixer_clean.py")
            if "project_detector.py" in readme_content:
                mentioned_files.append("project_detector.py")

            missing_files = []
            for file in mentioned_files:
                if not (self.project_path / file).exists():
                    missing_files.append(file)

            if missing_files:
                return ChaosIndicator(
                    type="documentation",
                    severity="major",
                    description="README mentions files that don't exist",
                    evidence=missing_files,
                    impact="Documentation doesn't match actual codebase",
                )
        except Exception:
            pass

        return None


class StrategicPreFlightChecker:
    """Pre-flight checker that analyzes codebase strategy before fixing."""

    def __init__(self, project_path: str, config_manager=None):
        self.project_path = Path(project_path)
        self.cache_file = (
            self.project_path / ".aider-lint-cache" / "strategic_analysis.json"
        )
        self.analyzer = MessyCodebaseAnalyzer(str(project_path))
        self.config_manager = config_manager

    def run_preflight_check(self, force_recheck: bool = False) -> PreFlightResult:
        """Run strategic pre-flight check."""

        # Check if we have a recent analysis (unless forced)
        if not force_recheck and self._has_recent_analysis():
            cached_result = self._load_cached_analysis()
            if cached_result and cached_result.should_proceed:
                return cached_result

        # Analyze chaos level
        chaos_level = self.analyzer.analyze_chaos_level()
        indicators = self.analyzer._detect_chaos_indicators()

        # Determine if we should proceed
        should_proceed = self._should_proceed_with_fixes(chaos_level, indicators)

        # Create result
        result = PreFlightResult(
            chaos_level=chaos_level.value,
            should_proceed=should_proceed,
            blocking_issues=self._get_blocking_issues(indicators),
            strategic_questions=[],  # Simplified for now
            recommended_actions=self._get_recommended_actions(chaos_level, indicators),
            analysis_timestamp=datetime.now().isoformat(),
            bypass_available=chaos_level in [ChaosLevel.MESSY, ChaosLevel.CHAOTIC],
        )

        # Cache the result
        self._cache_analysis(result)

        # Display results
        self._display_preflight_results(result)

        # Generate aider-powered recommendations if needed
        if not result.should_proceed:
            self._generate_aider_recommendations(chaos_level, indicators)

        return result

    def run_enhanced_preflight_check(
        self,
        force_recheck: bool = False,
        enable_enhanced_analysis: bool = False,
        quantify_debt: bool = False,
        predict_outcomes: bool = False,
        export_for_llm: str = None,
        chaos_dimensions: str = "basic",
    ) -> PreFlightResult:
        """Run enhanced strategic pre-flight check with research-based features."""

        print("🔬 Running enhanced strategic analysis...")
        print(f"   Enhanced analysis: {enable_enhanced_analysis}")
        print(f"   Technical debt quantification: {quantify_debt}")
        print(f"   Predictive outcomes: {predict_outcomes}")
        print(f"   Export for LLM: {export_for_llm or 'None'}")
        print(f"   Chaos dimensions: {chaos_dimensions}")

        # Run standard analysis first
        result = self.run_preflight_check(force_recheck)

        # Add enhanced analysis if requested
        if any(
            [enable_enhanced_analysis, quantify_debt, predict_outcomes, export_for_llm]
        ):
            try:
                from .enhanced_strategic_analyzer import EnhancedStrategicAnalyzer

                enhanced_analyzer = EnhancedStrategicAnalyzer(
                    str(self.project_path), self.config_manager
                )

                # Mock error analyses for demonstration (in real implementation, this would come from linter results)
                mock_error_analyses = self._create_mock_error_analyses()

                if quantify_debt:
                    print("\n📊 Technical Debt Analysis (SQALE Methodology):")
                    debt_metrics = enhanced_analyzer.analyze_technical_debt_metrics(
                        mock_error_analyses
                    )
                    print(
                        f"   Total Technical Debt: {debt_metrics.total_debt_hours:.1f} hours"
                    )
                    print(f"   SQALE Rating: {debt_metrics.sqale_rating}")
                    print(f"   Debt Ratio: {debt_metrics.debt_ratio:.2%}")

                if predict_outcomes:
                    print("\n🎯 Predictive Analysis:")
                    predictions = enhanced_analyzer.predict_fix_outcomes(
                        mock_error_analyses
                    )
                    print(
                        f"   Fix Success Probability: {predictions.fix_success_probability:.1%}"
                    )
                    print(f"   Confidence Score: {predictions.confidence_score:.1%}")
                    print(
                        f"   Recommended Approach: {predictions.recommended_approach}"
                    )
                    print(
                        f"   Estimated Effort: {predictions.estimated_effort_hours:.1f} hours"
                    )

                if export_for_llm:
                    print(f"\n🤖 Exporting for {export_for_llm.upper()} Analysis:")
                    chaos_level = self.analyzer.analyze_chaos_level()
                    indicators = self.analyzer._detect_chaos_indicators()

                    export_data = enhanced_analyzer.generate_external_llm_export(
                        chaos_level, indicators, mock_error_analyses, export_for_llm
                    )

                    # Save export data
                    export_file = (
                        self.project_path / f"strategic_analysis_{export_for_llm}.json"
                    )
                    import json

                    with open(export_file, "w") as f:
                        json.dump(export_data, f, indent=2, default=str)

                    print(f"   Export saved to: {export_file}")
                    print(
                        f"   Total files analyzed: {export_data['metadata']['total_files_analyzed']}"
                    )
                    print(f"   Total errors: {export_data['metadata']['total_errors']}")

                    # Show recommended prompts
                    if export_data.get("recommended_prompts"):
                        print(f"\n💡 Recommended {export_for_llm.upper()} Prompts:")
                        for i, prompt in enumerate(
                            export_data["recommended_prompts"], 1
                        ):
                            print(f"   {i}. {prompt[:100]}...")

            except ImportError as e:
                print(f"⚠️  Enhanced analysis not available: {e}")
            except Exception as e:
                print(f"⚠️  Enhanced analysis failed: {e}")

        return result

    def _create_mock_error_analyses(self):
        """Create mock error analyses for demonstration purposes."""
        # In real implementation, this would use actual linter results
        from .error_analyzer import ErrorAnalysis, LintError
        from .pattern_matcher import ErrorCategory

        mock_analyses = {}

        # Create some mock errors for demonstration
        mock_error = LintError(
            file_path="src/example.js",
            line=10,
            column=5,
            message="'logCallback' is not defined",
            rule_id="no-unde",
            linter="eslint",
        )

        mock_analysis = ErrorAnalysis(
            error=mock_error,
            category=ErrorCategory.UNDEFINED_VARIABLE,
            confidence=0.9,
            context_lines=[
                "function processData() {",
                "  logCallback('Processing...');",
                "}",
            ],
            suggested_fix="Define logCallback function or import it",
        )

        mock_analyses["src/example.js"] = type(
            "MockFileAnalysis", (), {"error_analyses": [mock_analysis]}
        )()

        return mock_analyses

    def _should_proceed_with_fixes(
        self, chaos_level: ChaosLevel, indicators: List
    ) -> bool:
        """Determine if automated fixing should proceed."""

        # Never proceed for disaster-level chaos without manual intervention
        if chaos_level == ChaosLevel.DISASTER:
            return False

        # For chaotic codebases, check for critical blocking issues
        if chaos_level == ChaosLevel.CHAOTIC:
            critical_indicators = [i for i in indicators if i.severity == "critical"]
            if critical_indicators:
                return False
            # Allow chaotic with only major/minor issues but warn user
            return False  # Block chaotic by default

        # For messy codebases, check for major blocking issues
        if chaos_level == ChaosLevel.MESSY:
            major_indicators = [
                i for i in indicators if i.severity in ["critical", "major"]
            ]
            if len(major_indicators) > 2:  # Too many major issues
                return False
            return True  # Allow messy with few major issues

        # Always proceed for clean codebases
        return True

    def _get_blocking_issues(self, indicators: List) -> List[str]:
        """Get list of issues that block automated fixing."""
        blocking = []

        for indicator in indicators:
            if indicator.severity in ["critical", "major"]:
                blocking.append(f"{indicator.type}: {indicator.description}")

        return blocking

    def _get_recommended_actions(
        self, chaos_level: ChaosLevel, indicators: List
    ) -> List[str]:
        """Get recommended actions before proceeding with fixes."""
        actions = []

        if chaos_level == ChaosLevel.DISASTER:
            actions.extend(
                [
                    "🚨 CRITICAL: Define clear project purpose and scope",
                    "🗂️  Organize files into logical directory structure",
                    "🧹 Remove experimental/demo files or move to separate folder",
                    "📝 Update documentation to match actual codebase",
                ]
            )

        elif chaos_level == ChaosLevel.CHAOTIC:
            actions.extend(
                [
                    "⚠️  Clarify which files are production vs experimental",
                    "📁 Reorganize root directory (too many files)",
                    "📖 Align README with actual project structure",
                ]
            )

        elif chaos_level == ChaosLevel.MESSY:
            actions.extend(
                [
                    "📂 Consider organizing files into modules",
                    "🧪 Move test files to tests/ directory",
                ]
            )

        return actions

    def _display_preflight_results(self, result: PreFlightResult):
        """Display pre-flight analysis results."""

        print(f"📊 Chaos Level: {result.chaos_level.upper()}")
        print(
            f"🚦 Proceed with Fixes: {'✅ YES' if result.should_proceed else '❌ NO'}"
        )

        # Only show blocking issues if they actually block
        if result.blocking_issues and not result.should_proceed:
            print("\n🚫 Blocking Issues:")
            for issue in result.blocking_issues:
                print(f"   • {issue}")
        elif result.blocking_issues and result.should_proceed:
            print("\n⚠️  Issues Detected (proceeding with caution):")
            for issue in result.blocking_issues[:2]:
                print(f"   • {issue}")

        if result.recommended_actions and not result.should_proceed:
            print("\n💡 Recommended Actions:")
            for action in result.recommended_actions[:3]:
                print(f"   {action}")
        elif result.recommended_actions and result.should_proceed:
            print("\n💡 Consider addressing later:")
            for action in result.recommended_actions[:2]:
                print(f"   {action}")

    def _has_recent_analysis(self) -> bool:
        """Check if we have a recent strategic analysis."""
        if not self.cache_file.exists():
            return False

        try:
            with open(self.cache_file, "r") as f:
                data = json.load(f)

            # Check if analysis is less than 24 hours old
            analysis_time = datetime.fromisoformat(data["analysis_timestamp"])
            age_hours = (datetime.now() - analysis_time).total_seconds() / 3600

            return age_hours < 24
        except Exception:
            return False

    def _load_cached_analysis(self) -> Optional[PreFlightResult]:
        """Load cached strategic analysis."""
        try:
            with open(self.cache_file, "r") as f:
                data = json.load(f)
            return PreFlightResult(**data)
        except Exception:
            return None

    def _cache_analysis(self, result: PreFlightResult):
        """Cache strategic analysis results."""
        try:
            # Ensure cache directory exists
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.cache_file, "w") as f:
                json.dump(asdict(result), f, indent=2)
        except Exception:
            pass  # Cache failure shouldn't block execution

    def _generate_aider_recommendations(
        self, chaos_level: ChaosLevel, indicators: List
    ):
        """Generate aider-powered strategic recommendations."""
        try:
            from .aider_strategic_recommendations import (
                AiderStrategicRecommendationEngine,
            )

            engine = AiderStrategicRecommendationEngine(
                str(self.project_path), self.config_manager
            )

            recommendations = engine.generate_recommendations(chaos_level, indicators)
            engine.display_recommendations(recommendations)

        except ImportError:
            print("\n💡 Manual Cleanup Recommendations:")
            print(
                "Since aider recommendations are not available, here are manual steps:"
            )

            for indicator in indicators:
                if indicator.severity in ["critical", "major"]:
                    print(f"\n• {indicator.description}")
                    print(f"  Files: {', '.join(indicator.evidence[:3])}")
                    if indicator.type == "file_organization":
                        print("  → Create src/ directory and move Python files")
                        print("  → Organize related files into modules")
                    elif indicator.type == "code_structure":
                        print("  → Move experimental files to experiments/ directory")
                        print("  → Delete obsolete demo/debug files")
                    elif indicator.type == "documentation":
                        print("  → Update README.md to match actual structure")
                        print("  → Fix references to non-existent files")

        except Exception as e:
            print(f"\n⚠️  Could not generate aider recommendations: {e}")
            print("Please manually address the strategic issues listed above.")
