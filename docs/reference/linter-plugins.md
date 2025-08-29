# Linter Plugins Reference

This document provides comprehensive information about supported linters, their plugin architecture, and integration capabilities with aider-lint-fixer.

## Plugin Architecture

aider-lint-fixer uses a modular plugin architecture that allows for extensible linter support through the `BaseLinter` interface.

### Core Components

#### BaseLinter Interface
All linters implement the standardized `BaseLinter` interface:

```python
class BaseLinter:
    def is_available(self) -> bool
    def run(self, files: List[str]) -> LinterResult
    def is_success(self, return_code: int, errors: List[LintError], warnings: List[LintError]) -> bool
    def get_supported_extensions(self) -> List[str]
    def get_version(self) -> Optional[str]
```

#### Modular Linter System
Located in `aider_lint_fixer/linters/`, each linter is a self-contained module:

- **AnsibleLintLinter**: `ansible_lint_linter.py`
- **ESLintLinter**: `eslint_linter.py`
- **Flake8Linter**: `flake8_linter.py`
- **JSHintLinter**: `jshint_linter.py`
- **PrettierLinter**: `prettier_linter.py`
- **PylintLinter**: `pylint_linter.py`

## Supported Linters by Language

### Python Linters

#### flake8
**Description**: Style guide enforcement and error detection for Python code.

| Attribute | Value |
|-----------|-------|
| **Tested Version** | Latest stable |
| **Supported Versions** | 3.x, 4.x, 5.x, 6.x |
| **File Extensions** | `.py`, `.pyi` |
| **Profile Support** | ✅ Basic, Default, Strict |
| **Output Format** | Text, JSON (limited) |
| **Installation** | `pip install flake8` |

**Key Features:**
- PEP 8 style checking
- Syntax error detection
- Complexity analysis (mccabe)
- Plugin ecosystem support

**Common Rules:**
- `E101`: Indentation issues
- `E501`: Line too long
- `F401`: Unused imports
- `W291`: Trailing whitespace

#### pylint
**Description**: Comprehensive code analysis and quality checking for Python.

| Attribute | Value |
|-----------|-------|
| **Tested Version** | 3.3.7 |
| **Supported Versions** | 3.3, 3.2, 3.1, 3.0, 2.x |
| **File Extensions** | `.py`, `.pyi` |
| **Profile Support** | ✅ Basic, Default, Strict |
| **Output Format** | Text, JSON |
| **Installation** | `pip install pylint` |

**Key Features:**
- Code quality analysis
- Error and warning detection
- Code metrics and statistics
- Configurable rule sets

**Common Rules:**
- `C0103`: Invalid name
- `W0612`: Unused variable
- `R0903`: Too few public methods
- `E1101`: Instance has no member

#### mypy
**Description**: Static type checking for Python code.

| Attribute | Value |
|-----------|-------|
| **Tested Version** | Latest stable |
| **Supported Versions** | 1.x, 0.9x |
| **File Extensions** | `.py`, `.pyi` |
| **Profile Support** | ✅ Basic, Default, Strict |
| **Output Format** | Text, JSON |
| **Installation** | `pip install mypy` |

**Key Features:**
- Static type checking
- Type inference
- Gradual typing support
- Integration with IDEs

#### black
**Description**: Uncompromising Python code formatter.

| Attribute | Value |
|-----------|-------|
| **Tested Version** | Latest stable |
| **Supported Versions** | 22.x, 23.x, 24.x |
| **File Extensions** | `.py`, `.pyi` |
| **Profile Support** | ✅ Basic, Default, Strict |
| **Output Format** | Text, diff |
| **Installation** | `pip install black` |

**Key Features:**
- Automatic code formatting
- Consistent style enforcement
- Minimal configuration
- Fast performance

#### isort
**Description**: Import statement organizer for Python.

| Attribute | Value |
|-----------|-------|
| **Tested Version** | Latest stable |
| **Supported Versions** | 5.x |
| **File Extensions** | `.py`, `.pyi` |
| **Profile Support** | ✅ Basic, Default, Strict |
| **Output Format** | Text, diff |
| **Installation** | `pip install isort` |

**Key Features:**
- Import statement sorting
- Section organization
- Multiple style profiles
- Integration with black

### JavaScript/TypeScript Linters

