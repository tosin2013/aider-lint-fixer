---
title: Architecture Overview
---

# Architecture Overview

This document explains the architectural concepts and design philosophy behind aider-lint-fixer, a Python-based linting tool that integrates with aider.chat for AI-powered code analysis and fixing.

## Introduction

aider-lint-fixer implements a **hybrid Python-JavaScript architecture** with **modular plugin system** that enables comprehensive multi-language linting while maintaining AI integration capabilities. The architecture follows methodological pragmatism principles, optimizing for practical outcomes while maintaining systematic verification processes.

## Core Concepts

### AI-Integrated Linting Pipeline

The core concept revolves around a **three-stage pipeline**:

1. **Detection**: Multi-language linters identify code issues
2. **Analysis**: AI-powered error classification and context analysis  
3. **Resolution**: Automated fixes through aider.chat integration

This approach combines deterministic linting tools with AI reasoning for enhanced fix success rates.

### Modular Plugin Architecture

Each linter is implemented as an independent plugin inheriting from a base class:

```python
class BaseLinter(ABC):
    @abstractmethod
    def run_linter(self, file_path: str) -> Dict[str, Any]
    
    @abstractmethod
    def parse_output(self, output: str) -> List[Dict[str, Any]]
```

This enables:
- **Independent Evolution**: Each linter can be updated independently
- **Consistent Interface**: Uniform API across all linting tools
- **Easy Extension**: New linters can be added without core changes

### Dual Runtime Support

The architecture supports both Python and JavaScript ecosystems:

- **Python Runtime**: Core application, Python linters (flake8, pylint, mypy)
- **Node.js Runtime**: JavaScript linters (ESLint, Prettier, JSHint)
- **Orchestration Layer**: Python-based coordination between runtimes

## Design Decisions

### Why Hybrid Python-JavaScript?

**Primary Rationale**: Modern development requires multi-language support

**Benefits**:
- **Comprehensive Coverage**: Support for both Python and JavaScript/TypeScript projects
- **Native Tool Integration**: Use each ecosystem's best-in-class linters
- **Performance Optimization**: Leverage native runtime performance

**Trade-offs**:
- **Complexity**: Managing two runtime environments
- **Dependencies**: Requires both Python and Node.js installations
- **Coordination Overhead**: Inter-runtime communication complexity

### AI Integration Strategy

**Approach**: Wrapper layer around aider.chat rather than direct LLM integration

**Rationale**:
- **Proven Toolchain**: Leverage aider.chat's established AI capabilities
- **Maintenance Reduction**: Avoid reimplementing LLM interaction patterns
- **Feature Inheritance**: Benefit from aider.chat's ongoing improvements

**Implementation**:
```python
class AiderIntegration:
    def analyze_and_fix(self, errors: List[LintError]) -> FixResult:
        # Coordinate with aider.chat for AI-powered fixes
```

## Comparison with Alternatives

| Approach | Pros | Cons | Fix Success Rate |
|----------|------|------|------------------|
| **Our Hybrid Approach** | Multi-language, AI-enhanced, modular | Runtime complexity | 85-95% |
| **Python-Only** | Simple, single runtime | Limited language support | 60-80% |
| **Direct LLM Integration** | Custom AI logic | High maintenance, API costs | 70-85% |
| **Traditional Linting** | Fast, deterministic | No AI assistance | 40-60% |

## Architectural Layers

### Application Layer
- **CLI Interface**: Command-line tool for direct usage
- **API Interface**: Programmatic access for integrations
- **Configuration Management**: Unified and language-specific configs

### Orchestration Layer
- **Linter Coordination**: Manages multi-linter execution
- **Error Aggregation**: Consolidates results across tools
- **AI Integration**: Coordinates with aider.chat for fixes

### Plugin Layer
- **Python Linters**: flake8, pylint, mypy, bandit, black, isort
- **JavaScript Linters**: ESLint, JSHint, Prettier
- **Infrastructure Linters**: ansible-lint (with version management)

### Runtime Layer
- **Python Environment**: Core application runtime
- **Node.js Environment**: JavaScript linter execution
- **Container Environment**: Isolated execution contexts

## Deployment Architecture

### Multi-Environment Strategy

The architecture supports diverse deployment scenarios:

- **Local Development**: Direct Python/Node.js installation
- **Containerized**: Docker containers for isolated environments
- **Enterprise RHEL**: Customer-build containers with subscription management
- **CI/CD Integration**: Pipeline-optimized execution

### Container Strategy

**Dual Container Approach**:
- **Default Container**: Latest tools for general development (macOS/Ubuntu)
- **RHEL Containers**: Version-specific builds for enterprise compliance

This separation optimizes for both developer experience and enterprise requirements.

## Further Reading

- [Container Architecture](./container-architecture.md) - Detailed container strategy
- [Design Decisions](./design-decisions.md) - Specific architectural choices
- [Technology Stack](./technology-stack.md) - Complete technology overview
- [ADR 0004: Hybrid Python-JavaScript Architecture](../adrs/0004-hybrid-python-javascript-architecture.md)
- [ADR 0003: Modular Plugin System](../adrs/0003-modular-plugin-system.md)