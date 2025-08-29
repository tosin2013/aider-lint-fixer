# Python Linter Ecosystem Support

* Status: accepted
* Deciders: Development Team
* Date: 2025-08-24

Technical Story: Define comprehensive Python linting support with flake8, pylint, and mypy integration.

## Context and Problem Statement

Python projects require multiple complementary linting tools to ensure code quality, style consistency, and type safety. Each tool serves different purposes and provides unique value in the development workflow.

## Decision Drivers

* Comprehensive Python code quality coverage
* Integration with existing Python development workflows
* Support for different Python project types and complexity levels
* Compatibility with modern Python features (3.11+)
* AI-assisted fixing capabilities for Python-specific issues

## Considered Options

* Single linter approach (flake8 only)
* Comprehensive multi-linter approach (flake8 + pylint + mypy)
* Configurable linter selection based on project needs
* External tool integration without built-in support

## Decision Outcome

Chosen option: "Comprehensive multi-linter approach (flake8 + pylint + mypy)", because each tool provides complementary analysis that together ensures comprehensive Python code quality.

### Positive Consequences

* Complete coverage of Python code quality aspects
* Flexibility to enable/disable specific linters per project
* Leverages existing Python developer toolchain knowledge
* High success rate for AI-assisted fixes on Python code
* Support for both style and semantic error detection

### Negative Consequences

* Increased complexity with multiple tool configurations
* Potential for conflicting rules between linters
* Higher resource usage when running all linters
* Learning curve for teams unfamiliar with specific tools

## Python Linter Implementations

### flake8 (Style and Error Checking)
- **Purpose**: PEP 8 style guide enforcement and basic error detection
- **Strengths**: Fast execution, widely adopted, extensive plugin ecosystem
- **Fix Success Rate**: 85-95% for style issues
- **Configuration**: `.flake8`, `setup.cfg`, `pyproject.toml` support
- **Integration**: Direct subprocess execution with structured output parsing

### pylint (Comprehensive Code Analysis)
- **Purpose**: Advanced static analysis, code complexity, and quality metrics
- **Strengths**: Deep analysis, refactoring suggestions, code smell detection
- **Fix Success Rate**: 60-80% (varies by rule complexity)
- **Configuration**: `.pylintrc`, `pyproject.toml` support
- **Integration**: JSON output format for structured error parsing

### mypy (Static Type Checking)
- **Purpose**: Type annotation validation and type safety enforcement
- **Strengths**: Catches type-related bugs, supports gradual typing
- **Fix Success Rate**: 70-85% for type annotation issues
- **Configuration**: `mypy.ini`, `pyproject.toml` support
- **Integration**: Structured output with precise error locations

## Implementation Strategy

### Plugin Architecture
```python
class PythonFlake8Linter(BaseLinter):
    def build_command(self, file_paths: List[str]) -> List[str]:
        return ["flake8", "--format=json"] + file_paths
    
    def parse_output(self, stdout: str) -> List[LintError]:
        # Parse flake8 output into structured errors
        pass

class PythonPylintLinter(BaseLinter):
    def build_command(self, file_paths: List[str]) -> List[str]:
        return ["pylint", "--output-format=json"] + file_paths
```

### Configuration Management
- **Project Detection**: Automatic detection via `pyproject.toml`, `setup.py`, `requirements.txt`
- **Configuration Hierarchy**: Project-specific → User-specific → Default configurations
- **Rule Customization**: Per-project rule enabling/disabling
- **Profile Support**: Basic, strict, and custom profiles

### AI Integration Points
- **Error Classification**: Python-specific error categorization for better AI context
- **Fix Suggestions**: Linter-aware fix generation with Python syntax understanding
- **Validation**: Post-fix validation using the same linters to ensure correctness

## Pros and Cons of the Options

### Single linter approach (flake8 only)

* Good, because simple setup and configuration
* Good, because fast execution and minimal resource usage
* Good, because widely known and adopted
* Bad, because limited analysis depth
* Bad, because misses type-related issues
* Bad, because no advanced code quality metrics

### Comprehensive multi-linter approach

* Good, because complete Python code quality coverage
* Good, because leverages best-in-class tools for each purpose
* Good, because flexible configuration per project needs
* Good, because high AI fix success rates across different issue types
* Bad, because increased setup complexity
* Bad, because potential rule conflicts between tools
* Bad, because higher resource usage

### Configurable linter selection

* Good, because flexibility to choose tools per project
* Good, because can start simple and add complexity
* Bad, because inconsistent experience across projects
* Bad, because requires deep knowledge of each tool's strengths
* Bad, because complex configuration management

### External tool integration

* Good, because no maintenance burden for linter implementations
* Good, because always uses latest tool versions
* Bad, because limited control over output format and parsing
* Bad, because difficult AI integration without structured data
* Bad, because inconsistent user experience

## Links

* [ADR-0002](0002-ai-integration-architecture.md) - AI integration that works with Python linters
* [ADR-0003](0003-modular-plugin-system.md) - Plugin architecture supporting Python linters
* [ADR-0004](0004-hybrid-python-javascript-architecture.md) - Overall hybrid architecture decision
