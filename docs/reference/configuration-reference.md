# Configuration Reference

This document provides comprehensive configuration options for aider-lint-fixer.

## Configuration File Locations

Configuration files are loaded in the following order (later files override earlier ones):

1. Default configuration (built-in)
2. Global configuration: `~/.aider-lint-fixer.yml`
3. Project configuration: `[PROJECT_ROOT]/.aider-lint-fixer.yml`
4. Environment variables
5. Command-line arguments

## Configuration File Format

Configuration files use YAML format. Here's a complete example:

```yaml
# LLM Configuration
llm:
  provider: "deepseek"  # Options: deepseek, openrouter, ollama
  model: "deepseek/deepseek-chat"
  fallback_providers:
    - "openrouter"
    - "ollama"
  api_key: null  # Set via environment variables
  api_base: null  # Optional API base URL

# Linter Configuration
linters:
  auto_detect: true
  enabled:
    - flake8
    - pylint
    - black
    - isort
    - mypy
    - eslint
    - prettier
    - tslint
    - golint
    - gofmt
    - govet
    - rustfmt
    - clippy
  smart_selection_defaults:
    development: true
    ci: false
    tutorial: true
    production: false

# Aider Configuration
aider:
  auto_commit: false
  backup_files: true
  max_retries: 3
  context_window: 8192

# Project Settings
project:
  exclude_patterns:
    - "*.min.js"
    - "*.min.css"
    - "node_modules/"
    - "__pycache__/"
    - ".git/"
    - ".venv/"
    - "venv/"
    - "build/"
    - "dist/"
    - "target/"
  include_patterns:
    - "*.py"
    - "*.js"
    - "*.ts"
    - "*.jsx"
    - "*.tsx"
    - "*.go"
    - "*.rs"
    - "*.java"
    - "*.c"
    - "*.cpp"
    - "*.h"
    - "*.hpp"

# Logging Configuration
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: "aider-lint-fixer.log"
  max_size: "10MB"
  backup_count: 5
```

## Configuration Sections

### LLM Configuration (`llm`)

Controls the Language Learning Model provider and settings.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `provider` | string | `"deepseek"` | LLM provider to use |
| `model` | string | `"deepseek/deepseek-chat"` | Specific model to use |
| `fallback_providers` | list | `["openrouter", "ollama"]` | Fallback providers if primary fails |
| `api_key` | string | `null` | API key (use environment variables) |
| `api_base` | string | `null` | Custom API base URL |

#### Supported Providers

- **deepseek**: DeepSeek AI models
- **openrouter**: OpenRouter API gateway
- **ollama**: Local Ollama models

### Linter Configuration (`linters`)

Controls which linters are enabled and how they're selected.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `auto_detect` | boolean | `true` | Automatically detect project type and enable relevant linters |
| `enabled` | list | See default list | List of enabled linters |
| `smart_selection_defaults` | object | See below | Environment-specific defaults |

#### Default Enabled Linters

- **Python**: flake8, pylint, black, isort, mypy
- **JavaScript/TypeScript**: eslint, prettier, tslint
- **Go**: golint, gofmt, govet
- **Rust**: rustfmt, clippy

#### Smart Selection Defaults

| Environment | Default | Purpose |
|-------------|---------|---------|
| `development` | `true` | Fast feedback during development |
| `ci` | `false` | Comprehensive checking in CI |
| `tutorial` | `true` | Always smart for tutorials |
| `production` | `false` | Safety first in production |

### Aider Configuration (`aider`)

Controls aider.chat integration behavior.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `auto_commit` | boolean | `false` | Automatically commit fixes |
| `backup_files` | boolean | `true` | Create backups before making changes |
| `max_retries` | integer | `3` | Maximum retries for aider operations |
| `context_window` | integer | `8192` | Context window size for AI model |

### Project Configuration (`project`)

Controls file inclusion and exclusion patterns.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `exclude_patterns` | list | See default list | Patterns to exclude from processing |
| `include_patterns` | list | See default list | Patterns to include in processing |

### Logging Configuration (`logging`)

Controls logging behavior and output.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `level` | string | `"INFO"` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `file` | string | `"aider-lint-fixer.log"` | Log file path |
| `max_size` | string | `"10MB"` | Maximum log file size |
| `backup_count` | integer | `5` | Number of backup log files to keep |

## Environment Variables

Configuration can be overridden using environment variables:

### LLM Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AIDER_LLM_PROVIDER` | Override LLM provider | `deepseek` |
| `AIDER_LLM_MODEL` | Override LLM model | `deepseek/deepseek-chat` |
| `OLLAMA_API_BASE` | Ollama API base URL | `http://localhost:11434` |

### API Key Environment Variables

| Variable | Description |
|----------|-------------|
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |

### Aider Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AIDER_AUTO_COMMIT` | Auto-commit behavior | `true` |
| `AIDER_MAX_RETRIES` | Maximum retries | `5` |

### Logging Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AIDER_LOG_LEVEL` | Log level | `DEBUG` |

