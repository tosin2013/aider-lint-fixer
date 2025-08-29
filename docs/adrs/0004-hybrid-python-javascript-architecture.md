# ADR 0004: Hybrid Python-JavaScript Linter Architecture

**Status**: Accepted  
**Date**: 2024-08-24  
**Deciders**: Development Team  

## Context

aider-lint-fixer needs to support multiple programming languages and their associated linting tools. The primary languages in scope are Python and JavaScript/TypeScript, each with distinct ecosystems, tooling, and best practices. A unified architecture must accommodate both language ecosystems while maintaining performance, extensibility, and ease of use.

### Problem Statement

Modern development projects increasingly use multiple programming languages:
- **Python**: Ansible playbooks, automation scripts, backend services
- **JavaScript/TypeScript**: Frontend applications, Node.js services, build tools
- **Mixed Projects**: Full-stack applications, DevOps toolchains, documentation sites

Each language ecosystem has mature linting tools with different:
- Configuration formats (YAML, JSON, TOML, INI)
- Execution models (CLI tools, language servers, plugins)
- Output formats (JSON, XML, custom text formats)
- Installation methods (pip, npm, system packages)

## Decision

We will implement a **hybrid architecture** that provides unified orchestration while preserving language-specific optimizations.

### Core Architecture Components

#### 1. Unified Plugin Interface

```python
class LinterPlugin(ABC):
    """Abstract base class for all linter plugins"""
    
    @abstractmethod
    def detect_files(self, workspace: Path) -> List[Path]:
        """Detect files this linter can process"""
        
    @abstractmethod
    def run_linter(self, files: List[Path], config: Dict) -> LinterResult:
        """Execute linter and return structured results"""
        
    @abstractmethod
    def get_default_config(self) -> Dict:
        """Return default configuration for this linter"""
```

#### 2. Language-Specific Implementations

**Python Linter Ecosystem**:
- **Base Class**: `PythonLinterBase`
- **Implementations**: `Flake8Linter`, `PylintLinter`, `MypyLinter`
- **Package Management**: pip-based installation and virtual environments
- **Configuration**: pyproject.toml, setup.cfg, .flake8 files

**JavaScript Linter Ecosystem**:
- **Base Class**: `JavaScriptLinterBase`
- **Implementations**: `ESLintLinter`, `JSHintLinter`, `PrettierLinter`
- **Package Management**: npm/yarn-based installation
- **Configuration**: .eslintrc.js, package.json, prettier.config.js

#### 3. Orchestration Layer

```python
class LinterOrchestrator:
    """Coordinates execution across multiple language ecosystems"""
    
    def __init__(self):
        self.python_linters = []
        self.javascript_linters = []
        self.ansible_linters = []
    
    def discover_linters(self, workspace: Path) -> Dict[str, List[LinterPlugin]]:
        """Auto-detect applicable linters based on project structure"""
        
    def execute_parallel(self, linter_groups: Dict) -> CombinedResults:
        """Execute linter groups in parallel for performance"""
```

### Integration Patterns

#### 1. Configuration Unification

```yaml
# aider-lint-config.yaml
linters:
  python:
    - name: flake8
      enabled: true
      config_file: .flake8
    - name: mypy
      enabled: true
      strict_mode: true
  
  javascript:
    - name: eslint
      enabled: true
      config_file: .eslintrc.js
    - name: prettier
      enabled: true
      check_only: true

profiles:
  development:
    strict: false
    auto_fix: true
  
  ci:
    strict: true
    fail_fast: true
```

#### 2. Result Normalization

```python
@dataclass
class LinterIssue:
    """Normalized issue representation across all linters"""
    file_path: Path
    line: int
    column: int
    severity: Severity  # ERROR, WARNING, INFO
    rule_id: str
    message: str
    linter_name: str
    fixable: bool = False
    
@dataclass
class LinterResult:
    """Normalized result container"""
    issues: List[LinterIssue]
    execution_time: float
    linter_version: str
    config_used: Dict
```

#### 3. Dependency Management

**Python Dependencies**:
```python
# Managed via pip and virtual environments
PYTHON_LINTERS = {
    'flake8': 'flake8>=6.0.0',
    'pylint': 'pylint>=2.17.0',
    'mypy': 'mypy>=1.5.0'
}
```

**JavaScript Dependencies**:
```python
# Managed via npm with package.json
JAVASCRIPT_LINTERS = {
    'eslint': '^8.45.0',
    'jshint': '^2.13.6',
    'prettier': '^3.0.0'
}
```

## Rationale

### Why Hybrid Architecture?

