#!/usr/bin/env python3
"""
Pre-Lint Risk Assessment System
Analyzes project health and provides recommendations before automated linting.
Similar to preflight check but focused on lint-specific risks.
"""
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .lint_runner import LintRunner
from .project_detector import ProjectDetector

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for automated linting."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(Enum):
    """Categories of linting risks."""

    VOLUME = "volume"  # Too many errors
    UNDEFINED_VARS = "undefined_vars"  # Runtime-breaking errors
    MISSING_TESTS = "missing_tests"  # No safety net
    LEGACY_CODE = "legacy_code"  # Old patterns that might be intentional
    EXTERNAL_DEPS = "external_deps"  # Global variables, external scripts
    PRODUCTION_CODE = "production_code"  # Live/critical system


@dataclass
class RiskAssessment:
    """Assessment of linting risks for a project."""

    overall_risk: RiskLevel
    total_errors: int
    error_breakdown: Dict[str, int]
    risk_factors: List[Tuple[RiskCategory, str, RiskLevel]]
    recommendations: List[str]
    safe_to_proceed: bool
    suggested_approach: str
    architect_guidance: Optional[Dict] = None


class PreLintAssessor:
    """Assesses project risks before automated linting."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.project_detector = ProjectDetector()
        # Initialize with basic project info for lint runner
        project_info = self.project_detector.detect_project(str(self.project_root))
        self.lint_runner = LintRunner(project_info)

    def assess_project(self, linters: Optional[List[str]] = None) -> RiskAssessment:
        """Perform comprehensive pre-lint risk assessment."""
        logger.info("🔍 Performing pre-lint risk assessment...")
        # Detect project info
        project_info = self.project_detector.detect_project(str(self.project_root))
        # Run quick lint scan
        lint_results = self._run_quick_lint_scan(linters)
        # Analyze risks
        risk_factors = []
        recommendations = []
        # Volume risk assessment
        total_errors = sum(len(result.errors) for result in lint_results.values())
        volume_risk = self._assess_volume_risk(
            total_errors, risk_factors, recommendations
        )
        # Error type risk assessment
        error_breakdown = self._analyze_error_types(
            lint_results, risk_factors, recommendations
        )
        # Project context risk assessment
        self._assess_project_context(project_info, risk_factors, recommendations)
        # Test coverage assessment
        self._assess_test_coverage(project_info, risk_factors, recommendations)
        # Determine overall risk
        overall_risk = self._calculate_overall_risk(risk_factors)
        # Generate approach recommendation
        suggested_approach = self._suggest_approach(
            overall_risk, total_errors, error_breakdown
        )
        # Generate architect mode guidance for dangerous errors
        architect_guidance = generate_architect_guidance_for_dangerous_errors(
            lint_results
        )
        return RiskAssessment(
            overall_risk=overall_risk,
            total_errors=total_errors,
            error_breakdown=error_breakdown,
            risk_factors=risk_factors,
            recommendations=recommendations,
            safe_to_proceed=overall_risk in [RiskLevel.LOW, RiskLevel.MEDIUM],
            suggested_approach=suggested_approach,
            architect_guidance=architect_guidance,
        )

    def _run_quick_lint_scan(self, linters: Optional[List[str]]) -> Dict:
        """Run a quick lint scan to get error counts."""
        try:
            # Use only fast linters for assessment
            quick_linters = linters or ["eslint", "flake8"]  # Fast, common linters
            logger.info(f"🔍 Quick scan starting for linters: {quick_linters}")
            logger.info(f"📁 Project root: {self.project_root}")
            results = {}
            for linter in quick_linters:
                try:
                    logger.info(f"🔧 Running quick scan for {linter}...")
                    # Run linter without specific file paths - let it use project's native scope
                    result = self.lint_runner.run_linter(linter)
                    if result:
                        results[linter] = result
                        logger.info(
                            f"✅ Quick scan for {linter}: {len(result.errors)} errors, {len(result.warnings)} warnings"
                        )
                    else:
                        logger.warning(
                            f"❌ Quick scan for {linter}: No result returned"
                        )
                except Exception as e:
                    logger.warning(f"❌ Quick scan failed for {linter}: {e}")
                    import traceback

                    logger.debug(f"Quick scan traceback: {traceback.format_exc()}")
                    continue
            logger.info(f"📊 Quick scan complete: {len(results)} linters succeeded")
            return results
        except Exception as e:
            logger.error(f"Quick lint scan failed: {e}")
            import traceback

            logger.debug(f"Quick scan traceback: {traceback.format_exc()}")
            return {}

    def _assess_volume_risk(
        self, total_errors: int, risk_factors: List, recommendations: List
    ) -> RiskLevel:
        """Assess risk based on error volume."""
        if total_errors > 1000:
            risk_factors.append(
                (
                    RiskCategory.VOLUME,
                    f"Extremely high error count: {total_errors} errors",
                    RiskLevel.CRITICAL,
                )
            )
            recommendations.append(
                "Consider fixing errors in smaller batches or specific directories"
            )
            return RiskLevel.CRITICAL
        elif total_errors > 100:
            risk_factors.append(
                (
                    RiskCategory.VOLUME,
                    f"High error count: {total_errors} errors",
                    RiskLevel.HIGH,
                )
            )
            recommendations.append("Use --max-errors flag to limit fixes per session")
            return RiskLevel.HIGH
        elif total_errors > 20:
            risk_factors.append(
                (
                    RiskCategory.VOLUME,
                    f"Moderate error count: {total_errors} errors",
                    RiskLevel.MEDIUM,
                )
            )
            recommendations.append("Consider reviewing errors before automated fixing")
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _analyze_error_types(
        self, lint_results: Dict, risk_factors: List, recommendations: List
    ) -> Dict[str, int]:
        """Analyze types of errors and assess risks."""
        error_breakdown = {}
        # Dangerous error patterns
        dangerous_patterns = {
            "no-unde": "undefined variables (could break runtime)",
            "no-global-assign": "global variable assignment",
            "no-implicit-globals": "implicit global variables",
            "import/no-unresolved": "unresolved imports",
            "undefined-variable": "undefined variables",
        }
        for linter, result in lint_results.items():
            for error in result.errors:
                rule_id = error.rule_id or "unknown"
                error_breakdown[rule_id] = error_breakdown.get(rule_id, 0) + 1
                # Check for dangerous patterns
                if rule_id in dangerous_patterns:
                    risk_factors.append(
                        (
                            RiskCategory.UNDEFINED_VARS,
                            f"Found {error_breakdown[rule_id]} '{rule_id}' errors: {dangerous_patterns[rule_id]}",
                            RiskLevel.HIGH,
                        )
                    )
                    recommendations.append(
                        f"Manually review '{rule_id}' errors before automated fixing"
                    )
        return error_breakdown

    def _assess_project_context(
        self, project_info, risk_factors: List, recommendations: List
    ):
        """Assess risks based on project context."""
        # Check for web application indicators
        web_indicators = ["html", "css", "js", "react", "vue", "angular"]
        if any(
            indicator in str(project_info.languages).lower()
            for indicator in web_indicators
        ):
            risk_factors.append(
                (
                    RiskCategory.EXTERNAL_DEPS,
                    "Web application detected - may have global variables from HTML/external scripts",
                    RiskLevel.MEDIUM,
                )
            )
            recommendations.append(
                "Verify that 'undefined' variables aren't from HTML globals"
            )
        # Check for production indicators
        prod_indicators = [
            "dockerfile",
            "docker-compose",
            ".github/workflows",
            "makefile",
        ]
        if any(
            (self.project_root / indicator).exists() for indicator in prod_indicators
        ):
            risk_factors.append(
                (
                    RiskCategory.PRODUCTION_CODE,
                    "Production deployment files detected",
                    RiskLevel.MEDIUM,
                )
            )
            recommendations.append(
                "Test thoroughly after fixes - this appears to be production code"
            )

    def _assess_test_coverage(
        self, project_info, risk_factors: List, recommendations: List
    ):
        """Assess test coverage as a safety net."""
        test_indicators = [
            "test",
            "tests",
            "__tests__",
            "spec",
            "specs",
            "test.js",
            "test.py",
            "test.ts",
            ".test.",
            ".spec.",
        ]
        has_tests = False
        for indicator in test_indicators:
            if list(self.project_root.rglob(f"*{indicator}*")):
                has_tests = True
                break
        if not has_tests:
            risk_factors.append(
                (
                    RiskCategory.MISSING_TESTS,
                    "No test files detected - no safety net for automated fixes",
                    RiskLevel.HIGH,
                )
            )
            recommendations.append("Consider adding tests before automated linting")
            recommendations.append("Use --check-only mode to preview changes first")

    def _calculate_overall_risk(self, risk_factors: List) -> RiskLevel:
        """Calculate overall risk level."""
        if not risk_factors:
            return RiskLevel.LOW
        risk_levels = [factor[2] for factor in risk_factors]
        if RiskLevel.CRITICAL in risk_levels:
            return RiskLevel.CRITICAL
        elif RiskLevel.HIGH in risk_levels:
            return RiskLevel.HIGH
        elif RiskLevel.MEDIUM in risk_levels:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _suggest_approach(
        self, overall_risk: RiskLevel, total_errors: int, error_breakdown: Dict
    ) -> str:
        """Suggest the best approach based on risk assessment."""
        if overall_risk == RiskLevel.CRITICAL:
            return "❌ NOT RECOMMENDED: Use --check-only mode and fix manually in small batches"
        elif overall_risk == RiskLevel.HIGH:
            return "⚠️  CAUTION: Use --max-errors 5 and review each fix carefully"
        elif overall_risk == RiskLevel.MEDIUM:
            return "🔍 CAREFUL: Use --max-errors 10 and test after each session"
        else:
            return "✅ SAFE: Proceed with normal automated fixing"


def display_risk_assessment(assessment: RiskAssessment) -> bool:
    """Display risk assessment and get user confirmation."""
    print("\n" + "=" * 70)
    print("🔍 PRE-LINT RISK ASSESSMENT")
    print("=" * 70)
    # Overall status
    risk_colors = {
        RiskLevel.LOW: "🟢",
        RiskLevel.MEDIUM: "🟡",
        RiskLevel.HIGH: "🟠",
        RiskLevel.CRITICAL: "🔴",
    }
    print(
        f"\n📊 Overall Risk Level: {risk_colors[assessment.overall_risk]} {assessment.overall_risk.value.upper()}"
    )
    print(f"📈 Total Errors Found: {assessment.total_errors}")
    # Risk factors
    if assessment.risk_factors:
        print("\n⚠️  Risk Factors Identified:")
        for category, description, level in assessment.risk_factors:
            print(f"   {risk_colors[level]} {description}")
    # Error breakdown
    if assessment.error_breakdown:
        print("\n📋 Error Breakdown (Top 5):")
        sorted_errors = sorted(
            assessment.error_breakdown.items(), key=lambda x: x[1], reverse=True
        )
        for rule_id, count in sorted_errors[:5]:
            print(f"   • {rule_id}: {count} errors")
    # Recommendations
    if assessment.recommendations:
        print("\n💡 Recommendations:")
        for i, rec in enumerate(assessment.recommendations, 1):
            print(f"   {i}. {rec}")
    # Suggested approach
    print("\n🎯 Suggested Approach:")
    print(f"   {assessment.suggested_approach}")
    # Show architect guidance if available
    if assessment.architect_guidance and assessment.architect_guidance.get(
        "has_dangerous_errors"
    ):
        display_architect_guidance(assessment.architect_guidance)
    print("\n" + "=" * 70)
    # Get user decision
    if not assessment.safe_to_proceed:
        print("⚠️  Based on this assessment, automated linting is NOT recommended.")
        response = input("Do you want to proceed anyway? [y/N]: ").strip().lower()
        return response in ["y", "yes"]
    else:
        print("✅ Assessment indicates automated linting is relatively safe.")
        response = input("Proceed with automated linting? [Y/n]: ").strip().lower()
        return response not in ["n", "no"]


def generate_architect_guidance_for_dangerous_errors(lint_results: Dict) -> Dict:
    """Generate architect mode guidance for dangerous error types like no-undef."""
    guidance = {
        "has_dangerous_errors": False,
        "architect_mode_recommended": False,
        "dangerous_files": {},
        "safe_automation_plan": {},
        "architect_prompts": [],
    }
    if not lint_results:
        return guidance
    # Define dangerous vs safe error types
    dangerous_rules = [
        "no-unde",
        "no-global-assign",
        "no-implicit-globals",
        "no-redeclare",
    ]
    safe_rules = [
        "max-len",
        "no-unused-vars",
        "no-useless-escape",
        "no-fallthrough",
        "prefer-const",
        "no-console",
        "eqeqeq",
        "no-trailing-spaces",
    ]
    dangerous_files = {}
    safe_errors_count = 0
    # Analyze each error
    for linter_name, result in lint_results.items():
        for error in result.errors:
            if error.rule_id in dangerous_rules:
                guidance["has_dangerous_errors"] = True
                if error.file_path not in dangerous_files:
                    dangerous_files[error.file_path] = {
                        "errors": [],
                        "undefined_vars": set(),
                        "error_count": 0,
                    }
                dangerous_files[error.file_path]["errors"].append(
                    {
                        "line": error.line,
                        "rule": error.rule_id,
                        "message": error.message,
                        "variable": _extract_variable_name(
                            error.message, error.rule_id
                        ),
                    }
                )
                dangerous_files[error.file_path]["error_count"] += 1
                # Track undefined variables specifically
                if error.rule_id == "no-unde":
                    var_name = _extract_variable_name(error.message, error.rule_id)
                    if var_name:
                        dangerous_files[error.file_path]["undefined_vars"].add(var_name)
            elif error.rule_id in safe_rules:
                safe_errors_count += 1
    guidance["dangerous_files"] = dangerous_files
    # Generate recommendations if dangerous errors found
    if guidance["has_dangerous_errors"]:
        guidance["architect_mode_recommended"] = True
        guidance["architect_prompts"] = _create_architect_prompts(dangerous_files)
        guidance["safe_automation_plan"] = {
            "safe_errors_count": safe_errors_count,
            "recommended_approach": "Fix safe errors automatically, then use architect mode for dangerous ones",
            "safe_rules": safe_rules,
            "automation_command": f"--max-errors {min(10, safe_errors_count)} --exclude-rules no-undef,no-global-assign",
        }
    return guidance


def _extract_variable_name(message: str, rule_id: str) -> str:
    """Extract variable name from ESLint error message."""
    if rule_id == "no-unde":
        # "'variableName' is not defined"
        import re

        match = re.search(r"'([^']+)' is not defined", message)
        return match.group(1) if match else ""
    return ""


def _create_architect_prompts(dangerous_files: Dict) -> List[Dict]:
    """Create architect mode prompts for each file with dangerous errors."""
    prompts = []
    for file_path, file_info in dangerous_files.items():
        undefined_vars = list(file_info["undefined_vars"])
        if undefined_vars:
            prompt = {
                "file": file_path,
                "error_count": file_info["error_count"],
                "undefined_variables": undefined_vars,
                "architect_prompt": _generate_file_specific_prompt(
                    file_path, undefined_vars, file_info["errors"]
                ),
                "suggested_solutions": _suggest_solutions_for_file(
                    file_path, undefined_vars
                ),
            }
            prompts.append(prompt)
    return prompts


def _generate_file_specific_prompt(
    file_path: str, undefined_vars: List[str], errors: List[Dict]
) -> str:
    """Generate a specific architect prompt for a file."""
    file_name = file_path.split("/")[-1]
    prompt = """# Architect Mode: Fix undefined variables in {file_name}
