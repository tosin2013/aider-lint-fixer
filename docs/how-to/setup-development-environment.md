# Setup Development Environment

This guide will help you set up your development environment for aider-lint-fixer.

## Prerequisites

- Python 3.11 or higher
- Git
- Virtual environment tool (venv)

## Step 1: Clone the Repository

```bash
git clone https://github.com/tosin2013/aider-lint-fixer.git
cd aider-lint-fixer
```

## Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -e .
pip install -r requirements-test.txt
```

## Step 4: Verify Installation

```bash
python -m aider_lint_fixer --help
```

## Step 5: Run Tests

```bash
pytest
```

## Development Tools

### Code Quality
- **Black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **flake8**: Linting

### Testing
- **pytest**: Test framework
- **coverage**: Code coverage

## Next Steps

- Read the [API Reference](../reference/api-reference.md)
- Check out [How to Add a New Feature](./how-to-add-a-new-feature.md)
- Learn about [Running Tests](./run-tests.md)