1. **Language Ecosystem Respect**: Each language has mature tooling that works best within its native environment
2. **Performance Optimization**: Language-specific optimizations (e.g., Node.js for JavaScript tools)
3. **Configuration Familiarity**: Developers can use existing configuration files
4. **Extensibility**: Easy to add new linters within each ecosystem
5. **Maintenance**: Separate concerns reduce complexity

### Alternative Approaches Considered

#### 1. Single Language Implementation
**Rejected**: Would require reimplementing mature linting logic, losing ecosystem benefits

#### 2. Shell Script Orchestration
**Rejected**: Poor error handling, difficult testing, limited cross-platform support

#### 3. Docker-Only Approach
**Rejected**: Performance overhead, complexity for simple use cases

## Implementation Strategy

### Phase 1: Core Infrastructure
- Implement abstract base classes and interfaces
- Create Python linter base class and core implementations
- Develop result normalization and aggregation

### Phase 2: JavaScript Integration
- Implement JavaScript linter base class
- Add ESLint, JSHint, and Prettier support
- Create npm dependency management

### Phase 3: Advanced Features
- Parallel execution optimization
- Configuration file auto-discovery
- Auto-fix capabilities across languages

### Phase 4: Ecosystem Extensions
- Additional Python linters (bandit, black, isort)
- TypeScript-specific tooling
- YAML and Markdown linters

## Consequences

### Positive

- **Unified Experience**: Single command to lint multi-language projects
- **Best-of-Breed Tools**: Leverage mature, language-specific linters
- **Performance**: Parallel execution across language ecosystems
- **Extensibility**: Clear plugin architecture for new linters
- **Configuration Flexibility**: Support both unified and language-specific configs

### Negative

- **Complexity**: More complex than single-language solutions
- **Dependencies**: Requires both Python and Node.js environments
- **Maintenance**: Need to track multiple ecosystem changes
- **Installation**: More complex setup for full functionality

### Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Dependency conflicts | High | Use virtual environments and version pinning |
| Performance degradation | Medium | Implement parallel execution and caching |
| Configuration complexity | Medium | Provide sensible defaults and auto-discovery |
| Ecosystem fragmentation | Low | Monitor and adapt to tooling changes |

## Validation

### Success Criteria

1. **Functionality**: Successfully lint Python and JavaScript files in mixed projects
2. **Performance**: <2x overhead compared to running linters individually
3. **Usability**: Single configuration file for multi-language projects
4. **Extensibility**: Add new linter with <50 lines of code

### Testing Strategy

- **Unit Tests**: Each linter plugin independently
- **Integration Tests**: Multi-language project scenarios
- **Performance Tests**: Large codebases with mixed languages
- **Compatibility Tests**: Various Python and Node.js versions

## Related ADRs

- [ADR 0001: Record Architecture Decisions](0001-record-architecture-decisions.md)
- [ADR 0002: AI Integration Architecture](0002-ai-integration-architecture.md)
- [ADR 0003: Modular Plugin System](0003-modular-plugin-system.md)
- [ADR 0005: Python Linter Ecosystem](0005-python-linter-ecosystem.md)
- [ADR 0006: JavaScript/TypeScript Linter Ecosystem](0006-javascript-typescript-linter-ecosystem.md)

## Implementation Evidence

### File Structure
```
aider_lint_fixer/
├── linters/
│   ├── base.py              # Abstract base classes
│   ├── python/
│   │   ├── __init__.py
│   │   ├── base.py          # PythonLinterBase
│   │   ├── flake8.py        # Flake8Linter
│   │   ├── pylint.py        # PylintLinter
│   │   └── mypy.py          # MypyLinter
│   ├── javascript/
│   │   ├── __init__.py
│   │   ├── base.py          # JavaScriptLinterBase
│   │   ├── eslint.py        # ESLintLinter
│   │   ├── jshint.py        # JSHintLinter
│   │   └── prettier.py      # PrettierLinter
│   └── orchestrator.py      # LinterOrchestrator
├── config/
│   ├── defaults.py          # Default configurations
│   └── loader.py            # Configuration loading
└── results/
    ├── normalizer.py        # Result normalization
    └── formatter.py         # Output formatting
```

### Configuration Examples

**Unified Configuration**:
```yaml
# .aider-lint.yaml
linters:
  - flake8
  - eslint
  - ansible-lint

profiles:
  strict:
    python:
      flake8:
        max-line-length: 88
    javascript:
      eslint:
        rules:
          semi: error
```

**Language-Specific Fallback**:
```python
# Automatically discovers and uses:
# - .flake8, pyproject.toml for Python
# - .eslintrc.js, package.json for JavaScript
# - .ansible-lint for Ansible
```

This hybrid architecture provides the foundation for supporting multiple programming languages while maintaining the flexibility and performance characteristics needed for modern development workflows.
