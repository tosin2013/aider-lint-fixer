# Aider Lint Fixer Documentation

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Automated lint error detection and fixing powered by aider.chat and AI**

Welcome to the comprehensive documentation for Aider Lint Fixer - an intelligent tool that automatically detects lint errors in your codebase and fixes them using AI-powered code generation through [aider.chat](https://aider.chat).

## 🚀 Quick Start

New to Aider Lint Fixer? Start here:

```bash
# Install
pip install aider-lint-fixer

# Basic usage
aider-lint-fixer ./src

# With specific linters
aider-lint-fixer --linters flake8,eslint ./src
```

## 📚 Learning-Oriented: Tutorials

Perfect for beginners - step-by-step guides to get you started:

- **[Getting Started](tutorials/getting-started.md)** - Your first lint fixing session
- **[Getting Started with Containers](tutorials/getting-started-with-containers.md)** - Docker and container usage  
- **[Setting Up Your Development Environment](tutorials/setting-up-your-development-environment.md)** - Complete development setup
- **[Writing and Running Tests](tutorials/writing-and-running-tests.md)** - Testing your lint fixes
- **[Container Deployment](tutorials/container-deployment.md)** - Production deployment guide

## 🔧 Task-Oriented: How-To Guides

Practical solutions for specific tasks:

### Configuration & Setup
- **[Configure Linters](how-to/configure-linters.md)** - Set up and customize linters
- **[Setup Development Environment](how-to/setup-development-environment.md)** - Development environment setup
- **[Integrate with Aider](how-to/integrate-with-aider.md)** - Advanced aider.chat integration

### Development & Debugging  
- **[Add a New Feature](how-to/how-to-add-a-new-feature.md)** - Extend functionality
- **[Debug Common Issues](how-to/how-to-debug-common-issues.md)** - Troubleshooting guide
- **[Run Tests](how-to/run-tests.md)** - Testing strategies

### Deployment & Operations
- **[Deploy to Production](how-to/deploy-to-production.md)** - Production deployment
- **[Deploy Your Application](how-to/how-to-deploy-your-application.md)** - Application deployment
- **[Monitor Performance](how-to/monitor-performance.md)** - Performance monitoring
- **[Security Best Practices](how-to/security-best-practices.md)** - Security guidelines

## 📖 Information-Oriented: Reference

Detailed technical reference documentation:

### API & Configuration
- **[API Documentation](reference/api-documentation.md)** - Complete API reference
- **[API Reference](reference/api-reference.md)** - API usage examples
- **[Configuration Reference](reference/configuration-reference.md)** - Comprehensive configuration guide
- **[Command Line Interface](reference/command-line-interface.md)** - CLI reference

### Linters & Errors
- **[Linter Plugins](reference/linter-plugins.md)** - Supported linters and plugins
- **[Error Codes](reference/error-codes.md)** - Error codes and troubleshooting
- **[FAQ](reference/faq.md)** - Frequently asked questions

## 💡 Understanding-Oriented: Explanation

Deep dives into concepts, architecture, and design decisions:

### Architecture & Design
- **[Architecture Overview](explanation/architecture-overview.md)** - System architecture
- **[Container Architecture](explanation/container-architecture.md)** - Container design
- **[Design Decisions](explanation/design-decisions.md)** - Why we made certain choices
- **[Technology Stack](explanation/technology-stack.md)** - Technologies used

## 🏗️ Architecture Decision Records (ADRs)

Historical decisions and their rationale:

- **[Record Architecture Decisions](adrs/0001-record-architecture-decisions.md)**
- **[AI Integration Architecture](adrs/0002-ai-integration-architecture.md)**
- **[Modular Plugin System](adrs/0003-modular-plugin-system.md)**
- **[Python Ecosystem Focus](adrs/0004-python-ecosystem-focus.md)**
- **[Python Linter Ecosystem](adrs/0005-python-linter-ecosystem.md)**
- **[JavaScript TypeScript Ecosystem](adrs/0006-javascript-typescript-ecosystem.md)**
- **[Infrastructure DevOps Linter Ecosystem](adrs/0007-infrastructure-devops-linter-ecosystem.md)**
- **[Deployment Environments](adrs/0008-deployment-environments.md)** 
- **[RHEL Container Build Requirements](adrs/0009-rhel-container-build-requirements.md)**

## 🎯 Key Features

### 🧠 AI-Powered Intelligence
- **Native Lint Detection**: Automatically discovers project lint configurations
- **Pre-Lint Risk Assessment**: Analyzes codebase health before fixing
- **Intelligent Force Mode**: ML-powered with confidence-based auto-forcing
- **Cost Monitoring**: Real-time LLM API cost tracking and budget controls

### 📊 Supported Linters

| Language | Linters | Profile Support |
|----------|---------|-----------------|
| **Python** | flake8, pylint, black, isort, mypy | ✅ Basic, Default, Strict |
| **JavaScript/TypeScript** | ESLint, JSHint, Prettier | ✅ Basic, Default, Strict |
| **Ansible** | ansible-lint | ✅ Basic, Production |
| **Go** | golint, gofmt, go vet | ✅ Basic, Default, Strict |
| **Rust** | rustfmt, clippy | ✅ Basic, Default, Strict |

### 🚀 Enterprise Features
- **Docker Support**: Production-ready containerization
- **Multi-Architecture**: ARM64 and x86_64 support
- **Session Recovery**: Resume interrupted operations
- **Progress Tracking**: Visual progress and metrics
- **Community Learning**: Improve classifications over time

## 🆘 Getting Help

- **Issues**: [GitHub Issues](https://github.com/tosin2013/aider-lint-fixer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tosin2013/aider-lint-fixer/discussions)
- **Documentation**: You're reading it! 📖

## 🤝 Contributing

We welcome contributions! Check out our contributor guides:

- **[Contributor Version Guide](CONTRIBUTOR_VERSION_GUIDE.md)** - Version-specific contribution info
- **[Installation Guide](INSTALLATION_GUIDE.md)** - Development setup
- **[Linter Testing Guide](LINTER_TESTING_GUIDE.md)** - Testing linter integrations
- **[Node.js Linters Guide](NODEJS_LINTERS_GUIDE.md)** - JavaScript/TypeScript development

---

*This documentation is organized using the [Diataxis framework](https://diataxis.fr/) for maximum clarity and usability.*
