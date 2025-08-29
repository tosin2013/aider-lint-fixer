# Architectural Decision Records (ADRs)

This directory contains Architectural Decision Records for the aider-lint-fixer project.

## What are ADRs?

Architectural Decision Records (ADRs) are documents that capture important architectural decisions made along with their context and consequences. They help teams understand why certain decisions were made and provide historical context for future changes.

## ADR Format

We use the [MADR (Markdown Architectural Decision Records)](https://adr.github.io/madr/) format for consistency and readability.

## ADR Lifecycle

- **Proposed**: The ADR is proposed and under discussion
- **Accepted**: The ADR has been accepted and should be implemented
- **Deprecated**: The ADR is no longer relevant but kept for historical context
- **Superseded**: The ADR has been replaced by a newer ADR

## Current ADRs

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-record-architecture-decisions.md) | Record Architecture Decisions | Accepted |
| [0002](0002-ai-integration-architecture.md) | AI Integration Architecture | Accepted |
| [0003](0003-modular-plugin-system.md) | Modular Plugin System | Accepted |
| [0004](0004-hybrid-python-javascript-architecture.md) | Hybrid Python-JavaScript Architecture | Accepted |
| [0005](0005-python-linter-ecosystem.md) | Python Linter Ecosystem Support | Accepted |
| [0006](0006-javascript-typescript-linter-ecosystem.md) | JavaScript/TypeScript Linter Ecosystem Support | Accepted |
| [0007](0007-infrastructure-devops-linter-ecosystem.md) | Infrastructure/DevOps Linter Ecosystem Support | Accepted |
| [0008](0008-deployment-environments.md) | Deployment Environments and Runtime Requirements | Accepted |
| [0009](0009-rhel-container-build-requirements.md) | RHEL Container Build Requirements and Subscription Management | Accepted |

## Creating New ADRs

1. Copy the `template.md` file
2. Rename it with the next sequential number: `NNNN-title-in-kebab-case.md`
3. Fill in the template with your decision details
4. Update this README with the new ADR entry
5. Submit for review through the normal PR process

## Guidelines

- Keep ADRs concise but complete
- Include context, decision, and consequences
- Consider alternatives and trade-offs
- Update status as decisions evolve
- Reference related ADRs when relevant
