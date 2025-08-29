# Container Deployment Guide

This tutorial walks you through deploying aider-lint-fixer using containers, covering both the default container for general development and RHEL-specific customer builds.

## Overview

aider-lint-fixer provides two container strategies:

- **Default Container**: Optimized for macOS and Ubuntu with latest ansible-lint
- **RHEL Containers**: Customer-build approach for RHEL 9 and RHEL 10 environments

## Default Container (macOS/Ubuntu)

### Quick Start

```bash
# Build the default container
docker build -t aider-lint-fixer:latest .

# Run on your project
docker run --rm -v $(pwd):/workspace:ro \
  aider-lint-fixer:latest \
  --linters flake8,ansible-lint --dry-run
```

### What's Included

The default container includes:
- Latest ansible-lint with newest rules and features
- Python linters: flake8, pylint, mypy
- JavaScript linters: ESLint, JSHint, Prettier
- No subscription requirements or licensing constraints

### Container Features

- **Non-root execution**: Runs as user ID 1001 for security
- **Volume mounting**: Mount your project at `/workspace`
- **Environment variables**: Configurable via environment
- **Health checks**: Built-in container health monitoring

## RHEL Container Strategy

### Why Customer-Build?

RHEL containers require customer builds due to:
- Red Hat subscription requirements for ansible-core
- Version-specific ansible-core tied to RHEL lifecycle
- Licensing constraints preventing pre-built distribution

### RHEL 9 Container

**Note**: Build scripts use **Podman** by default (RHEL's native container tool).

```bash
# Use automated build script (uses Podman automatically)
./scripts/containers/build-rhel9.sh

# Or build manually with Podman (recommended)
podman build \
  --build-arg RHEL_USERNAME=your-username \
  --build-arg RHEL_PASSWORD=your-password \
  -f Dockerfile.rhel9 \
  -t my-company/aider-lint-fixer:rhel9 .

# Or build manually with Docker (fallback)
docker build \
  --build-arg RHEL_USERNAME=your-username \
  --build-arg RHEL_PASSWORD=your-password \
  -f Dockerfile.rhel9 \
  -t my-company/aider-lint-fixer:rhel9 .
```

**RHEL 9 Specifications:**
- ansible-core 2.14 (frozen for RHEL 9 lifecycle until May 2032)
- Python 3.9 system dependency
- UBI 9 base image

### RHEL 10 Container

```bash
# Use automated build script with security scanning (uses Podman automatically)
./scripts/containers/build-rhel10.sh --validate --security-scan

# Or build manually with Podman (recommended)
podman build \
  --build-arg RHEL_USERNAME=your-username \
  --build-arg RHEL_PASSWORD=your-password \
  -f Dockerfile.rhel10 \
  -t my-company/aider-lint-fixer:rhel10 .

# Or build manually with Docker (fallback)
docker build \
  --build-arg RHEL_USERNAME=your-username \
  --build-arg RHEL_PASSWORD=your-password \
  -f Dockerfile.rhel10 \
  -t my-company/aider-lint-fixer:rhel10 .
```

**RHEL 10 Specifications:**
- ansible-core 2.16+ (modern version with latest features)
- Python 3.12 system dependency
- UBI 10 base image (16% smaller than UBI 9)
- Post-Quantum Cryptography support

## Build Script Features

### RHEL 9 Build Script

```bash
# Interactive build (prompts for credentials)
./scripts/containers/build-rhel9.sh

# Build with specific configuration
./scripts/containers/build-rhel9.sh \
  --name my-company/aider-lint-fixer \
  --tag v1.0-rhel9 \
  --registry quay.io \
  --validate

# Dry run to see build command
./scripts/containers/build-rhel9.sh --dry-run
```

### RHEL 10 Build Script

```bash
# Build with security scanning
./scripts/containers/build-rhel10.sh \
  --name my-company/aider-lint-fixer \
  --tag v2.0-rhel10 \
  --validate \
  --security-scan
```

### Script Features

- **Interactive credential prompting** for secure RHEL subscription handling
- **Validation and testing** capabilities with built-in health checks
- **Security scanning integration** (Trivy/Grype support)
- **Dry-run capabilities** for testing build commands
- **Registry integration** support for enterprise container registries

## Security Best Practices

### Credential Management

```bash
# Use environment variables
export RHEL_USERNAME=your-username
export RHEL_PASSWORD=your-password
./scripts/containers/build-rhel9.sh

# Or use build args file
echo "RHEL_USERNAME=your-username" > .build-args.rhel9
echo "RHEL_PASSWORD=your-password" >> .build-args.rhel9
./scripts/containers/build-rhel9.sh --file .build-args.rhel9
```

### Container Security

- All containers run as non-root user (UID 1001)
- Subscription credentials are not stored in final image
- Health checks validate container functionality
- Read-only volume mounts for project code

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Container Build and Test

on: [push, pull_request]

jobs:
  test-default-container:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Default Container
        run: docker build -t aider-lint-fixer:test .
      - name: Test Container
        run: |
          docker run --rm -v $(pwd):/workspace:ro \
            aider-lint-fixer:test --version

  test-rhel-container:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Build RHEL Container
        env:
          RHEL_USERNAME: ${{ secrets.RHEL_USERNAME }}
          RHEL_PASSWORD: ${{ secrets.RHEL_PASSWORD }}
        run: ./scripts/containers/build-rhel9.sh --validate
```

## Troubleshooting

### Common Issues

**Default Container Build Fails**
```bash
# Check Docker daemon
docker info

# Clean build cache
docker system prune -f
docker build --no-cache -t aider-lint-fixer:latest .
```

**RHEL Subscription Issues**
```bash
# Verify credentials
subscription-manager status

# Check repository access
dnf repolist
```

**Container Runtime Issues**
```bash
# Check container logs
docker logs <container-id>

# Debug container interactively
{{ ... }}
docker run -it --entrypoint /bin/bash aider-lint-fixer:latest
```

## Next Steps

- [Container Architecture](../explanation/container-architecture.md)
- [Configure Linters](../how-to/configure-linters.md)
- [Production Deployment](../how-to/deploy-to-production.md)