## Context
File: {file_path}
Undefined variables detected: {', '.join(undefined_vars)}
## Task
Please analyze this file and fix the undefined variable issues. These variables might be:
1. **Missing imports** - Need to add proper import statements
2. **Global variables** - Should be declared or imported from HTML/config
3. **Typos** - Variable name misspellings
4. **Scope issues** - Variables declared in wrong scope
## Specific Issues:
"""
    for error in errors:
        if error["variable"]:
            prompt += (
                f"\n- Line {error['line']}: `{error['variable']}` - {error['message']}"
            )
    prompt += """
## Instructions
1. Examine each undefined variable in context
2. Determine the correct solution for each:
   - Add missing imports if it's an external dependency
   - Declare global variables if they come from HTML/external scripts
   - Fix typos if it's a misspelled variable name
   - Move declarations if it's a scope issue
3. Apply the fixes while preserving functionality
4. Ensure no runtime errors are introduced
Please analyze and fix these undefined variable issues."""
    return prompt


def _suggest_solutions_for_file(file_path: str, undefined_vars: List[str]) -> List[str]:
    """Suggest specific solutions based on file type and variable names."""
    suggestions = []
    file_name = file_path.split("/")[-1].lower()
    # Common patterns based on variable names and file types
    for var in undefined_vars:
        if var.lower() in ["console", "window", "document", "global", "process"]:
            suggestions.append(
                f"'{var}' appears to be a browser/Node.js global - consider adding to eslint globals"
            )
        elif var.lower().endswith("callback") or "callback" in var.lower():
            suggestions.append(
                f"'{var}' might be a callback parameter - check function signatures"
            )
        elif file_name.endswith(".mjs") or "module" in file_name:
            suggestions.append(
                f"'{var}' might need an import statement in this ES module"
            )
        elif "config" in file_name or "settings" in file_name:
            suggestions.append(
                f"'{var}' might be a configuration variable - check config files"
            )
        else:
            suggestions.append(
                f"'{var}' needs investigation - could be import, global, or typo"
            )
    return suggestions


def display_architect_guidance(guidance: Dict):
    """Display architect mode guidance to the user."""
    if not guidance.get("has_dangerous_errors"):
        return
    print("\n🏗️  ARCHITECT MODE RECOMMENDED")
    print("=" * 50)
    print("Dangerous errors detected that require manual review:")
    for file_path, file_info in guidance["dangerous_files"].items():
        file_name = file_path.split("/")[-1]
        undefined_vars = list(file_info["undefined_vars"])
        print(f"\n📁 {file_name}")
        print(f"   Path: {file_path}")
        print(f"   Undefined variables: {', '.join(undefined_vars)}")
        print(f"   Total errors: {file_info['error_count']}")
    # Show safe automation plan
    safe_plan = guidance.get("safe_automation_plan", {})
    if safe_plan:
        print("\n✅ SAFE AUTOMATION PLAN:")
        print(
            f"   • {safe_plan['safe_errors_count']} safe errors can be fixed automatically"
        )
        print(
            f"   • Recommended command: aider-lint-fixer {safe_plan['automation_command']}"
        )
        print(f"   • Safe rules: {', '.join(safe_plan['safe_rules'][:5])}...")
    print("\n💡 WORKFLOW RECOMMENDATION:")
    print(
        f"   1. Run safe automation first: Fix {safe_plan.get('safe_errors_count', 0)} safe errors"
    )
    print(
        f"   2. Use architect mode for dangerous errors in {len(guidance['dangerous_files'])} files"
    )
    print("   3. Review each undefined variable manually")
    # Offer to generate CoT prompt for external AI review
    print("\n🧠 CHAIN OF THOUGHT ANALYSIS:")
    print(
        "   Would you like to generate a Chain of Thought prompt for external AI review?"
    )
    response = input("   Generate CoT prompt? [y/N]: ").strip().lower()
    if response in ["y", "yes"]:
        cot_prompt = generate_cot_prompt_for_dangerous_errors(guidance)
        save_cot_prompt(cot_prompt, guidance)
    return guidance


def generate_cot_prompt_for_dangerous_errors(guidance: Dict) -> str:
    """Generate a Chain of Thought prompt for external AI analysis of dangerous errors.
    Args:
        guidance: Architect guidance containing dangerous error information
    Returns:
        Formatted CoT prompt string for external AI review
    """
    dangerous_files = guidance.get("dangerous_files", {})
    safe_plan = guidance.get("safe_automation_plan", {})
    cot_prompt = """# Chain of Thought Analysis: Dangerous Lint Error Review