#### ESLint
**Description**: Comprehensive linting and code quality tool for JavaScript/TypeScript.

| Attribute | Value |
|-----------|-------|
| **Tested Version** | 8.57.1 |
| **Supported Versions** | 8.57.x, 8.5.x, 8.x, 7.x |
| **File Extensions** | `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs` |
| **Profile Support** | ✅ Basic, Default, Strict |
| **Output Format** | Text, JSON, Stylish |
| **Installation** | `npm install -g eslint` |

**Key Features:**
- Syntax error detection
- Style checking
- TypeScript support via plugins
- Extensive rule ecosystem
- Auto-fixing capabilities

**Configuration Files:**
- `.eslintrc.js`, `.eslintrc.json`, `.eslintrc.yml`
- `package.json` (eslintConfig)
- `.eslintrc.yaml`

**Common Rules:**
- `semi`: Semicolon requirements
- `quotes`: Quote style consistency
- `no-unused-vars`: Unused variable detection
- `prefer-const`: Prefer const over let
- `@typescript-eslint/no-unused-vars`: TypeScript unused vars

**TypeScript Integration:**
```json
{
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint"],
  "extends": ["@typescript-eslint/recommended"],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/explicit-function-return-type": "warn"
  }
}
```

#### JSHint
**Description**: Community-driven tool for detecting errors in JavaScript code.

| Attribute | Value |
|-----------|-------|
| **Tested Version** | 2.13.6 |
| **Supported Versions** | 2.13.x, 2.1.x, 2.x |
| **File Extensions** | `.js`, `.mjs`, `.cjs` |
| **Profile Support** | ✅ Basic, Default, Strict |
| **Output Format** | Text, JSON |
| **Installation** | `npm install -g jshint` |

**Key Features:**
- JavaScript error detection
- Code quality warnings
- Configurable options
- Legacy project support

**Configuration Files:**
- `.jshintrc`
- `package.json` (jshintConfig)

#### Prettier
**Description**: Opinionated code formatter for multiple languages.

| Attribute | Value |
|-----------|-------|
| **Tested Version** | 3.6.2 |
| **Supported Versions** | 3.6.x, 3.x, 2.x |
| **File Extensions** | `.js`, `.jsx`, `.ts`, `.tsx`, `.json`, `.css`, `.scss`, `.html`, `.md`, `.yaml`, `.yml` |
| **Profile Support** | ✅ Basic, Default, Strict |
| **Output Format** | Text, formatted code |
| **Installation** | `npm install -g prettier` |

**Key Features:**
- Multi-language formatting
- Consistent code style
- Integration with ESLint
- Editor integration
- Minimal configuration

**Configuration Files:**
- `.prettierrc`, `.prettierrc.json`, `.prettierrc.yml`
- `prettier.config.js`
- `package.json` (prettier)

### Ansible Linters

#### ansible-lint
**Description**: Best practices checker for Ansible playbooks.

| Attribute | Value |
|-----------|-------|
| **Tested Version** | 25.6.1 |
| **Supported Versions** | 25.x, 24.x, 6.x |
| **File Extensions** | `.yml`, `.yaml` (Ansible playbooks) |
| **Profile Support** | ✅ Basic, Production |
| **Output Format** | Text, JSON, SARIF |
| **Installation** | `pip install ansible-lint` |

**Key Features:**
- Ansible best practices checking
- YAML syntax validation
- Security rule checking
- Role and playbook analysis
- Custom rule support

**Profiles:**
- **Basic**: Essential checks for development
- **Production**: Comprehensive checks for production deployments

**Common Rules:**
- `yaml[indentation]`: YAML indentation issues
- `name[missing]`: Missing task names
- `no-changed-when`: Missing changed_when
- `risky-shell-pipe`: Dangerous shell usage

### Go Linters

#### golint
**Description**: Linter for Go source code.

| Attribute | Value |
|-----------|-------|
| **Status** | Legacy (deprecated) |
| **Supported Versions** | Latest available |
| **File Extensions** | `.go` |
| **Profile Support** | ✅ Basic, Default, Strict |
| **Output Format** | Text |
| **Installation** | `go install golang.org/x/lint/golint@latest` |

**Note**: golint is deprecated. Consider using `revive` or `golangci-lint` instead.

#### gofmt
**Description**: Go code formatter.

