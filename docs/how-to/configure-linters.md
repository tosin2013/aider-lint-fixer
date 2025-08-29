# Configure Linters

This guide explains how to configure linters in aider-lint-fixer for optimal code quality and team consistency.

## Configuration Overview

aider-lint-fixer supports multiple configuration approaches:
- **Unified configuration**: Single file for all linters
- **Language-specific configs**: Native configuration files
- **Profile-based settings**: Different rules for different environments
- **Command-line overrides**: Runtime configuration changes

## Unified Configuration

### Basic Configuration File

Create `.aider-lint.yaml` in your project root:

```yaml
# .aider-lint.yaml
linters:
  - flake8
  - pylint
  - mypy
  - eslint
  - ansible-lint

profiles:
  development:
    strict: false
    auto_fix: true
    parallel: true
  
  ci:
    strict: true
    fail_fast: true
    output_format: "junit"

output:
  format: "json"
  file: "lint-results.json"
```

### Advanced Configuration

```yaml
# .aider-lint.yaml
linters:
  python:
    - name: flake8
      enabled: true
      config_file: .flake8
      args: ["--max-line-length=88"]
    - name: mypy
      enabled: true
      strict_mode: true
      ignore_missing_imports: true
  
  javascript:
    - name: eslint
      enabled: true
      config_file: .eslintrc.js
      extensions: [".js", ".jsx", ".ts", ".tsx"]
    - name: prettier
      enabled: true
      check_only: true
  
  ansible:
    - name: ansible-lint
      enabled: true
      profile: "production"

profiles:
  development:
    python:
      strict: false
      auto_fix: true
    javascript:
      auto_fix: true
    output:
      format: "console"
  
  ci:
    python:
      strict: true
      mypy:
        disallow_untyped_defs: true
    javascript:
      strict: true
    output:
      format: "junit"
      file: "test-results/lint.xml"

exclude_patterns:
  - "build/"
  - "dist/"
  - "node_modules/"
  - "*.min.js"
  - "__pycache__/"
```

## Language-Specific Configuration

### Python Linters

#### Flake8 Configuration

Create `.flake8` or add to `pyproject.toml`:

```ini
# .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    .venv
per-file-ignores =
    __init__.py:F401
    tests/*:S101
```

```toml
# pyproject.toml
[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]
exclude = [".git", "__pycache__", "build", "dist", ".venv"]
```

#### Pylint Configuration

Create `.pylintrc` or add to `pyproject.toml`:

```ini
# .pylintrc
[MASTER]
load-plugins = pylint.extensions.docparams

[MESSAGES CONTROL]
disable = C0111,R0903,R0913

[FORMAT]
max-line-length = 88

[DESIGN]
max-args = 7
max-locals = 15
```

```toml
# pyproject.toml
[tool.pylint.messages_control]
disable = ["C0111", "R0903", "R0913"]

[tool.pylint.format]
max-line-length = 88
```

#### MyPy Configuration

Create `mypy.ini` or add to `pyproject.toml`:

```ini
# mypy.ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
ignore_missing_imports = True

[mypy-tests.*]
ignore_errors = True
```

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "tests.*"
ignore_errors = true
```

### JavaScript/TypeScript Linters

#### ESLint Configuration

Create `.eslintrc.js`:

```javascript
// .eslintrc.js
module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 12,
    sourceType: 'module',
  },
  plugins: [
    '@typescript-eslint',
  ],
  rules: {
    'indent': ['error', 2],
    'linebreak-style': ['error', 'unix'],
    'quotes': ['error', 'single'],
    'semi': ['error', 'always'],
  },
  ignorePatterns: [
    'dist/',
    'build/',
    'node_modules/',
    '*.min.js',
  ],
};
```

#### Prettier Configuration

Create `.prettierrc.js`:

```javascript
// .prettierrc.js
module.exports = {
  semi: true,
  trailingComma: 'es5',
  singleQuote: true,
  printWidth: 80,
  tabWidth: 2,
  useTabs: false,
};
```

### Ansible Configuration

Create `.ansible-lint`:

```yaml
# .ansible-lint
profile: production

exclude_paths:
  - .cache/
  - .github/
  - molecule/
  - .venv/

skip_list:
  - yaml[line-length]
  - name[casing]

warn_list:
  - experimental

use_default_rules: true
parseable: true
```

## Profile-Based Configuration

### Development Profile

Optimized for developer productivity:

```yaml
# Development profile settings
profiles:
  development:
    strict: false
    auto_fix: true
    parallel: true
    watch_mode: true
    
    python:
      flake8:
        ignore_warnings: true
      mypy:
        ignore_missing_imports: true
    
    javascript:
      eslint:
        fix: true
      prettier:
        write: true
    
    output:
      format: "console"
      show_source: true