## Context
I have a codebase with lint errors that have been categorized into "safe" and "dangerous" types. The dangerous errors require careful human review before automated fixing. Please analyze these dangerous errors and provide recommendations.
## Task
Analyze the undefined variables and dangerous errors below using Chain of Thought reasoning. For each error, think through:
1. **Context Analysis**: What might this variable represent?
2. **Risk Assessment**: What could go wrong if fixed incorrectly?
3. **Solution Options**: What are the possible ways to fix this?
4. **Recommendation**: What's the safest approach?
## Dangerous Errors Found
### Summary
- **Total dangerous files**: {len(dangerous_files)}
- **Safe errors available for automation**: {safe_plan.get('safe_errors_count', 0)}
- **Dangerous errors requiring review**: {sum(len(file_info.get('undefined_vars', set())) for file_info in dangerous_files.values())}
### File-by-File Analysis Needed
"""
    for file_path, file_info in dangerous_files.items():
        file_name = file_path.split("/")[-1]
        undefined_vars = list(file_info.get("undefined_vars", set()))
        errors = file_info.get("errors", [])
        cot_prompt += """#### File: {file_name}
**Path**: `{file_path}`
**Undefined Variables**: {', '.join(f'`{var}`' for var in undefined_vars)}
**Total Errors**: {file_info.get('error_count', 0)}
**Chain of Thought Analysis Needed**:
"""
        for var in undefined_vars:
            cot_prompt += """
