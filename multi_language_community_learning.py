#!/usr/bin/env python3
"""
Multi-Language Community Learning System

Demonstrates how the community learning system would work across all
supported languages and linters in aider-lint-fixer.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class SupportedLanguage(Enum):
    """All languages supported by aider-lint-fixer."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    ANSIBLE = "ansible"
    GO = "go"
    RUST = "rust"
    # Future languages can be added here


@dataclass
class LanguageEcosystem:
    """Configuration for each language ecosystem."""

    language: SupportedLanguage
    linters: List[str]
    common_unfixable_patterns: List[str]
    github_repo_examples: List[str]
    community_size: str


# Language ecosystem configurations
LANGUAGE_ECOSYSTEMS = {
    SupportedLanguage.PYTHON: LanguageEcosystem(
        language=SupportedLanguage.PYTHON,
        linters=["flake8", "pylint", "black", "isort", "mypy"],
        common_unfixable_patterns=[
            "undefined-variable",
            "import-error",
            "missing-docstring",
            "too-many-arguments",
            "line-too-long",
        ],
        github_repo_examples=["django/django", "pallets/flask", "psf/requests"],
        community_size="Very Large",
    ),
    SupportedLanguage.JAVASCRIPT: LanguageEcosystem(
        language=SupportedLanguage.JAVASCRIPT,
        linters=["eslint", "jshint", "prettier"],
        common_unfixable_patterns=[
            "no-unused-vars",
            "no-undef",
            "prefer-const",
            "missing-semicolon",
            "indent",
        ],
        github_repo_examples=["facebook/react", "microsoft/vscode", "nodejs/node"],
        community_size="Very Large",
    ),
    SupportedLanguage.TYPESCRIPT: LanguageEcosystem(
        language=SupportedLanguage.TYPESCRIPT,
        linters=["eslint", "@typescript-eslint", "prettier"],
        common_unfixable_patterns=[
            "@typescript-eslint/no-unused-vars",
            "@typescript-eslint/no-explicit-any",
            "@typescript-eslint/explicit-function-return-type",
            "prefer-const",
            "missing-semicolon",
        ],
        github_repo_examples=["microsoft/TypeScript", "angular/angular", "nestjs/nest"],
        community_size="Large",
    ),
    SupportedLanguage.ANSIBLE: LanguageEcosystem(
        language=SupportedLanguage.ANSIBLE,
        linters=["ansible-lint"],
        common_unfixable_patterns=[
            "yaml[trailing-spaces]",
            "yaml[document-start]",
            "yaml[key-duplicates]",
            "name[missing]",
            "args[module]",
        ],
        github_repo_examples=[
            "ansible/ansible",
            "ansible-collections/community.general",
            "geerlingguy/ansible-role-*",
        ],
        community_size="Large",
    ),
    SupportedLanguage.GO: LanguageEcosystem(
        language=SupportedLanguage.GO,
        linters=["golint", "gofmt", "go vet", "staticcheck"],
        common_unfixable_patterns=[
            "exported function should have comment",
            "should not use dot imports",
            "error should be the last type",
            "if block ends with a return statement",
        ],
        github_repo_examples=["golang/go", "kubernetes/kubernetes", "docker/docker"],
        community_size="Large",
    ),
    SupportedLanguage.RUST: LanguageEcosystem(
        language=SupportedLanguage.RUST,
        linters=["clippy", "rustfmt"],
        common_unfixable_patterns=[
            "unused variable",
            "unnecessary parentheses",
            "redundant clone",
            "missing documentation",
        ],
        github_repo_examples=["rust-lang/rust", "tokio-rs/tokio", "serde-rs/serde"],
        community_size="Medium",
    ),
}


def generate_language_specific_examples():
    """Generate examples of how community learning would work for each language."""

    examples = {}

    for lang, ecosystem in LANGUAGE_ECOSYSTEMS.items():
        examples[lang.value] = {
            "real_world_scenarios": _generate_scenarios(ecosystem),
            "github_issue_templates": _generate_github_templates(ecosystem),
            "learning_patterns": _generate_learning_patterns(ecosystem),
        }

    return examples


def _generate_scenarios(ecosystem: LanguageEcosystem) -> List[Dict[str, Any]]:
    """Generate real-world scenarios for each language."""

    scenarios = []

    if ecosystem.language == SupportedLanguage.PYTHON:
        scenarios = [
            {
                "error": "flake8 E501: line too long (88 > 79 characters)",
                "user_fix": "Split long line into multiple lines with proper indentation",
                "success_rate": "95%",
                "fix_time": "30 seconds",
                "community_impact": "High - very common error",
            },
            {
                "error": "pylint C0111: Missing module docstring",
                "user_fix": "Added descriptive module docstring",
                "success_rate": "90%",
                "fix_time": "2 minutes",
                "community_impact": "Medium - documentation improvement",
            },
        ]

    elif ecosystem.language == SupportedLanguage.JAVASCRIPT:
        scenarios = [
            {
                "error": "eslint no-unused-vars: 'React' is defined but never used",
                "user_fix": "Removed unused import or added React usage",
                "success_rate": "85%",
                "fix_time": "15 seconds",
                "community_impact": "High - very common in React projects",
            },
            {
                "error": "eslint prefer-const: 'data' is never reassigned",
                "user_fix": "Changed 'let' to 'const' for immutable variables",
                "success_rate": "98%",
                "fix_time": "5 seconds",
                "community_impact": "High - simple and safe fix",
            },
        ]

    elif ecosystem.language == SupportedLanguage.ANSIBLE:
        scenarios = [
            {
                "error": "ansible-lint yaml[trailing-spaces]: Trailing spaces",
                "user_fix": "Removed trailing whitespace from YAML files",
                "success_rate": "100%",
                "fix_time": "10 seconds",
                "community_impact": "High - formatting issue, very safe",
            },
            {
                "error": "ansible-lint name[missing]: All tasks should be named",
                "user_fix": "Added descriptive name to Ansible task",
                "success_rate": "92%",
                "fix_time": "1 minute",
                "community_impact": "Medium - improves readability",
            },
        ]

    # Add more scenarios for other languages...

    return scenarios


