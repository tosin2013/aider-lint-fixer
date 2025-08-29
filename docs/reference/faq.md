# Frequently Asked Questions

This document answers common questions about aider-lint-fixer usage, configuration, and troubleshooting.

## General Questions

### What is aider-lint-fixer?

aider-lint-fixer is an AI-powered tool that automatically detects and fixes linting issues across multiple programming languages. It supports Python, JavaScript/TypeScript, and Ansible with a unified interface and intelligent auto-fixing capabilities.

### Which linters are supported?

**Python**:
- flake8 (style and error checking)
- pylint (comprehensive code analysis)
- mypy (static type checking)
- bandit (security analysis)
- black (code formatting)

**JavaScript/TypeScript**:
- ESLint (linting and style checking)
- JSHint (error detection)
- Prettier (code formatting)
- TSLint (TypeScript-specific, deprecated but supported)

**Ansible**:
- ansible-lint (playbook and role validation)

**Other**:
- YAML linting for configuration files
- Markdown linting for documentation

### How does auto-fixing work?

aider-lint-fixer uses AI to understand code context and apply intelligent fixes:
1. **Pattern Recognition**: Identifies common linting issues
2. **Context Analysis**: Understands surrounding code structure
3. **Safe Transformations**: Applies fixes that preserve functionality
4. **Backup Creation**: Creates backups before making changes
5. **Validation**: Re-runs linters to verify fixes

## Installation and Setup

### How do I install aider-lint-fixer?

**Container-based (Recommended)**:
```bash
# macOS/Ubuntu - use default container
docker build -t aider-lint-fixer:latest .
docker run --rm -v $(pwd):/workspace:ro aider-lint-fixer:latest

# RHEL - build customer container
./scripts/containers/build-rhel9.sh --validate
podman run --rm -v $(pwd):/workspace:ro my-company/aider-lint-fixer:rhel9
```

**Native Installation**:
```bash
# Create virtual environment
python3 -m venv ~/.venv/aider-lint-fixer
source ~/.venv/aider-lint-fixer/bin/activate

# Install from source
pip install -e .

# Install additional linters
pip install flake8 pylint mypy
npm install -g eslint prettier
```

### What are the system requirements?

**Minimum Requirements**:
- Python 3.9+ (Python 3.11+ recommended)
- 2GB RAM
- 1GB disk space

**For JavaScript Support**:
- Node.js 16+ (Node.js 18+ recommended)
- npm or yarn

**For Container Usage**:
- Docker or Podman
- 4GB RAM recommended for large projects

### How do I configure linters?

Create `.aider-lint.yaml` in your project root:
```yaml
linters:
  - flake8
  - eslint
  - ansible-lint

profiles:
  development:
    auto_fix: true
    strict: false
  ci:
    strict: true
    fail_fast: true
```

See [Configure Linters](../how-to/configure-linters.md) for detailed configuration options.

## Usage Questions

### How do I run linting on my project?

**Basic Usage**:
```bash
# Lint entire project
aider-lint-fixer

# Lint specific files
aider-lint-fixer file1.py file2.js

# Use specific linters
aider-lint-fixer --linters flake8,eslint

# Auto-fix issues
aider-lint-fixer --auto-fix --backup
```

**Container Usage**:
```bash
# Default container
docker run --rm -v $(pwd):/workspace:ro aider-lint-fixer:latest

# RHEL container
podman run --rm -v $(pwd):/workspace:ro my-company/aider-lint-fixer:rhel9
```

### Can I exclude certain files or directories?

Yes, use exclude patterns in your configuration:

```yaml
# .aider-lint.yaml
exclude_patterns:
  - "build/"
  - "dist/"
  - "node_modules/"
  - "*.min.js"
  - "__pycache__/"
  - ".git/"
```

Or use command-line options:
```bash
aider-lint-fixer --exclude "build/,dist/,*.min.js"
```

### How do I integrate with my IDE?

**VS Code**:
1. Install the aider-lint-fixer extension
2. Configure in settings.json:
```json
{
  "aider-lint-fixer.configFile": ".aider-lint.yaml",
  "aider-lint-fixer.autoFix": true,
  "aider-lint-fixer.lintOnSave": true
}
```