**Variable: `{var}`**
- **Step 1 - Context Analysis**:
  - What type of variable might `{var}` be? (global, import, parameter, typo)
  - Based on the file name `{file_name}`, what's the likely purpose?
  - Are there naming patterns that suggest its origin?
- **Step 2 - Risk Assessment**:
  - What happens if we create a dummy variable?
  - What happens if we add it as a global?
  - What happens if we add an import?
  - What's the worst-case scenario for each approach?
- **Step 3 - Solution Options**:
  - Option A: Add as global variable declaration
  - Option B: Add as import statement
  - Option C: Add as function parameter
  - Option D: Fix as typo/rename
  - Option E: Leave as-is with comment
- **Step 4 - Recommendation**:
  - Which option is safest and why?
  - What additional investigation is needed?
  - Should this be fixed automatically or manually?
"""
        cot_prompt += "\n---\n"
    cot_prompt += """
## Safe Automation Context
The following error types have been identified as safe for automation:
{', '.join(safe_plan.get('safe_rules', [])[:10])}
**Safe errors count**: {safe_plan.get('safe_errors_count', 0)}
## Questions for Analysis
1. **Priority Assessment**: Which dangerous errors should be fixed first?
2. **Automation Potential**: Are any of these dangerous errors actually safe to automate?
3. **Risk Mitigation**: What safeguards should be in place?
4. **Testing Strategy**: What tests should be run after fixes?
5. **Rollback Plan**: How can changes be safely reverted if needed?
## Expected Output Format
For each undefined variable, please provide:
```
Variable: `variableName`
Analysis: [Your chain of thought reasoning]
Risk Level: [Low/Medium/High]
Recommended Action: [Specific action to take]
Rationale: [Why this is the safest approach]
```
## Additional Context
- This is a production codebase that needs to maintain functionality
- Automated fixes should be conservative and safe
- Manual review is preferred for ambiguous cases
- The goal is to fix errors without breaking existing functionality
Please analyze each dangerous error using the Chain of Thought approach and provide specific, actionable recommendations.
"""
    return cot_prompt


def save_cot_prompt(cot_prompt: str, guidance: Dict) -> None:
    """Save the CoT prompt to a file for external AI review.
    Args:
        cot_prompt: The generated CoT prompt
        guidance: Architect guidance for context
    """
    import os
    import tempfile
    from datetime import datetime

    try:
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cot_dangerous_errors_analysis_{timestamp}.md"
        # Save to current directory or temp directory
        try:
            filepath = os.path.join(os.getcwd(), filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(cot_prompt)
            print(f"\n✅ CoT prompt saved to: {filepath}")
        except PermissionError:
            # Fallback to temp directory
            temp_dir = tempfile.gettempdir()
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(cot_prompt)
            print(f"\n✅ CoT prompt saved to: {filepath}")
        print("📋 You can now:")
        print("   1. Copy this prompt to ChatGPT, Claude, or another AI")
        print("   2. Get detailed Chain of Thought analysis")
        print("   3. Use the recommendations to safely fix dangerous errors")
        print("   4. Return to aider-lint-fixer with confidence")
        # Show file stats
        dangerous_files = guidance.get("dangerous_files", {})
        total_vars = sum(
            len(file_info.get("undefined_vars", set()))
            for file_info in dangerous_files.values()
        )
        print("\n📊 CoT Prompt Stats:")
        print(f"   Files to analyze: {len(dangerous_files)}")
        print(f"   Undefined variables: {total_vars}")
        print(f"   Prompt length: {len(cot_prompt):,} characters")
    except Exception as e:
        print(f"\n❌ Failed to save CoT prompt: {e}")
        print("📋 CoT prompt content (copy manually):")
        print("=" * 50)
        print(cot_prompt[:1000] + "..." if len(cot_prompt) > 1000 else cot_prompt)
        print("=" * 50)
