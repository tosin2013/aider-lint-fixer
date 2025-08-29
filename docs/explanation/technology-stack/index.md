# Technology Stack

Complete overview of technologies used in aider-lint-fixer, a Python-based linting tool with AI integration and multi-language support.

## Core Technologies

### Runtime & Language
- **Python 3.11+**: Primary development language and runtime
- **Node.js 16+**: JavaScript linter execution environment
- **Bash/Shell**: Build scripts and automation

### Package Management
- **pip**: Python package management
- **pyproject.toml**: Modern Python project configuration
- **npm**: Node.js package management for JavaScript linters
- **requirements.txt**: Python dependency specification

## Python Ecosystem

### Core Python Libraries
- **aider-chat**: AI-powered code modification integration
- **subprocess**: Process management for linter execution
- **asyncio**: Asynchronous linter execution
- **pathlib**: Modern file system operations
- **typing**: Type hints and annotations

### Configuration Management
- **PyYAML**: YAML configuration parsing
- **configparser**: INI-style configuration support
- **argparse**: Command-line interface parsing
- **os/environ**: Environment variable management

### Testing Framework
- **pytest**: Primary testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Code coverage reporting
- **unittest.mock**: Mocking for isolated tests

## Linting Tools

### Python Linters
- **flake8**: Style guide enforcement (85-95% fix success)
- **pylint**: Comprehensive code analysis (60-80% fix success)
- **mypy**: Static type checking (70-85% fix success)
- **bandit**: Security vulnerability scanning
- **black**: Code formatting
- **isort**: Import sorting

### JavaScript/TypeScript Linters
- **ESLint**: JavaScript/TypeScript linting (90-95% fix success)
- **Prettier**: Code formatting (98% fix success)
- **JSHint**: JavaScript code quality (75-85% fix success)
- **@typescript-eslint**: TypeScript-specific rules

### Infrastructure Linters
- **ansible-lint**: Ansible playbook validation (80-90% fix success)
- **yamllint**: YAML file validation
- **shellcheck**: Shell script analysis

## Container Technologies

### Container Runtimes
- **Docker**: Default container runtime (macOS/Ubuntu)
- **Podman**: Preferred RHEL container runtime
- **Container registries**: Docker Hub, Quay.io, Red Hat Registry

### Base Images
- **python:3.11-slim**: Default container base
- **registry.redhat.io/ubi9/ubi**: RHEL 9 enterprise base
- **registry.redhat.io/ubi10/ubi**: RHEL 10 enterprise base

### Container Security
- **Non-root execution**: UID 1001 for security
- **Read-only volumes**: Project code mounted read-only
- **SELinux support**: Volume labeling for RHEL
- **Credential management**: Build-time only, automatic cleanup

## Development Tools

### Code Quality
- **pre-commit**: Git hook management
- **black**: Python code formatting
- **isort**: Import organization
- **flake8**: Style enforcement in development

### Build Tools
- **setuptools**: Python package building
- **wheel**: Binary package distribution
- **Docker/Podman**: Container image building
- **Make**: Build automation and task running

### Version Control Integration
- **Git**: Source control
- **GitHub**: Repository hosting
- **GitHub Actions**: CI/CD pipelines
- **Dependabot**: Automated dependency updates

## Infrastructure

### CI/CD Platforms
- **GitHub Actions**: Primary CI/CD platform
- **GitLab CI**: Alternative CI/CD support
- **Jenkins**: Enterprise CI/CD integration
- **Tekton/OpenShift Pipelines**: RHEL/OpenShift environments

### Documentation
- **MkDocs**: Documentation site generation
- **Markdown**: Documentation format
- **Diataxis**: Documentation framework structure
- **GitHub Pages**: Documentation hosting

### Monitoring & Logging
- **Python logging**: Built-in logging framework
- **JSON logging**: Structured log output
- **Container logs**: Docker/Podman log integration
- **Health checks**: Container readiness/liveness probes

## Dependencies

### Core Python Dependencies
```python
# Core functionality
aider-chat>=0.50.0
pyyaml>=6.0
click>=8.0

# Linting tools
flake8>=6.0.0
pylint>=2.17.0
mypy>=1.5.0
bandit>=1.7.0
```

### JavaScript Dependencies
```json
{
  "eslint": "^8.0.0",
  "prettier": "^3.0.0",
  "jshint": "^2.13.0",
  "@typescript-eslint/parser": "^6.0.0",
  "@typescript-eslint/eslint-plugin": "^6.0.0"
}
```

### Development Dependencies
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **pre-commit**: Git hooks
- **black**: Code formatting
- **mypy**: Type checking

## Platform Support

### Operating Systems
- **macOS**: Development and production support
- **Ubuntu 20.04+**: Development and production support
- **RHEL 9**: Enterprise production support
- **RHEL 10**: Next-generation enterprise support

### Python Versions
- **Python 3.11+**: Default/recommended version
- **Python 3.9**: RHEL 9 compatibility
- **Python 3.12**: RHEL 10 and latest features

### Container Orchestration
- **Docker Compose**: Local development orchestration
- **Kubernetes**: Production container orchestration
- **OpenShift**: RHEL/enterprise container platform
- **Podman Compose**: RHEL-native orchestration

## Security Tools

### Development Security
- **bandit**: Python security vulnerability scanning
- **safety**: Python dependency vulnerability checking
- **npm audit**: JavaScript dependency security
- **pre-commit hooks**: Security checks in development

### Production Security
- **Container scanning**: Trivy, Grype integration
- **Credential management**: Environment variables, build args
- **Network security**: TLS/SSL for API communications
- **Access control**: RBAC for container registries

## AI Integration

### AI Frameworks
- **aider-chat**: Primary AI integration for code fixes
- **OpenAI API**: LLM access through aider.chat
- **Anthropic Claude**: Alternative LLM support
- **Local models**: Support for self-hosted AI models

### AI Optimization
- **Token optimization**: Efficient prompt engineering
- **Context management**: Relevant code context for AI
- **Caching**: AI response caching for performance
- **Rate limiting**: API usage management

## Development Environment

### Recommended IDE
- **VS Code**: Primary development environment with Python extension
- **PyCharm**: Professional Python IDE alternative
- **Vim/Neovim**: Terminal-based development with LSP
- **Sublime Text**: Lightweight alternative with Python support

### Local Development
- **Virtual environments**: venv/virtualenv for isolation
- **Hot reloading**: Development server with auto-restart
- **Debugging**: pdb, VS Code debugger, PyCharm debugger
- **Testing**: pytest with coverage reporting

## Upgrade Path

### Version Management
- **Dependabot**: Automated dependency updates
- **Version pinning**: Controlled upgrade cycles
- **Security monitoring**: CVE tracking and patching
- **Compatibility testing**: Multi-version test matrix

### Future Technologies
- **Python 3.13+**: Future Python version support
- **Container evolution**: OCI standards, new runtimes
- **AI advancement**: Next-generation AI model integration
- **Cloud native**: Kubernetes operators, service mesh integration
