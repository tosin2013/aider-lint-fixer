# Modular Plugin System

* Status: accepted
* Deciders: Development Team
* Date: 2025-08-24

Technical Story: Design modular architecture for supporting multiple linting tools and languages.

## Context and Problem Statement

The aider-lint-fixer project needs to support multiple linting tools (flake8, pylint, ansible-lint, etc.) and programming languages. A rigid, monolithic approach would make it difficult to add new linters or customize behavior for different project types.

## Decision Drivers

* Support for multiple linting tools and languages
* Easy extensibility for new linters
* Consistent interface across different linter implementations
* Testability and maintainability
* Configuration flexibility per linter type

## Considered Options

* Monolithic linter with conditional logic
* Plugin system with base class inheritance
* Composition-based plugin architecture
* External plugin system with discovery

## Decision Outcome

Chosen option: "Plugin system with base class inheritance", because it provides clear structure, enforces consistent interfaces, and allows for easy testing while maintaining simplicity.

### Positive Consequences

* Clear separation of concerns per linter type
* Consistent interface across all linters
* Easy to add new linter support
* Testable in isolation
* Configuration can be linter-specific

### Negative Consequences

* Additional abstraction complexity
* Potential code duplication across similar linters
* Base class changes affect all plugins

## Architecture Design

### Base Linter Class
```python
class BaseLinter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def detect_issues(self, file_path: str) -> List[LintIssue]:
        """Detect lint issues in the given file."""
        raise NotImplementedError
    
    def can_handle_file(self, file_path: str) -> bool:
        """Check if this linter can handle the file type."""
        raise NotImplementedError
    
    def get_fix_suggestions(self, issue: LintIssue) -> List[FixSuggestion]:
        """Get AI-powered fix suggestions for the issue."""
        raise NotImplementedError
```

### Linter Implementations
- `PythonFlake8Linter`: Handles Python files with flake8
- `PythonPylintLinter`: Handles Python files with pylint
- `AnsibleLintLinter`: Handles Ansible YAML files
- `JavaScriptESLintLinter`: Handles JavaScript/TypeScript files

### Plugin Discovery
- Automatic discovery of linter classes in `aider_lint_fixer/linters/`
- Registration system for third-party plugins
- Configuration-driven linter selection

## Integration Points

### With AI System
- Each linter provides context-specific information for AI prompts
- Linter-specific fix validation logic
- Error classification tailored to linter type

### With Configuration System
- Per-linter configuration sections
- Global configuration inheritance
- Environment-specific overrides

## Pros and Cons of the Options

### Monolithic linter with conditional logic

* Good, because simple implementation
* Good, because no abstraction overhead
* Bad, because becomes unwieldy with multiple linters
* Bad, because difficult to test individual linter logic
* Bad, because tight coupling between linter types

### Plugin system with base class inheritance

* Good, because clear structure and interfaces
* Good, because easy to add new linters
* Good, because testable in isolation
* Good, because consistent behavior across linters
* Bad, because additional abstraction complexity
* Bad, because base class changes affect all plugins

### Composition-based plugin architecture

* Good, because flexible composition of behaviors
* Good, because avoids inheritance issues
* Bad, because more complex to implement
* Bad, because less clear interface contracts
* Bad, because potential for inconsistent implementations

### External plugin system with discovery

* Good, because maximum extensibility
* Good, because third-party plugin support
* Bad, because complex plugin discovery mechanism
* Bad, because security concerns with external plugins
* Bad, because dependency management complexity

## Links

* [ADR-0002](0002-ai-integration-architecture.md) - AI integration that works with this plugin system
* [ADR-0004](0004-python-ecosystem-focus.md) - Python-first approach influences plugin priorities