**PyCharm/IntelliJ**:
1. Add external tool configuration
2. Program: `aider-lint-fixer`
3. Arguments: `--file $FilePath$`

See platform-specific guides for detailed IDE integration:
- [macOS/Ubuntu Developer Guide](../how-to/macos-ubuntu-developer-guide.md)
- [Red Hat Developer Guide](../how-to/red-hat-developer-guide.md)

### How do I use different profiles?

Profiles allow different configurations for different environments:

```bash
# Use development profile (auto-fix enabled)
aider-lint-fixer --profile development

# Use CI profile (strict mode)
aider-lint-fixer --profile ci

# Use production profile (security-focused)
aider-lint-fixer --profile production
```

## Container Questions

### What's the difference between default and RHEL containers?

**Default Container** (macOS/Ubuntu):
- Latest ansible-lint and linting tools
- No subscription requirements
- Optimized for development environments
- Uses Docker

**RHEL Containers** (Enterprise):
- Version-specific ansible-core (2.14 for RHEL 9, 2.16+ for RHEL 10)
- Requires Red Hat subscription for building
- Customer-build approach for compliance
- Uses Podman (RHEL native)

### Why do I need to build RHEL containers myself?

Red Hat licensing requires customers to build containers with their own subscriptions:
- UBI images don't include ansible-core by default
- ansible-core requires AppStream repository access
- Cannot distribute pre-built containers with ansible-core
- Ensures compliance with Red Hat subscription terms

### How do I troubleshoot container builds?

**RHEL Container Issues**:
```bash
# Check subscription status
subscription-manager status

# Validate build script
./scripts/containers/build-rhel9.sh --dry-run

# Debug build interactively
podman run -it --entrypoint /bin/bash registry.redhat.io/ubi9/ubi:latest
```

**General Container Issues**:
```bash
# Check container runtime
docker info  # or podman info

# Clean up containers and images
docker system prune -a

# Check resource usage
docker stats
```

## Configuration Questions

### How do I handle conflicting linter rules?

1. **Use unified configuration** to manage conflicts:
```yaml
# .aider-lint.yaml
linters:
  python:
    flake8:
      ignore: ["E203", "W503"]  # Conflicts with black
    black:
      line_length: 88
```

2. **Use per-file ignores**:
```ini
# .flake8
per-file-ignores =
    __init__.py:F401
    tests/*:S101
```

3. **Configure linter precedence**:
```yaml
# .aider-lint.yaml
linter_precedence:
  - black      # Formatting takes precedence
  - flake8     # Then style checking
  - pylint     # Finally comprehensive analysis
```

### How do I configure for monorepos?

Use directory-specific configurations:

```yaml
# .aider-lint.yaml (root)
linters:
  - flake8
  - eslint

directory_configs:
  backend/:
    linters:
      - flake8
      - pylint
      - mypy
    python:
      strict: true
  
  frontend/:
    linters:
      - eslint
      - prettier
    javascript:
      typescript: true
  
  ansible/:
    linters:
      - ansible-lint
    ansible:
      profile: production
```

### Can I use existing linter configuration files?

Yes, aider-lint-fixer automatically discovers and uses:
- `.flake8`, `pyproject.toml` for Python
- `.eslintrc.js`, `package.json` for JavaScript
- `.ansible-lint` for Ansible

You can also specify configuration files explicitly:
```yaml
# .aider-lint.yaml
linters:
  python:
    flake8:
      config_file: custom-flake8.cfg
  javascript:
    eslint:
      config_file: custom-eslint.js
```

## Performance Questions

### How can I improve linting performance?

1. **Enable parallel processing**:
```bash
aider-lint-fixer --parallel --jobs 4
```

2. **Use caching**:
```bash
aider-lint-fixer --cache-dir ~/.cache/aider-lint
```

3. **Exclude unnecessary files**:
```yaml
exclude_patterns:
  - "node_modules/"
  - "build/"
  - "*.min.js"
```

4. **Use incremental linting**:
```bash
# Only lint changed files
aider-lint-fixer --changed-only

# Lint since specific commit
aider-lint-fixer --since HEAD~1
```

### Why is the first run slow?

