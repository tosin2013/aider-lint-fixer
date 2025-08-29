# How to Add a New Feature

This guide walks you through the process of adding a new feature to aider-lint-fixer, including new linters, AI integrations, or core functionality.

## Step 1: Plan Your Feature

Before writing code:
1. **Define Requirements**: Document what the feature should accomplish
2. **Check ADRs**: Review existing [Architectural Decision Records](../adrs/) for guidance
3. **Impact Analysis**: Consider effects on existing linters and AI integration
4. **Implementation Strategy**: Choose between plugin extension or core modification

## Step 2: Set Up Development Environment

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements-test.txt
pip install -e .

# Install pre-commit hooks
pre-commit install
```

## Step 3: Implementation Patterns

### Adding a New Linter

**1. Create Linter Class**
```python
# aider_lint_fixer/linters/your_linter.py
from .base import BaseLinter
from typing import Dict, List, Any

class YourLinter(BaseLinter):
    def __init__(self):
        super().__init__()
        self.name = "your-linter"
        self.supported_extensions = [".py", ".js"]
    
    def run_linter(self, file_path: str) -> Dict[str, Any]:
        # Implement linter execution
        pass
    
    def parse_output(self, output: str) -> List[Dict[str, Any]]:
        # Parse linter output into standard format
        pass
```

**2. Register Linter**
```python
# aider_lint_fixer/linters/__init__.py
from .your_linter import YourLinter

AVAILABLE_LINTERS = {
    "your-linter": YourLinter,
    # ... existing linters
}
```

### Adding Core Functionality

**1. Follow Plugin Architecture**
```python
# aider_lint_fixer/core/your_feature.py
class YourFeature:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def process(self, data: Any) -> Any:
        # Implement feature logic
        pass
```

**2. Add Configuration Support**
```yaml
# Add to default config schema
your_feature:
  enabled: true
  option1: value1
  option2: value2
```

## Step 4: Write Comprehensive Tests

### Unit Tests
```python
# tests/test_your_feature.py
import pytest
from aider_lint_fixer.linters.your_linter import YourLinter

class TestYourLinter:
    def test_initialization(self):
        linter = YourLinter()
        assert linter.name == "your-linter"
    
    def test_run_linter(self):
        linter = YourLinter()
        result = linter.run_linter("test_file.py")
        assert isinstance(result, dict)
    
    def test_parse_output(self):
        linter = YourLinter()
        output = "sample linter output"
        parsed = linter.parse_output(output)
        assert isinstance(parsed, list)
```

### Integration Tests
```python
# tests/integration/test_your_feature_integration.py
import pytest
from aider_lint_fixer.main import AiderLintFixer

class TestYourFeatureIntegration:
    def test_feature_with_existing_linters(self):
        # Test feature interaction with existing components
        pass
    
    def test_ai_integration(self):
        # Test AI integration if applicable
        pass
```

### Container Tests
```bash
# Test in container environment
docker build -t aider-lint-fixer-test .
docker run --rm -v $(pwd):/workspace:ro aider-lint-fixer-test \
  python -m pytest tests/test_your_feature.py
```

## Step 5: Update Documentation

### Code Documentation
```python
def your_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief description of function.
    
    Args:
        param1: Description of parameter
        param2: Description of parameter
    
    Returns:
        Dict containing result data
    
    Raises:
        ValueError: When invalid parameters provided
    """
```

### User Documentation
- **How-to Guide**: Create specific usage instructions
- **Configuration**: Document new config options
- **Examples**: Provide practical usage examples

### Update Existing Docs
```bash
# Update configure-linters.md if adding linter
# Update architecture docs if changing core functionality
# Add ADR if making architectural decisions
```

## Step 6: Testing and Validation

### Local Testing
```bash
# Run full test suite
python -m pytest tests/ -v

# Test specific feature
python -m pytest tests/test_your_feature.py -v

# Run linting on your code
flake8 aider_lint_fixer/
pylint aider_lint_fixer/
mypy aider_lint_fixer/

# Test container builds
docker build -t aider-lint-fixer-dev .
```

### Multi-Environment Testing
```bash
# Test RHEL containers (if applicable)
./scripts/containers/build-rhel9.sh --test
./scripts/containers/build-rhel10.sh --test

# Test with different Python versions
tox -e py39,py311,py312
```

## Step 7: Submit for Review

### Pre-submission Checklist
- [ ] All tests passing
- [ ] Code follows project style (black, flake8, pylint)
- [ ] Documentation updated
- [ ] Container builds successful
- [ ] No breaking changes (or properly documented)
- [ ] Performance impact assessed

### Create Pull Request
```bash
# Push feature branch
git push origin feature/your-feature-name

# Create PR with template
# Include:
# - Feature description
# - Testing performed
# - Documentation updates
# - Breaking changes (if any)
```

### Address Review Feedback
```bash
# Make requested changes
git add .
git commit -m "Address review feedback: specific changes"
git push origin feature/your-feature-name
```

## Best Practices

### Code Quality
- **Follow PEP 8**: Use black and flake8 for formatting
- **Type Hints**: Add comprehensive type annotations
- **Error Handling**: Include appropriate exception handling
- **Logging**: Add structured logging for debugging

### Architecture Alignment
- **Plugin Pattern**: Extend existing plugin architecture
- **Configuration**: Use existing config management patterns
- **AI Integration**: Follow established aider.chat integration patterns
- **Container Support**: Ensure feature works in all container environments

### Performance Considerations
- **Async Operations**: Use asyncio for I/O operations
- **Caching**: Implement caching for expensive operations
- **Resource Limits**: Respect concurrency and memory limits
- **Profiling**: Profile performance impact

### Security
- **Input Validation**: Validate all external inputs
- **Credential Handling**: Follow secure credential patterns
- **Container Security**: Maintain non-root execution
- **Dependency Security**: Check for vulnerable dependencies

## Feature-Specific Guidelines

### Adding Python Linters
- Inherit from `BaseLinter`
- Support standard configuration files
- Provide fix success rate estimates
- Handle version compatibility

### Adding JavaScript Linters
- Ensure Node.js runtime coordination
- Support TypeScript if applicable
- Handle npm dependency management
- Test cross-platform compatibility

### Adding AI Features
- Integrate through aider.chat wrapper
- Implement caching for performance
- Handle API rate limits
- Provide fallback behavior

### Adding Container Features
- Support both Docker and Podman
- Test on all base images (default, RHEL 9, RHEL 10)
- Handle SELinux contexts
- Maintain security best practices

## Related Documentation

- [Architecture Overview](../explanation/architecture-overview.md) - Understanding the system
- [Design Decisions](../explanation/design-decisions.md) - Architectural rationale
- [Configure Linters](./configure-linters.md) - Configuration patterns
- [ADR Template](../adrs/template.md) - For architectural decisions