```

### CI/CD Profile

Optimized for continuous integration:

```yaml
# CI profile settings
profiles:
  ci:
    strict: true
    fail_fast: true
    parallel: true
    
    python:
      flake8:
        max_complexity: 10
      mypy:
        strict: true
        disallow_any_generics: true
    
    javascript:
      eslint:
        max_warnings: 0
    
    output:
      format: "junit"
      file: "test-results/lint.xml"
      quiet: true
```

### Production Profile

Optimized for deployment readiness:

```yaml
# Production profile settings
profiles:
  production:
    strict: true
    security_focused: true
    
    python:
      bandit:
        enabled: true
        confidence: "high"
      safety:
        enabled: true
    
    ansible:
      ansible-lint:
        profile: "production"
        strict: true
    
    output:
      format: "sarif"
      file: "security-results.sarif"
```

## Environment Variables

Configure linters using environment variables:

```bash
# Global settings
export AIDER_LINT_CONFIG=./custom-config.yaml
export AIDER_LINT_PROFILE=development
export AIDER_LINT_CACHE_DIR=~/.cache/aider-lint

# Linter-specific settings
export FLAKE8_CONFIG=.flake8
export ESLINT_CONFIG=.eslintrc.js
export MYPY_CONFIG_FILE=mypy.ini

# Output settings
export AIDER_LINT_OUTPUT_FORMAT=json
export AIDER_LINT_OUTPUT_FILE=lint-results.json
```

## Command-Line Configuration

Override configuration at runtime:

```bash
# Basic usage with config override
aider-lint-fixer --config custom-config.yaml

# Profile selection
aider-lint-fixer --profile ci

# Linter selection
aider-lint-fixer --linters flake8,eslint,ansible-lint

# Output format override
aider-lint-fixer --output-format junit --output-file results.xml

# Strict mode override
aider-lint-fixer --strict --fail-fast

# Auto-fix mode
aider-lint-fixer --auto-fix --backup
```

## Configuration Discovery

aider-lint-fixer automatically discovers configuration files in this order:

1. **Command-line specified**: `--config path/to/config.yaml`
2. **Project root**: `.aider-lint.yaml` or `.aider-lint.yml`
3. **Home directory**: `~/.aider-lint.yaml`
4. **Language-specific**: `.flake8`, `.eslintrc.js`, etc.
5. **Default settings**: Built-in sensible defaults

## Integration Examples

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: aider-lint-fixer
        name: Aider Lint Fixer
        entry: aider-lint-fixer --profile ci
        language: system
        files: \.(py|js|ts|yml|yaml)$
        pass_filenames: false
```

### GitHub Actions

```yaml
# .github/workflows/lint.yml
name: Lint Code
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run linting
        run: |
          aider-lint-fixer \
            --profile ci \
            --output-format github-actions \
            --fail-fast
```

### VS Code Settings

```json
{
  "aider-lint-fixer.configFile": ".aider-lint.yaml",
  "aider-lint-fixer.profile": "development",
  "aider-lint-fixer.autoFix": true,
  "aider-lint-fixer.lintOnSave": true
}
```

## Troubleshooting Configuration

### Common Issues

**Configuration not found**:
```bash
# Check configuration discovery
aider-lint-fixer --show-config

# Validate configuration file
aider-lint-fixer --validate-config .aider-lint.yaml
```

**Linter conflicts**:
```bash
# Show active linters and their configs
aider-lint-fixer --list-linters --verbose

# Test specific linter configuration
aider-lint-fixer --linters flake8 --dry-run
```

**Performance issues**:
```bash
# Enable parallel processing
aider-lint-fixer --parallel --jobs 4

# Use caching
aider-lint-fixer --cache-dir ~/.cache/aider-lint
```

### Configuration Validation

```bash
# Validate configuration syntax
aider-lint-fixer --validate-config

# Test configuration with dry run
aider-lint-fixer --dry-run --verbose

# Show effective configuration
aider-lint-fixer --show-effective-config
```

## Best Practices

### Team Configuration
- Use unified configuration for consistency
- Define clear profiles for different environments
- Document configuration decisions in comments
- Version control all configuration files

### Performance Optimization
- Enable parallel processing for large codebases
- Use appropriate cache directories
- Configure exclude patterns for build artifacts
- Consider file-specific rules for performance

### Maintenance
- Regularly update linter versions
- Review and update rules based on team feedback
- Monitor configuration effectiveness
- Keep configuration files synchronized across environments

## Related Documentation

- [Red Hat Developer Guide](red-hat-developer-guide.md)
- [macOS/Ubuntu Developer Guide](macos-ubuntu-developer-guide.md)
- [Container Deployment Tutorial](../tutorials/container-deployment.md)
- [ADR 0004: Hybrid Python-JavaScript Architecture](../adrs/0004-hybrid-python-javascript-architecture.md)