The first run may be slower due to:
- Installing linter dependencies
- Building caches
- Analyzing entire codebase

Subsequent runs are much faster due to caching.

## Troubleshooting

### Common Error Messages

**"No linters found"**:
- Install required linters: `pip install flake8` or `npm install -g eslint`
- Check PATH configuration
- Verify virtual environment activation

**"Configuration file not found"**:
- Create `.aider-lint.yaml` in project root
- Use `--config` to specify custom location
- Check file permissions

**"Permission denied"**:
- Check file permissions: `chmod +x aider-lint-fixer`
- Use proper container volume mounts
- Verify user permissions in containers

**"Linter execution failed"**:
- Check linter installation: `flake8 --version`
- Verify configuration syntax
- Run linter directly to debug: `flake8 file.py`

### How do I debug issues?

1. **Enable verbose output**:
```bash
aider-lint-fixer --verbose --debug
```

2. **Check configuration**:
```bash
aider-lint-fixer --show-config --validate-config
```

3. **Test individual linters**:
```bash
aider-lint-fixer --linters flake8 --dry-run
```

4. **Check logs**:
```bash
# Container logs
docker logs <container-id>

# System logs
journalctl -u aider-lint-fixer
```

### How do I report bugs?

1. **Gather information**:
   - aider-lint-fixer version: `aider-lint-fixer --version`
   - System information: `uname -a`
   - Python version: `python --version`
   - Linter versions: `flake8 --version`, `eslint --version`

2. **Create minimal reproduction**:
   - Isolate the issue to specific files/configuration
   - Include configuration files
   - Provide sample code that triggers the issue

3. **Submit issue**:
   - Use GitHub issue template
   - Include all gathered information
   - Describe expected vs actual behavior

## Integration Questions

### How do I integrate with CI/CD?

**GitHub Actions**:
```yaml
- name: Run linting
  run: |
    docker run --rm -v ${{ github.workspace }}:/workspace:ro \
      aider-lint-fixer:latest \
      --profile ci --output-format github-actions
```

**Jenkins**:
```groovy
stage('Lint') {
    steps {
        sh 'aider-lint-fixer --profile ci --output-format junit'
        publishTestResults testResultsPattern: 'lint-results.xml'
    }
}
```

**GitLab CI**:
```yaml
lint:
  script:
    - aider-lint-fixer --profile ci
  artifacts:
    reports:
      junit: lint-results.xml
```

### Can I use with pre-commit hooks?

Yes, create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: aider-lint-fixer
        name: Aider Lint Fixer
        entry: aider-lint-fixer --profile ci
        language: system
        files: \.(py|js|ts|yml|yaml)$
```

### How do I integrate with code review tools?

Most code review tools support standard formats:
- **GitHub**: Use `--output-format github-actions`
- **GitLab**: Use `--output-format gitlab-ci`
- **SonarQube**: Use `--output-format sonarqube`
- **Generic**: Use `--output-format sarif` for SARIF-compatible tools

## Getting Help

### Where can I find more documentation?

- **How-to Guides**: Platform-specific setup and usage
- **Tutorials**: Step-by-step walkthroughs
- **Reference**: API documentation and configuration options
- **ADRs**: Architectural decisions and rationale

### How do I get support?

1. **Documentation**: Check relevant guides and tutorials
2. **GitHub Issues**: Search existing issues or create new ones
3. **Community Forum**: Join discussions and ask questions
4. **Enterprise Support**: Contact your Red Hat representative (for RHEL users)

### How do I contribute?

1. **Fork the repository** on GitHub
2. **Create feature branch**: `git checkout -b feature/new-linter`
3. **Add tests** for new functionality
4. **Submit pull request** with clear description
5. **Follow code review** process

See [Contributing Guide](../how-to/how-to-add-a-new-feature.md) for detailed instructions.

## Related Documentation

- [Configure Linters](../how-to/configure-linters.md)
- [Red Hat Developer Guide](../how-to/red-hat-developer-guide.md)
- [macOS/Ubuntu Developer Guide](../how-to/macos-ubuntu-developer-guide.md)
- [Container Deployment Tutorial](../tutorials/container-deployment.md)
- [API Documentation](api-documentation.md)
