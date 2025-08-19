# Installation Guide

This guide provides comprehensive installation instructions for aider-lint-fixer across different environments and use cases.

## Prerequisites

- **Python**: 3.11 or higher
- **Git**: Required for aider.chat integration
- **Node.js**: 16+ (for JavaScript/TypeScript projects)
- **npm/yarn**: For Node.js package management

## Installation Methods

### 1. Standard Installation (Recommended)

```bash
pip install aider-lint-fixer
```

### 2. Installation with Learning Features

For enhanced AI-powered error classification:

```bash
pip install aider-lint-fixer[learning]
```

This includes additional dependencies:
- `scikit-learn` for machine learning models
- `pyahocorasick` for high-performance pattern matching

### 3. Development Installation

For contributors and developers:

```bash
git clone https://github.com/tosin2013/aider-lint-fixer.git
cd aider-lint-fixer
pip install -e .
```

### 4. Container Installation

Using the provided container setup:

```bash
# Build the container
docker build -t aider-lint-fixer .

# Run in container
docker run -v $(pwd):/workspace aider-lint-fixer
```

## Language-Specific Setup

### Python Projects

Install required linters:

```bash
pip install flake8 pylint black isort
```

### JavaScript/TypeScript Projects

Install ESLint and related tools:

```bash
npm install -g eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
```

### Ansible Projects

Install ansible-lint:

```bash
pip install ansible-lint
```

## Configuration

### 1. Basic Configuration

Create a `.aider-lint-fixer.json` configuration file:

```json
{
  "profile": "basic",
  "linters": ["flake8", "eslint"],
  "auto_fix": true,
  "interactive": false
}
```

### 2. AI Provider Setup

Configure your preferred AI provider for aider.chat:

```bash
# OpenAI (default)
export OPENAI_API_KEY="your-api-key"

# Claude
export ANTHROPIC_API_KEY="your-api-key"

# Or use local models
export AIDER_MODEL="ollama/codellama"
```

## Verification

Test your installation:

```bash
# Check version
aider-lint-fixer --version

# Run basic check
aider-lint-fixer --help

# Test on a sample project
aider-lint-fixer --dry-run ./sample-project
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# If you see "No module named 'aider_lint_fixer'"
pip install --upgrade aider-lint-fixer
```

#### 2. Permission Errors

```bash
# Use --user flag for user-local installation
pip install --user aider-lint-fixer
```

#### 3. Python Version Issues

```bash
# Check Python version
python --version

# Use specific Python version
python3.11 -m pip install aider-lint-fixer
```

#### 4. Container Issues

```bash
# Check if Docker is running
docker --version

# Rebuild container if needed
docker build --no-cache -t aider-lint-fixer .
```

### Getting Help

- Check the [README.md](../README.md) for basic usage
- Review [CONTRIBUTOR_VERSION_GUIDE.md](./CONTRIBUTOR_VERSION_GUIDE.md) for development setup
- Report issues on [GitHub Issues](https://github.com/tosin2013/aider-lint-fixer/issues)

## Next Steps

After installation:

1. Read the [Node.js Linters Guide](./NODEJS_LINTERS_GUIDE.md) for JavaScript/TypeScript projects
2. Check the [Linter Testing Guide](./LINTER_TESTING_GUIDE.md) for testing your setup
3. Explore the main README for usage examples and features