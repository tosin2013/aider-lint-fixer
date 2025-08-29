# Container Architecture Strategy

This document explains the architectural decisions behind aider-lint-fixer's container strategy, covering the rationale for the dual-approach design and its implementation details.

## Strategic Overview

aider-lint-fixer implements a **dual container strategy** that optimizes for different use cases:

1. **Default Container**: General development with latest tools
2. **RHEL Containers**: Enterprise-specific customer builds

This approach follows methodological pragmatism principles by optimizing for the common case while maintaining comprehensive enterprise support.

## Architecture Decisions

### Default Container Design

**Target Platforms**: macOS and Ubuntu development environments

**Key Characteristics**:
- Uses latest ansible-lint and ansible-core versions
- No subscription or licensing constraints
- Simple, single-stage Docker build
- Optimized for developer experience

**Technical Stack**:
```dockerfile
FROM python:3.11-slim
# Latest versions of all tools
RUN pip install ansible-lint ansible-core ansible
RUN pip install flake8 pylint mypy
RUN npm install -g eslint jshint prettier
```

### RHEL Container Design

**Target Platforms**: RHEL 9 and RHEL 10 enterprise environments

**Key Characteristics**:
- Version-specific ansible-core tied to RHEL lifecycle
- Customer-build approach due to subscription requirements
- Separate containers for RHEL 9 and RHEL 10
- Enterprise security and compliance features

**Technical Stack**:
```dockerfile
# RHEL 9
FROM registry.redhat.io/ubi9/ubi:latest
# ansible-core 2.14.x (frozen for RHEL 9 lifecycle)

# RHEL 10  
FROM registry.redhat.io/ubi10/ubi:latest
# ansible-core 2.16+ (modern features)
```

## Design Rationale

### Why Not a Unified Container?

**Version Incompatibilities**:
- RHEL 9: ansible-core 2.14 (frozen until May 2032)
- RHEL 10: ansible-core 2.16+ (2-major-version jump)
- ansible-lint supports only last 2 major versions

**Licensing Constraints**:
- UBI images don't include ansible-core by default
- Requires RHEL subscription for AppStream access
- Cannot distribute pre-built containers with ansible-core

**Performance Optimization**:
- UBI 10: 16% smaller images, modern kernel
- Python version differences: 3.9 vs 3.12
- Post-Quantum Cryptography in RHEL 10

### Benefits of Dual Strategy

**Developer Experience**:
- Simple default container for 90% of use cases
- Latest tools and features without complexity
- No subscription management for general development

**Enterprise Support**:
- Version-specific optimization for RHEL environments
- Customer control over container supply chain
- Licensing compliance through customer subscriptions

## Implementation Architecture

### Container Hierarchy

```
aider-lint-fixer containers
├── Dockerfile (default)
│   ├── Target: macOS/Ubuntu
│   ├── Base: python:3.11-slim
│   └── Tools: latest versions
├── Dockerfile.rhel9
│   ├── Target: RHEL 9 enterprise
│   ├── Base: registry.redhat.io/ubi9/ubi
│   └── Tools: ansible-core 2.14.x
└── Dockerfile.rhel10
    ├── Target: RHEL 10 enterprise
    ├── Base: registry.redhat.io/ubi10/ubi
    └── Tools: ansible-core 2.16+
```

### Build Automation

**Default Container**:
```bash
# Simple build process
docker build -t aider-lint-fixer:latest .
```

**RHEL Containers**:
```bash
# Automated build scripts (use Podman by default)
./scripts/containers/build-rhel9.sh
./scripts/containers/build-rhel10.sh
```

### Security Architecture

**Non-Root Execution**:
```dockerfile
RUN useradd -m -u 1001 aider
USER 1001
```

**Credential Management**:
- Subscription credentials via build args
- Automatic unregistration after build
- No credentials stored in final image

**Volume Security**:
```dockerfile
VOLUME ["/workspace"]
# Read-only mounts for project code
```

## Version Management Strategy

### ansible-core Version Matrix

| Platform | ansible-core | Python | Lifecycle |
|----------|-------------|---------|-----------|
| Default | Latest | 3.11+ | Rolling |
| RHEL 9 | 2.14.x | 3.9 | Until May 2032 |
| RHEL 10 | 2.16+ | 3.12 | Active development |

### Compatibility Considerations

**ansible-lint Rules**:
- Latest container: Newest rules and features
- RHEL 9: Compatible with ansible-core 2.14
- RHEL 10: Modern rules with ansible-core 2.16+

**Python Ecosystem**:
- Default: Latest Python linter versions
- RHEL: System-compatible versions

## Deployment Patterns

### Development Workflow

```bash
# Local development (default container)
docker build -t aider-lint-fixer:latest .
docker run --rm -v $(pwd):/workspace:ro aider-lint-fixer:latest

# RHEL testing (customer build)
./scripts/containers/build-rhel9.sh --validate
```

### CI/CD Integration

**Multi-Platform Testing**:
```yaml
strategy:
  matrix:
    container: [default, rhel9, rhel10]
```

**Environment-Specific Builds**:
- Default container for general CI/CD
- RHEL containers for enterprise validation

## Future Considerations

### Scalability

**Additional Platforms**:
- Framework supports additional enterprise platforms
- Plugin architecture enables platform-specific optimizations

**Version Evolution**:
- RHEL 11 support through additional Dockerfile
- Automated version detection and container selection

### Maintenance Strategy

**Default Container**:
- Regular updates with latest tool versions
- Automated dependency updates via Dependabot

**RHEL Containers**:
- Version-specific maintenance aligned with RHEL lifecycle
- Customer responsibility for builds and updates

## Related Documentation

- [ADR 0008: Deployment Environments](../adrs/0008-deployment-environments.md)
- [ADR 0009: RHEL Container Build Requirements](../adrs/0009-rhel-container-build-requirements.md)
- [Container Deployment Tutorial](../tutorials/container-deployment.md)
- [Production Deployment Guide](../how-to/deploy-to-production.md)