### Tool-Specific Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AIDER_LINT_FIXER_DEBUG` | Enable debug mode | `true` |
| `AIDER_LINT_FIXER_LOG_LEVEL` | Tool log level | `INFO` |
| `AIDER_LINT_FIXER_MAX_FILES` | Maximum files to process | `10` |
| `AIDER_LINT_FIXER_MAX_ERRORS` | Maximum errors per file | `5` |
| `ANSIBLE_LINT_VERSION` | Ansible-lint version selection | `enterprise` |

## Command Line Options

Configuration can also be set via command-line arguments, which override all other settings:

### Basic Options

| Option | Type | Description |
|--------|------|-------------|
| `--config`, `-c` | string | Path to configuration file |
| `--verbose`, `-v` | flag | Enable verbose output |
| `--quiet`, `-q` | flag | Suppress non-error output |
| `--no-color` | flag | Disable colored output |
| `--log-file` | string | Path to log file |
| `--no-banner` | flag | Disable banner output |

### LLM Options

| Option | Type | Description |
|--------|------|-------------|
| `--llm` | string | LLM provider |
| `--model` | string | Specific model to use |
| `--ai-model` | choice | AI model for cost calculations |

### Linter Options

| Option | Type | Description |
|--------|------|-------------|
| `--linters` | string | Comma-separated list of linters |
| `--profile` | choice | Linter profile (basic, default, strict) |
| `--ansible-profile` | choice | Ansible-lint profile (basic, production) |
| `--list-linters` | flag | List all available linters |

### Processing Options

| Option | Type | Description |
|--------|------|-------------|
| `--max-files` | integer | Maximum files to process |
| `--max-errors` | integer | Maximum errors per file |
| `--dry-run` | flag | Show what would be fixed |
| `--check-only` | flag | Only check, don't fix |
| `--interactive` | flag | Confirm each fix |

### File Selection Options

| Option | Type | Description |
|--------|------|-------------|
| `--include` | string | Include patterns (multiple allowed) |
| `--exclude` | string | Exclude patterns (multiple allowed) |
| `--extensions` | string | File extensions to process |
| `--target-dir` | string | Target directory to lint |

### Smart Features

| Option | Type | Description |
|--------|------|-------------|
| `--smart-linter-selection` | flag | Enable smart linter selection |
| `--max-linter-time` | float | Time budget for linters (seconds) |
| `--confidence-threshold` | float | Minimum confidence for selection (0.0-1.0) |
| `--dag-workflow` | flag | Enable DAG workflow execution |
| `--max-workers` | integer | Maximum parallel workers |

### Cost Management

| Option | Type | Description |
|--------|------|-------------|
| `--max-cost` | float | Maximum total cost budget |
| `--max-iteration-cost` | float | Maximum cost per iteration |
| `--show-cost-prediction` | flag | Show cost predictions |

### Advanced Options

| Option | Type | Description |
|--------|------|-------------|
| `--use-architect-mode` | flag | Use architect mode for complex errors |
| `--architect-model` | string | Model for architect reasoning |
| `--editor-model` | string | Model for file editing |
| `--architect-only` | flag | Only use architect mode |

## Profile Configurations

### Basic Profile
- Minimal linter set
- Fast execution
- Good for initial setup or CI

### Default Profile
- Balanced linter selection
- Reasonable performance
- Recommended for most projects

### Strict Profile
- Comprehensive linting
- Slower execution
- Best for production-ready code

## Best Practices

1. **Start with Basic Profile**: Use the basic profile for initial setup and gradually move to stricter profiles.

2. **Use Project-Specific Configs**: Create `.aider-lint-fixer.yml` in your project root for project-specific settings.

3. **Environment Variables for Secrets**: Always use environment variables for API keys, never commit them to configuration files.

4. **Smart Selection in Development**: Enable smart linter selection during development for faster feedback.

5. **Comprehensive Checking in CI**: Disable smart selection in CI environments for thorough validation.

6. **Exclude Build Artifacts**: Always exclude build directories, node_modules, and other generated content.

7. **Log Rotation**: Configure appropriate log rotation to prevent disk space issues.

## Troubleshooting

### Common Configuration Issues

1. **Configuration Not Loading**: Check file paths and YAML syntax
2. **API Key Not Found**: Verify environment variable names and values
3. **Linters Not Found**: Ensure linters are installed and in PATH
4. **Permission Issues**: Check file permissions for config files

### Validation

Use the `--check-only` flag to validate configuration without making changes:

```bash
aider-lint-fixer --check-only --verbose
```

## Migration Guide

### From v1.x to v2.x

1. Update configuration file format from JSON to YAML
2. Rename `smart_selection` to `smart_linter_selection`
3. Add new `logging` section for log configuration
4. Update environment variable names (add `AIDER_` prefix)

### Configuration Conversion

Use the built-in migration tool:

```bash
aider-lint-fixer --migrate-config path/to/old-config.json
```

This will create a new YAML configuration file with equivalent settings.