| Attribute | Value |
|-----------|-------|
| **Tested Version** | Built-in with Go |
| **Supported Versions** | All Go versions |
| **File Extensions** | `.go` |
| **Profile Support** | ✅ Basic, Default, Strict |
| **Output Format** | Text, diff |
| **Installation** | Included with Go |

**Key Features:**
- Automatic code formatting
- Consistent Go style
- Built-in with Go toolchain

#### go vet
**Description**: Static analysis tool for Go.

| Attribute | Value |
|-----------|-------|
| **Tested Version** | Built-in with Go |
| **Supported Versions** | All Go versions |
| **File Extensions** | `.go` |
| **Profile Support** | ✅ Basic, Default, Strict |
| **Output Format** | Text |
| **Installation** | Included with Go |

**Key Features:**
- Static analysis
- Bug detection
- Go best practices

### Rust Linters

#### rustfmt
**Description**: Rust code formatter.

| Attribute | Value |
|-----------|-------|
| **Tested Version** | Latest stable |
| **Supported Versions** | Stable Rust versions |
| **File Extensions** | `.rs` |
| **Profile Support** | ✅ Basic, Default, Strict |
| **Output Format** | Text, diff |
| **Installation** | `rustup component add rustfmt` |

**Key Features:**
- Automatic Rust formatting
- Configurable style options
- Integration with Cargo

#### clippy
**Description**: Rust linter for catching common mistakes.

| Attribute | Value |
|-----------|-------|
| **Tested Version** | Latest stable |
| **Supported Versions** | Stable Rust versions |
| **File Extensions** | `.rs` |
| **Profile Support** | ✅ Basic, Default, Strict |
| **Output Format** | Text, JSON |
| **Installation** | `rustup component add clippy` |

**Key Features:**
- Lint checking for Rust
- Performance suggestions
- Idiomatic code recommendations

## Plugin Development

### Creating Custom Linters

To add support for a new linter, create a class inheriting from `BaseLinter`:

```python
from aider_lint_fixer.linters.base_linter import BaseLinter, LinterResult

class MyCustomLinter(BaseLinter):
    def __init__(self, project_path: str):
        super().__init__(project_path)
        self.name = "my-custom-linter"
    
    def is_available(self) -> bool:
        """Check if the linter is installed and available."""
        try:
            result = subprocess.run(
                ["my-linter", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def run(self, files: List[str]) -> LinterResult:
        """Run the linter on specified files."""
        # Implementation details
        pass
    
    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return [".myext"]
```

### Plugin Registration

Add your linter to the plugin registry:

```python
# In aider_lint_fixer/linters/__init__.py
try:
    from .my_custom_linter import MyCustomLinter
    MY_CUSTOM_AVAILABLE = True
except ImportError:
    MY_CUSTOM_AVAILABLE = False

if MY_CUSTOM_AVAILABLE:
    __all__.append("MyCustomLinter")
```

### Testing Framework

Create comprehensive tests for your linter plugin:

```python
def test_my_custom_linter():
    """Test the custom linter functionality."""
    linter = MyCustomLinter("/path/to/project")
    
    # Test availability
    assert linter.is_available()
    
    # Test file processing
    result = linter.run(["test_file.myext"])
    assert isinstance(result, LinterResult)
    
    # Test error detection
    assert len(result.errors) > 0
```

## Configuration Integration

### Linter-Specific Configuration

Each linter can be configured individually in `.aider-lint-fixer.yml`:

```yaml
linters:
  eslint:
    enabled: true
    config_file: ".eslintrc.custom.js"
    extra_args: ["--max-warnings", "0"]
  
  flake8:
    enabled: true
    max_line_length: 88
    ignore: ["E203", "W503"]
  
  ansible-lint:
    enabled: true
    profile: "production"
    exclude_paths: ["roles/legacy/"]
```

### Profile-Specific Settings

Configure different behavior for different profiles:

```yaml
profiles:
  basic:
    linters:
      enabled: ["flake8", "eslint"]
      strict_mode: false
  
  strict:
    linters:
      enabled: ["flake8", "pylint", "mypy", "eslint"]
      strict_mode: true
      fail_on_warning: true
```

## Performance Optimization

### Smart Linter Selection

Enable intelligent linter selection based on project analysis:

