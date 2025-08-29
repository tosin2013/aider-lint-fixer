# Hybrid Python-JavaScript Architecture

* Status: accepted
* Deciders: Development Team
* Date: 2025-08-24

Technical Story: Establish hybrid Python-JavaScript architecture for aider-lint-fixer to support comprehensive multi-language linting capabilities.

## Context and Problem Statement

The aider-lint-fixer project supports multiple programming languages and their respective linting tools. While the core AI integration and orchestration is Python-based, comprehensive JavaScript/TypeScript linting support requires deep integration with Node.js ecosystem tools like ESLint, Prettier, and JSHint.

## Decision Drivers

* Multi-language linting support requirements
* Integration with existing JavaScript/TypeScript toolchains
* Leveraging best-in-class linters for each ecosystem
* Maintaining consistent Python-based AI integration
* Supporting diverse development environments

## Considered Options

* Pure Python implementation with subprocess calls
* Hybrid Python-JavaScript architecture
* Separate Python and Node.js tools
* Language-agnostic approach with multiple runtimes

## Decision Outcome

Chosen option: "Hybrid Python-JavaScript architecture", because it provides the best balance of Python-based AI capabilities with native JavaScript ecosystem integration for optimal linting results.

### Positive Consequences

* Native JavaScript/TypeScript linting with ESLint, Prettier, JSHint
* Python-based AI integration and orchestration
* Best-in-class tools for each language ecosystem
* Comprehensive multi-language project support
* Flexible architecture supporting diverse development workflows

### Negative Consequences

* Increased complexity with dual runtime requirements
* Dependency management across Python and Node.js ecosystems
* Potential version compatibility issues between ecosystems
* Higher setup complexity for development environments

## Architecture Components

### Python Core (Orchestration Layer)
- **Python Version**: 3.11+ (as defined in pyproject.toml)
- **Package Management**: pip with pyproject.toml
- **AI Integration**: aider-chat library for LLM communication
- **Core Classes**: AiderIntegration, ErrorAnalyzer, SmartErrorClassifier
- **Plugin System**: Base linter classes with inheritance
- **Configuration**: ConfigManager with YAML support

### JavaScript/Node.js Integration (Linting Layer)
- **ESLint**: Full integration with v8.x/9.x support
- **TypeScript**: Native support via @typescript-eslint
- **Prettier**: Code formatting integration
- **JSHint**: Legacy JavaScript project support
- **Configuration Detection**: Automatic .eslintrc.*, package.json detection
- **Execution**: npx/npm script integration with JSON output parsing

### Supported Linters by Ecosystem

#### Python Ecosystem
- **flake8**: Style and error checking
- **pylint**: Comprehensive code analysis
- **mypy**: Static type checking

#### JavaScript/TypeScript Ecosystem  
- **ESLint**: Primary linting with extensive rule support
- **Prettier**: Code formatting (integrated with ESLint)
- **JSHint**: Legacy project support

#### Infrastructure/DevOps
- **ansible-lint**: Ansible playbook and role validation

## Implementation Guidelines

### Dependency Management
- Primary dependencies in pyproject.toml
- Optional dependencies grouped by functionality (dev, linters, learning)
- Pin major versions for stability
- Regular dependency audits for security

### Code Organization
- **Main Package**: `aider_lint_fixer/` (Python orchestration)
- **Plugin System**: `aider_lint_fixer/linters/` with language-specific implementations
- **Configuration**: YAML format with per-linter sections
- **Tests**: Mirror source structure with integration tests for both ecosystems

### Integration Patterns
- **ESLint Integration**: Native npx/npm execution with JSON output parsing
- **Configuration Detection**: Automatic discovery of .eslintrc.*, tsconfig.json, package.json
- **TypeScript Support**: Dynamic extension detection based on project setup
- **Error Classification**: Language-aware error analysis and fix suggestions

## Pros and Cons of the Options

### Pure Python implementation with subprocess calls

* Good, because single runtime environment
* Good, because consistent Python development practices
* Good, because simplified deployment
* Bad, because limited JavaScript ecosystem integration
* Bad, because subprocess overhead and complexity
* Bad, because difficult configuration detection for JS tools

### Hybrid Python-JavaScript architecture

* Good, because native JavaScript/TypeScript tooling integration
* Good, because best-in-class linters for each ecosystem
* Good, because comprehensive multi-language support
* Good, because leverages existing developer toolchains
* Bad, because dual runtime complexity
* Bad, because increased setup requirements
* Bad, because cross-ecosystem dependency management

### Separate Python and Node.js tools

* Good, because clear separation of concerns
* Good, because independent versioning and deployment
* Bad, because fragmented user experience
* Bad, because duplicate configuration and setup
* Bad, because no shared AI integration benefits

### Language-agnostic approach with multiple runtimes

* Good, because maximum flexibility for future languages
* Good, because pluggable architecture
* Bad, because excessive complexity for current requirements
* Bad, because maintenance burden across multiple ecosystems
* Bad, because unclear technology focus

## Migration Actions

### Documentation Updates
- ✅ Ecosystem analysis corrected to reflect Python focus
- ✅ ADRs document Python-first architecture
- 🔄 Update any remaining Node.js references in documentation
- 🔄 Ensure all code examples use Python syntax

### Development Process
- ✅ pyproject.toml defines complete Python toolchain
- ✅ GitHub Actions workflows support Python testing
- 🔄 Validate all development scripts use Python
- 🔄 Ensure container images are Python-based

## Links

* [ADR-0002](0002-ai-integration-architecture.md) - AI integration using Python aider-chat library
* [ADR-0003](0003-modular-plugin-system.md) - Python-based plugin architecture
* Project Configuration - Complete Python project configuration in pyproject.toml
