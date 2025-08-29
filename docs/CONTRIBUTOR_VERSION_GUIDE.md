# Contributor Version Guide

This guide is for contributors and developers working on aider-lint-fixer. It covers development setup, version management, and contribution workflows.

## Development Environment Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/aider-lint-fixer.git
cd aider-lint-fixer

# Add upstream remote
git remote add upstream https://github.com/tosin2013/aider-lint-fixer.git
```

### 2. Development Installation

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e .[learning,dev]

# Install pre-commit hooks
pre-commit install
```

### 3. Development Dependencies

The `dev` extra includes:
- `pytest` for testing
- `black` for code formatting
- `flake8` for linting
- `isort` for import sorting
- `pre-commit` for git hooks

## Version Management

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

### Current Version Tracking

The version is defined in multiple places:
- `aider_lint_fixer/__init__.py` - Main version constant
- `setup.py` - Package metadata
- `pyproject.toml` - Build configuration

### Release Process

#### 1. Prepare Release

```bash
# Update version in all files
scripts/prepare_release_v1.7.0.py  # Example script

# Update CHANGELOG.md with new features and fixes
# Update README.md with new version badges
```

#### 2. Create Release Branch

```bash
git checkout -b release/v1.7.0
git add .
git commit -m "chore: prepare release v1.7.0"
git push origin release/v1.7.0
```

#### 3. Testing

```bash
# Run full test suite
make test

# Run linting checks
make lint

# Test installation
pip install -e .
aider-lint-fixer --version
```

#### 4. Create Pull Request

Create a PR from your release branch to `main` with:
- Clear description of changes
- Updated documentation
- Version bump commits

## Development Workflow

### 1. Branch Strategy

- `main` - Stable production code
- `develop` - Development integration branch
- `feature/feature-name` - Feature development
- `bugfix/issue-number` - Bug fixes
- `release/version` - Release preparation

### 2. Code Standards

#### Python Code Style

```bash
# Format code
black aider_lint_fixer/

# Sort imports
isort aider_lint_fixer/

# Check linting
flake8 aider_lint_fixer/
```

#### Pre-commit Hooks

The following checks run automatically:
- Black formatting
- isort import sorting
- flake8 linting
- Basic syntax validation

#### Testing Requirements

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=aider_lint_fixer tests/

# Test specific module
pytest tests/test_error_analyzer.py
```

### 3. Adding New Features

#### For New Linter Support

1. Add linter configuration in `config_manager.py`
2. Update pattern matching in `pattern_matcher.py`
3. Add test cases in `tests/`
4. Update documentation

#### For New AI Providers

1. Update `aider_integration.py`
2. Add provider-specific configuration
3. Test with sample projects
4. Document setup instructions

### 4. Documentation Updates

When contributing:

1. Update relevant documentation files
2. Add docstrings for new functions/classes
3. Update README.md for new features
4. Add examples for complex features

## Testing Guide

### Test Structure

```
tests/
├── unit/           # Unit tests for individual modules
├── integration/    # Integration tests
├── fixtures/       # Test data and sample projects
└── test_*.py      # Main test files
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_error_analyzer.py

# With verbose output
pytest -v

# With coverage report
pytest --cov=aider_lint_fixer --cov-report=html
```

### Adding Tests

For new features, include:
- Unit tests for core functionality
- Integration tests for end-to-end workflows
- Edge case testing
- Error handling validation

## Debugging and Troubleshooting

### Development Debugging

```bash
# Enable debug logging
export AIDER_LINT_DEBUG=1

# Run with verbose output
aider-lint-fixer --verbose ./test-project

# Use Python debugger
python -m pdb -m aider_lint_fixer --help
```

### Common Development Issues

#### 1. Import Errors in Development

```bash
# Reinstall in development mode
pip install -e .
```

#### 2. Test Failures

```bash
# Clear pytest cache
pytest --cache-clear

# Run with detailed output
pytest -vvv
```

#### 3. Pre-commit Hook Failures

```bash
# Run manually
pre-commit run --all-files

# Skip hooks temporarily
git commit --no-verify
```

## Contribution Guidelines

### 1. Before Contributing

- Check existing issues and PRs
- Discuss major changes in issues first
- Follow the code style guidelines
- Add tests for new functionality

### 2. Pull Request Process

1. Create feature branch from `develop`
2. Make your changes with tests
3. Update documentation
4. Run full test suite
5. Create descriptive PR

### 3. Code Review

PRs require:
- Passing CI checks
- Code review approval
- Updated documentation
- Test coverage for new code

## Release History

### Recent Releases

- **v1.9.0**: Community Issue Reporting & Collaborative Improvement
- **v1.8.0**: Enhanced Interactive Mode & Progress Tracking
- **v1.7.0**: Learning System with 46.1% fixability rate
- **v1.6.0**: TypeScript Projects & Smart ESLint integration

See the project changelog for detailed release notes.

## Getting Help

- **Development Questions**: Open a discussion on GitHub
- **Bug Reports**: Create an issue with reproduction steps
- **Feature Requests**: Open an issue with detailed requirements
- **Code Review**: Tag maintainers in your PR

## Resources

- [Installation Guide](./INSTALLATION_GUIDE.md)
- [Node.js Linters Guide](./NODEJS_LINTERS_GUIDE.md)
- [Linter Testing Guide](./LINTER_TESTING_GUIDE.md)
- [Project Home](./index.md)