def _generate_github_templates(ecosystem: LanguageEcosystem) -> Dict[str, str]:
    """Generate GitHub issue templates for each language."""

    if ecosystem.language == SupportedLanguage.PYTHON:
        return {
            "title": "Enhancement: Improve Python {linter} {rule_id} classification",
            "body": """## 🐍 Python Enhancement Request

### **Error Pattern**
- **Linter**: {linter}
- **Rule**: {rule_id}
- **Message**: `{message}`

### **Community Evidence**
- **Success Rate**: {success_rate}% from {sample_count} manual fixes
- **Average Fix Time**: {avg_time} seconds
- **User Confidence**: {confidence}/10

### **Common in Python Ecosystem**
This pattern appears frequently in:
- Django projects
- Flask applications
- Data science notebooks
- CLI tools

### **Suggested Classification Update**
```python
# Add to Python pattern matcher
if error.linter == "{linter}" and "{rule_id}" in error.rule_id:
    return FixComplexity.TRIVIAL  # Safe auto-fix
```

### **Impact**
Improving this classification would benefit the large Python community using aider-lint-fixer.
""",
        }

    elif ecosystem.language == SupportedLanguage.JAVASCRIPT:
        return {
            "title": "Enhancement: Improve JavaScript/TypeScript {linter} {rule_id} classification",
            "body": """## ⚡ JavaScript/TypeScript Enhancement Request

### **Error Pattern**
- **Linter**: {linter}
- **Rule**: {rule_id}
- **Message**: `{message}`

### **Community Evidence**
- **Success Rate**: {success_rate}% from {sample_count} manual fixes
- **Frontend/Backend**: Both environments affected
- **Framework Impact**: React, Vue, Angular, Node.js

### **Common Scenarios**
- Modern ES6+ codebases
- TypeScript migration projects
- React component development
- Node.js backend services

### **Suggested Enhancement**
```javascript
// Pattern commonly seen in:
// - React hooks usage
// - Modern async/await patterns
// - TypeScript strict mode
```

### **Community Benefit**
JavaScript/TypeScript is widely used - this enhancement would help many developers.
""",
        }

    # Add templates for other languages...

    return {
        "title": f"Enhancement: Improve {ecosystem.language.value} classification",
        "body": "Generic template",
    }


def _generate_learning_patterns(ecosystem: LanguageEcosystem) -> List[str]:
    """Generate learning patterns specific to each language."""

    patterns = []

    if ecosystem.language == SupportedLanguage.PYTHON:
        patterns = [
            "Line length violations in Python are usually safe to auto-fix",
            "Import sorting issues (isort) are always safe to fix",
            "Missing docstrings often have standard patterns",
            "Unused imports can be safely removed in most cases",
        ]

    elif ecosystem.language == SupportedLanguage.JAVASCRIPT:
        patterns = [
            "Unused variables in React often indicate missing dependencies",
            "Semicolon issues are always safe to auto-fix",
            "Const vs let preferences are safe to change",
            "Indentation issues in JS/TS are formatting-only",
        ]

    elif ecosystem.language == SupportedLanguage.ANSIBLE:
        patterns = [
            "YAML formatting issues are always safe to fix",
            "Task naming is a style preference, usually safe",
            "Document start markers are formatting conventions",
            "Key duplicates are structural errors, safe to fix",
        ]

    return patterns


def demonstrate_multi_language_learning():
    """Demonstrate how community learning works across languages."""

    print("🌍 Multi-Language Community Learning System")
    print("=" * 60)

    examples = generate_language_specific_examples()

    for language, data in examples.items():
        ecosystem = LANGUAGE_ECOSYSTEMS[SupportedLanguage(language)]

        print(f"\n🔧 {language.upper()} ECOSYSTEM")
        print(f"   Linters: {', '.join(ecosystem.linters)}")
        print(f"   Community Size: {ecosystem.community_size}")
        print(f"   Example Repos: {', '.join(ecosystem.github_repo_examples[:2])}")

        if data["real_world_scenarios"]:
            print("\n   📊 Real-World Learning Examples:")
            for scenario in data["real_world_scenarios"][:2]:
                print(f"   • {scenario['error'][:50]}...")
                print(
                    f"     Success Rate: {scenario['success_rate']}, "
                    f"Fix Time: {scenario['fix_time']}"
                )

        print("\n   🧠 Learning Patterns:")
        for pattern in data["learning_patterns"][:2]:
            print(f"   • {pattern}")

    print("\n🎯 UNIVERSAL BENEFITS")
    print("=" * 60)
    print("✅ Each language ecosystem contributes unique patterns")
    print("✅ Cross-language learning (YAML issues affect multiple languages)")
    print("✅ Language-specific GitHub issue templates")
    print("✅ Community size determines contribution impact")
    print("✅ Ecosystem-aware classification improvements")


if __name__ == "__main__":
    demonstrate_multi_language_learning()
