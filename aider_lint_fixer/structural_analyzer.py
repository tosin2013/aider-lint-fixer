#!/usr/bin/env python3
"""
Enhanced Structural Problem Detection

This module implements enhanced detection of patterns that indicate structural code problems
when 100+ lint errors are detected, based on research findings about correlation between
high error counts and architectural issues.

Based on research findings that high lint error densities often suffer from "digital dark matter" -
hidden complexity and structural issues that manifest as surface-level violations but represent
deeper architectural problems. The analysis shows that 100+ lint errors are rarely distributed
randomly but concentrate in areas where architectural decisions have created maintenance bottlenecks.

Key Features:
- Structural problem pattern detection
- Architectural hotspot identification
- Technical debt measurement
- Complexity clustering analysis
- Refactoring recommendation generation
- Maintenance bottleneck detection
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class StructuralProblemType(Enum):
    """Types of structural problems that can be detected."""

    MONOLITHIC_FILES = "monolithic_files"
    TIGHT_COUPLING = "tight_coupling"
    POOR_SEPARATION = "poor_separation"
    COMPLEXITY_HOTSPOTS = "complexity_hotspots"
    DEPENDENCY_CYCLES = "dependency_cycles"
    ARCHITECTURAL_VIOLATIONS = "architectural_violations"
    TECHNICAL_DEBT_CLUSTERS = "technical_debt_clusters"


@dataclass
class StructuralIssue:
    """Represents a detected structural issue."""

    problem_type: StructuralProblemType
    severity: str  # low, medium, high, critical
    description: str
    affected_files: List[str] = field(default_factory=list)
    error_count: int = 0
    confidence: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class FileStructuralMetrics:
    """Structural metrics for a single file."""

    file_path: str
    error_count: int
    error_density: float  # errors per line of code
    error_types: Set[str] = field(default_factory=set)
    complexity_indicators: Dict[str, int] = field(default_factory=dict)
    coupling_score: float = 0.0
    cohesion_score: float = 0.0
    lines_of_code: int = 0


@dataclass
class ArchitecturalAnalysis:
    """Results of architectural analysis."""

    total_files: int
    total_errors: int
    structural_issues: List[StructuralIssue] = field(default_factory=list)
    hotspot_files: List[str] = field(default_factory=list)
    refactoring_candidates: List[str] = field(default_factory=list)
    architectural_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)


class StructuralProblemDetector:
    """Enhanced detector for structural code problems."""

    def __init__(self, project_path: str):
        self.project_path = project_path

        # Thresholds for problem detection
        self.high_error_threshold = 100  # Research threshold for chaotic codebases
        self.error_density_threshold = 0.05  # 5 errors per 100 lines
        self.monolithic_file_threshold = 500  # Lines of code
        self.complexity_threshold = 10  # Cyclomatic complexity

        # Pattern definitions for structural problems
        self.structural_patterns = {
            "undefined_variables": ["no-undef", "undefined-variable"],
            "import_issues": [
                "import/no-unresolved",
                "import/no-extraneous-dependencies",
            ],
            "global_usage": ["no-global-assign", "global-statement"],
            "complexity_indicators": ["max-len", "max-statements", "max-depth"],
            "coupling_indicators": ["import/no-cycle", "circular-import"],
            "cohesion_indicators": ["unused-import", "unused-variable"],
        }

    def analyze_structural_problems(
        self, file_analyses: Dict[str, any]
    ) -> ArchitecturalAnalysis:
        """Perform comprehensive structural problem analysis."""

        total_errors = sum(
            len(analysis.error_analyses) for analysis in file_analyses.values()
        )

        logger.info(
            f"Analyzing structural problems for {len(file_analyses)} files "
            f"with {total_errors} total errors"
        )

        # Calculate file-level metrics
        file_metrics = self._calculate_file_metrics(file_analyses)

        # Detect structural issues
        structural_issues = []

        if total_errors >= self.high_error_threshold:
            # High error count triggers comprehensive structural analysis
            structural_issues.extend(self._detect_monolithic_files(file_metrics))
            structural_issues.extend(
                self._detect_tight_coupling(file_metrics, file_analyses)
            )
            structural_issues.extend(self._detect_complexity_hotspots(file_metrics))
            structural_issues.extend(
                self._detect_architectural_violations(file_metrics, file_analyses)
            )
            structural_issues.extend(self._detect_technical_debt_clusters(file_metrics))

        # Identify hotspot files and refactoring candidates
        hotspot_files = self._identify_hotspot_files(file_metrics)
        refactoring_candidates = self._identify_refactoring_candidates(
            file_metrics, structural_issues
        )

        # Calculate overall architectural score
        architectural_score = self._calculate_architectural_score(
            file_metrics, structural_issues
        )

        # Generate recommendations
        recommendations = self._generate_architectural_recommendations(
            structural_issues, hotspot_files, total_errors
        )

        return ArchitecturalAnalysis(
            total_files=len(file_analyses),
            total_errors=total_errors,
            structural_issues=structural_issues,
            hotspot_files=hotspot_files,
            refactoring_candidates=refactoring_candidates,
            architectural_score=architectural_score,
            recommendations=recommendations,
        )

    def _calculate_file_metrics(
        self, file_analyses: Dict[str, any]
    ) -> List[FileStructuralMetrics]:
        """Calculate structural metrics for each file."""

        file_metrics = []

        for file_path, analysis in file_analyses.items():
            error_count = len(analysis.error_analyses)
            error_types = set(error.error.rule_id for error in analysis.error_analyses)

            # Estimate lines of code (rough approximation)
            lines_of_code = self._estimate_lines_of_code(file_path)
            error_density = error_count / max(lines_of_code, 1)

            # Calculate complexity indicators
            complexity_indicators = self._calculate_complexity_indicators(
                analysis.error_analyses
            )

            # Calculate coupling and cohesion scores
            coupling_score = self._calculate_coupling_score(
                error_types, analysis.error_analyses
            )
            cohesion_score = self._calculate_cohesion_score(
                error_types, analysis.error_analyses
            )

            metrics = FileStructuralMetrics(
                file_path=file_path,
                error_count=error_count,
                error_density=error_density,
                error_types=error_types,
                complexity_indicators=complexity_indicators,
                coupling_score=coupling_score,
                cohesion_score=cohesion_score,
                lines_of_code=lines_of_code,
            )

            file_metrics.append(metrics)

        return file_metrics

    def _detect_monolithic_files(
        self, file_metrics: List[FileStructuralMetrics]
    ) -> List[StructuralIssue]:
        """Detect monolithic files that are too large and complex."""

        issues = []

        for metrics in file_metrics:
            # Check for monolithic characteristics
            is_monolithic = (
                metrics.lines_of_code > self.monolithic_file_threshold
                and metrics.error_density > self.error_density_threshold
                and metrics.error_count > 20
            )

            if is_monolithic:
                severity = "critical" if metrics.error_count > 50 else "high"

                issue = StructuralIssue(
                    problem_type=StructuralProblemType.MONOLITHIC_FILES,
                    severity=severity,
                    description=f"Monolithic file with {metrics.lines_of_code} lines and {metrics.error_count} errors",
                    affected_files=[metrics.file_path],
                    error_count=metrics.error_count,
                    confidence=0.8,
                    recommendations=[
                        "Break down into smaller, focused modules",
                        "Extract reusable functions and classes",
                        "Implement single responsibility principle",
                        "Consider using composition over inheritance",
                    ],
                    metrics={
                        "lines_of_code": metrics.lines_of_code,
                        "error_density": metrics.error_density,
                        "complexity_score": sum(metrics.complexity_indicators.values()),
                    },
                )

                issues.append(issue)

        return issues

    def _detect_tight_coupling(
        self, file_metrics: List[FileStructuralMetrics], file_analyses: Dict[str, any]
    ) -> List[StructuralIssue]:
        """Detect tight coupling between modules."""

        issues = []

        # Analyze import patterns and dependencies
        import_patterns = defaultdict(set)
        global_usage = defaultdict(int)

        for file_path, analysis in file_analyses.items():
            for error_analysis in analysis.error_analyses:
                error_type = error_analysis.error.rule_id

                # Track import-related issues
                if error_type in self.structural_patterns["import_issues"]:
                    import_patterns[file_path].add(error_type)

                # Track global variable usage
                if error_type in self.structural_patterns["global_usage"]:
                    global_usage[file_path] += 1

        # Detect files with excessive coupling
        highly_coupled_files = []
        for metrics in file_metrics:
            if (
                metrics.coupling_score > 0.7
                or len(import_patterns.get(metrics.file_path, set())) > 3
                or global_usage.get(metrics.file_path, 0) > 5
            ):
                highly_coupled_files.append(metrics.file_path)

        if (
            len(highly_coupled_files) > len(file_metrics) * 0.3
        ):  # More than 30% of files
            issue = StructuralIssue(
                problem_type=StructuralProblemType.TIGHT_COUPLING,
                severity="high",
                description=f"Tight coupling detected across {len(highly_coupled_files)} files",
                affected_files=highly_coupled_files,
                error_count=sum(
                    len(import_patterns.get(f, set())) + global_usage.get(f, 0)
                    for f in highly_coupled_files
                ),
                confidence=0.7,
                recommendations=[
                    "Implement dependency injection patterns",
                    "Use interfaces to decouple modules",
                    "Reduce global variable usage",
                    "Apply facade pattern for complex subsystems",
                    "Consider event-driven architecture",
                ],
                metrics={
                    "affected_file_percentage": len(highly_coupled_files)
                    / len(file_metrics),
                    "average_coupling_score": sum(
                        m.coupling_score
                        for m in file_metrics
                        if m.file_path in highly_coupled_files
                    )
                    / len(highly_coupled_files),
                },
            )

            issues.append(issue)

        return issues

    def _detect_complexity_hotspots(
        self, file_metrics: List[FileStructuralMetrics]
    ) -> List[StructuralIssue]:
        """Detect complexity hotspots in the codebase."""

        issues = []

        # Find files with high complexity indicators
        complexity_hotspots = []

        for metrics in file_metrics:
            complexity_score = sum(metrics.complexity_indicators.values())

            if (
                complexity_score > self.complexity_threshold
                or metrics.error_density > self.error_density_threshold * 2
            ):
                complexity_hotspots.append((metrics.file_path, complexity_score))

        if complexity_hotspots:
            # Sort by complexity score
            complexity_hotspots.sort(key=lambda x: x[1], reverse=True)

            severity = "critical" if len(complexity_hotspots) > 5 else "high"

            issue = StructuralIssue(
                problem_type=StructuralProblemType.COMPLEXITY_HOTSPOTS,
                severity=severity,
                description=f"Complexity hotspots detected in {len(complexity_hotspots)} files",
                affected_files=[f[0] for f in complexity_hotspots],
                error_count=sum(
                    m.error_count
                    for m in file_metrics
                    if m.file_path in [f[0] for f in complexity_hotspots]
                ),
                confidence=0.8,
                recommendations=[
                    "Refactor complex functions into smaller units",
                    "Reduce nesting levels and cyclomatic complexity",
                    "Extract common patterns into reusable components",
                    "Apply strategy pattern for complex conditional logic",
                    "Consider state machines for complex state management",
                ],
                metrics={
                    "max_complexity_score": (
                        complexity_hotspots[0][1] if complexity_hotspots else 0
                    ),
                    "average_complexity": sum(score for _, score in complexity_hotspots)
                    / len(complexity_hotspots),
                    "hotspot_count": len(complexity_hotspots),
                },
            )

            issues.append(issue)

        return issues

    def _detect_architectural_violations(
        self, file_metrics: List[FileStructuralMetrics], file_analyses: Dict[str, any]
    ) -> List[StructuralIssue]:
        """Detect architectural violations and anti-patterns."""

        issues = []

        # Analyze undefined variable patterns (often indicates poor module organization)
        undefined_var_files = []
        total_undefined_errors = 0

        for file_path, analysis in file_analyses.items():
            undefined_count = sum(
                1
                for error in analysis.error_analyses
                if error.error.rule_id
                in self.structural_patterns["undefined_variables"]
            )

            if (
                undefined_count > 5
            ):  # Threshold for significant undefined variable issues
                undefined_var_files.append(file_path)
                total_undefined_errors += undefined_count

        if (
            len(undefined_var_files) > len(file_analyses) * 0.2
        ):  # More than 20% of files
            issue = StructuralIssue(
                problem_type=StructuralProblemType.ARCHITECTURAL_VIOLATIONS,
                severity="high",
                description=f"Poor module organization indicated by undefined variables in {len(undefined_var_files)} files",
                affected_files=undefined_var_files,
                error_count=total_undefined_errors,
                confidence=0.7,
                recommendations=[
                    "Establish clear module boundaries and interfaces",
                    "Implement proper import/export patterns",
                    "Use explicit dependency declarations",
                    "Apply layered architecture principles",
                    "Consider using a module bundler or dependency injection",
                ],
                metrics={
                    "undefined_variable_density": total_undefined_errors
                    / sum(len(a.error_analyses) for a in file_analyses.values()),
                    "affected_file_ratio": len(undefined_var_files)
                    / len(file_analyses),
                },
            )

            issues.append(issue)

        return issues

    def _detect_technical_debt_clusters(
        self, file_metrics: List[FileStructuralMetrics]
    ) -> List[StructuralIssue]:
        """Detect clusters of technical debt."""

        issues = []

        # Identify files with high technical debt indicators
        debt_files = []
        total_debt_score = 0

        for metrics in file_metrics:
            # Calculate technical debt score
            debt_score = (
                metrics.error_density * 10  # Error density weight
                + (1 - metrics.cohesion_score) * 5  # Low cohesion penalty
                + metrics.coupling_score * 5  # High coupling penalty
                + sum(metrics.complexity_indicators.values())
                * 0.5  # Complexity penalty
            )

            if debt_score > 5:  # Threshold for significant technical debt
                debt_files.append((metrics.file_path, debt_score))
                total_debt_score += debt_score

        if debt_files:
            # Sort by debt score
            debt_files.sort(key=lambda x: x[1], reverse=True)

            severity = "critical" if total_debt_score > 50 else "high"

            issue = StructuralIssue(
                problem_type=StructuralProblemType.TECHNICAL_DEBT_CLUSTERS,
                severity=severity,
                description=f"Technical debt clusters detected in {len(debt_files)} files",
                affected_files=[f[0] for f in debt_files],
                error_count=sum(
                    m.error_count
                    for m in file_metrics
                    if m.file_path in [f[0] for f in debt_files]
                ),
                confidence=0.8,
                recommendations=[
                    "Prioritize refactoring of highest debt files",
                    "Implement code quality gates in CI/CD",
                    "Establish technical debt tracking and reduction goals",
                    "Apply boy scout rule: leave code better than you found it",
                    "Consider rewriting heavily indebted modules",
                ],
                metrics={
                    "total_debt_score": total_debt_score,
                    "average_debt_score": total_debt_score / len(debt_files),
                    "max_debt_score": debt_files[0][1] if debt_files else 0,
                },
            )

            issues.append(issue)

        return issues

    def _identify_hotspot_files(
        self, file_metrics: List[FileStructuralMetrics]
    ) -> List[str]:
        """Identify files that are architectural hotspots."""

        hotspots = []

        # Sort files by combined score of error count, density, and complexity
        scored_files = []

        for metrics in file_metrics:
            hotspot_score = (
                metrics.error_count * 0.3
                + metrics.error_density * 100 * 0.4
                + sum(metrics.complexity_indicators.values()) * 0.3
            )

            scored_files.append((metrics.file_path, hotspot_score))

        # Sort by score and take top files
        scored_files.sort(key=lambda x: x[1], reverse=True)

        # Take top 20% or files with score > threshold
        threshold = max(5, len(scored_files) * 0.2)
        hotspots = [f[0] for f in scored_files[: int(threshold)] if f[1] > 3]

        return hotspots

    def _identify_refactoring_candidates(
        self,
        file_metrics: List[FileStructuralMetrics],
        structural_issues: List[StructuralIssue],
    ) -> List[str]:
        """Identify files that are good candidates for refactoring."""

        candidates = set()

        # Add files from structural issues
        for issue in structural_issues:
            if issue.severity in ["high", "critical"]:
                candidates.update(issue.affected_files)

        # Add files with high error density but manageable size
        for metrics in file_metrics:
            if (
                metrics.error_density > self.error_density_threshold
                and metrics.lines_of_code < self.monolithic_file_threshold * 2
                and metrics.error_count > 10
            ):
                candidates.add(metrics.file_path)

        return list(candidates)

    def _calculate_architectural_score(
        self,
        file_metrics: List[FileStructuralMetrics],
        structural_issues: List[StructuralIssue],
    ) -> float:
        """Calculate overall architectural health score (0-100)."""

        if not file_metrics:
            return 0.0

        # Base score starts at 100
        score = 100.0

        # Penalty for structural issues
        for issue in structural_issues:
            if issue.severity == "critical":
                score -= 20
            elif issue.severity == "high":
                score -= 10
            elif issue.severity == "medium":
                score -= 5

        # Penalty for high error density
        avg_error_density = sum(m.error_density for m in file_metrics) / len(
            file_metrics
        )
        score -= min(30, avg_error_density * 1000)  # Cap penalty at 30 points

        # Penalty for low cohesion
        avg_cohesion = sum(m.cohesion_score for m in file_metrics) / len(file_metrics)
        score -= (1 - avg_cohesion) * 20

        # Penalty for high coupling
        avg_coupling = sum(m.coupling_score for m in file_metrics) / len(file_metrics)
        score -= avg_coupling * 15

        return max(0.0, min(100.0, score))

    def _generate_architectural_recommendations(
        self,
        structural_issues: List[StructuralIssue],
        hotspot_files: List[str],
        total_errors: int,
    ) -> List[str]:
        """Generate high-level architectural recommendations."""

        recommendations = []

        if total_errors >= self.high_error_threshold:
            recommendations.append(
                f"🏥 CHAOTIC CODEBASE: {total_errors} errors indicate systemic architectural issues"
            )
            recommendations.append(
                "📋 Recommend comprehensive architectural review and refactoring plan"
            )

        # Issue-specific recommendations
        issue_types = set(issue.problem_type for issue in structural_issues)

        if StructuralProblemType.MONOLITHIC_FILES in issue_types:
            recommendations.append(
                "🔨 Break down monolithic files using modular architecture"
            )

        if StructuralProblemType.TIGHT_COUPLING in issue_types:
            recommendations.append(
                "🔗 Implement loose coupling through dependency injection"
            )

        if StructuralProblemType.COMPLEXITY_HOTSPOTS in issue_types:
            recommendations.append(
                "🧩 Refactor complexity hotspots using design patterns"
            )

        if StructuralProblemType.TECHNICAL_DEBT_CLUSTERS in issue_types:
            recommendations.append("💳 Establish technical debt reduction roadmap")

        # Hotspot-specific recommendations
        if len(hotspot_files) > 5:
            recommendations.append(
                f"🎯 Focus refactoring efforts on {len(hotspot_files)} identified hotspot files"
            )

        # General architectural recommendations
        if len(structural_issues) > 3:
            recommendations.append("🏗️ Consider adopting clean architecture principles")
            recommendations.append("📐 Implement automated architecture testing")

        return recommendations

    def _estimate_lines_of_code(self, file_path: str) -> int:
        """Estimate lines of code in a file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            # Fallback estimation based on file size
            try:
                file_size = Path(file_path).stat().st_size
                return max(1, file_size // 50)  # Rough estimate: 50 bytes per line
            except Exception:
                return 100  # Default fallback

    def _calculate_complexity_indicators(self, error_analyses: List) -> Dict[str, int]:
        """Calculate complexity indicators from error analyses."""

        indicators = defaultdict(int)

        for error_analysis in error_analyses:
            error_type = error_analysis.error.rule_id

            if error_type in self.structural_patterns["complexity_indicators"]:
                indicators[error_type] += 1

        return dict(indicators)

    def _calculate_coupling_score(
        self, error_types: Set[str], error_analyses: List
    ) -> float:
        """Calculate coupling score based on error patterns."""

        coupling_indicators = 0
        total_errors = len(error_analyses)

        for error_type in error_types:
            if error_type in self.structural_patterns["coupling_indicators"]:
                coupling_indicators += 1
            elif error_type in self.structural_patterns["import_issues"]:
                coupling_indicators += 1
            elif error_type in self.structural_patterns["global_usage"]:
                coupling_indicators += 1

        return min(1.0, coupling_indicators / max(1, total_errors * 0.1))

    def _calculate_cohesion_score(
        self, error_types: Set[str], error_analyses: List
    ) -> float:
        """Calculate cohesion score based on error patterns."""

        cohesion_issues = 0
        total_errors = len(error_analyses)

        for error_type in error_types:
            if error_type in self.structural_patterns["cohesion_indicators"]:
                cohesion_issues += 1

        # Higher cohesion issues = lower cohesion score
        cohesion_penalty = cohesion_issues / max(1, total_errors * 0.1)

        return max(0.0, 1.0 - cohesion_penalty)