```bash
# Enable smart selection
aider-lint-fixer --smart-linter-selection ./src

# Set time budget for linters
aider-lint-fixer --max-linter-time 30.0 ./src

# Set confidence threshold
aider-lint-fixer --confidence-threshold 0.8 ./src
```

### Parallel Processing

Utilize DAG workflow for parallel linter execution:

```bash
# Enable parallel processing
aider-lint-fixer --dag-workflow ./src

# Set maximum workers
aider-lint-fixer --max-workers 8 ./src
```

### Caching

Linter results are cached to improve performance on subsequent runs:

- **Cache Location**: `.aider-lint-cache/`
- **Cache Invalidation**: Based on file modification times
- **Cache Management**: Automatic cleanup of stale entries

## Integration Examples

### CI/CD Integration

#### GitHub Actions
```yaml
name: Lint and Fix
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Setup Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.11'
      - name: Install linters
        run: |
          npm install -g eslint prettier
          pip install flake8 pylint black
      - name: Run aider-lint-fixer
        run: aider-lint-fixer --check-only --output-format json ./src
```

#### GitLab CI
```yaml
lint_and_fix:
  stage: test
  image: node:18
  before_script:
    - npm install -g eslint prettier
    - pip install aider-lint-fixer flake8 pylint
  script:
    - aider-lint-fixer --check-only ./src
  artifacts:
    reports:
      junit: lint-report.xml
```

### Pre-commit Integration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: aider-lint-fixer
        name: Aider Lint Fixer
        entry: aider-lint-fixer
        language: system
        files: '\.(py|js|ts|jsx|tsx|yml|yaml)$'
        args: ['--auto-fix', '--profile', 'basic']
```

### IDE Integration

#### VS Code
```json
{
  "tasks": [
    {
      "label": "Aider Lint Fixer",
      "type": "shell",
      "command": "aider-lint-fixer",
      "args": ["--interactive", "${workspaceFolder}/src"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    }
  ]
}
```

## Troubleshooting

### Common Issues

#### Linter Not Detected
```bash
# Check linter availability
aider-lint-fixer --list-linters

# Force linter check
aider-lint-fixer --verbose --dry-run ./src
```

#### Configuration Conflicts
```bash
# Validate configuration
aider-lint-fixer --check-config

# Show effective configuration
aider-lint-fixer --show-config
```

#### Performance Issues
```bash
# Enable smart selection
aider-lint-fixer --smart-linter-selection

# Reduce scope
aider-lint-fixer --max-files 50 ./src

# Use specific linters only
aider-lint-fixer --linters flake8,eslint ./src
```

### Debug Information

Enable verbose logging for detailed plugin information:

```bash
aider-lint-fixer --verbose --debug ./src
```

This provides:
- Plugin loading details
- Linter detection results
- Configuration resolution
- Performance metrics

## Version Compatibility

### Supported Version Matrix

| Language | Linter | Tested | Supported | Notes |
|----------|--------|--------|-----------|-------|
| Python | flake8 | Latest | 3.x-6.x | Full feature support |
| Python | pylint | 3.3.7 | 2.x-3.x | JSON output recommended |
| Python | mypy | Latest | 0.9x-1.x | Type checking support |
| Python | black | Latest | 22.x-24.x | Formatting only |
| Python | isort | Latest | 5.x | Import sorting |
| JavaScript | ESLint | 8.57.1 | 7.x-8.x | TypeScript via plugins |
| JavaScript | JSHint | 2.13.6 | 2.x | Legacy support |
| JavaScript | Prettier | 3.6.2 | 2.x-3.x | Multi-language formatting |
| Ansible | ansible-lint | 25.6.1 | 6.x-25.x | Multiple profiles |
| Go | gofmt | Built-in | All Go | Standard formatting |
| Go | go vet | Built-in | All Go | Static analysis |
| Rust | rustfmt | Latest | Stable | Standard formatting |
| Rust | clippy | Latest | Stable | Lint checking |

### Migration Guide

When upgrading linter versions, use the migration helper:

```bash
# Check compatibility
aider-lint-fixer --check-versions

# Generate migration report
aider-lint-fixer --migration-report
```

This comprehensive linter plugins reference provides all the information needed to understand, configure, and extend the linter ecosystem in aider-lint-fixer.
