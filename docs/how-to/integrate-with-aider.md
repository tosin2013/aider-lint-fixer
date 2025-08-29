# Integrate with Aider

This guide explains how to integrate aider-lint-fixer with Aider AI coding assistant.

## What is Aider?

Aider is an AI-powered coding assistant that helps you write and edit code. The aider-lint-fixer tool is designed to work seamlessly with Aider to provide automated linting and code quality improvements.

## Installation

### Install Aider

```bash
pip install aider-chat
```

### Configure Aider with aider-lint-fixer

```bash
# Set up your API key (OpenAI, Anthropic, etc.)
export OPENAI_API_KEY=your_api_key_here

# Or use local models
aider --model ollama/codellama:7b
```

## Integration Workflow

### 1. Basic Integration

Run aider-lint-fixer before starting an Aider session:

```bash
python -m aider_lint_fixer --scan-directory ./src
aider
```

### 2. Automated Workflow

Create a pre-commit hook:

```bash
#!/bin/bash
# .git/hooks/pre-commit
python -m aider_lint_fixer --auto-fix
```

### 3. CI/CD Integration

```yaml
# .github/workflows/lint.yml
name: Lint Check
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run aider-lint-fixer
        run: |
          pip install aider-lint-fixer
          python -m aider_lint_fixer --check
```

## Best Practices

1. **Run linting before Aider sessions**
2. **Use incremental fixes**
3. **Review automated changes**
4. **Configure project-specific rules**

## Configuration

Create `.aider-lint-config.yml`:

```yaml
linters:
  - flake8
  - mypy
  - black
auto_fix: true
max_fixes_per_file: 10
```

## Troubleshooting

### Common Issues

- **API rate limits**: Use local models or adjust request frequency
- **Large files**: Process in chunks
- **Conflicting rules**: Configure linter priorities

## Next Steps

- [Monitor Performance](./monitor-performance.md)
- [Security Best Practices](./security-best-practices.md)
- [Run Tests](./run-tests.md)
