# RHEL Container Builds

This guide provides step-by-step instructions for building aider-lint-fixer containers for RHEL 9 and RHEL 10 environments using your Red Hat subscription.

## Prerequisites

- Active Red Hat subscription
- **Podman** (recommended) or Docker installed
- Network access to Red Hat repositories
- RHEL subscription credentials

## Quick Start

**Note**: These scripts use **Podman** by default (RHEL's native container tool). Docker is supported as fallback.

### RHEL 9 Container

```bash
# Interactive build (prompts for credentials)
./scripts/containers/build-rhel9.sh

# Build with validation
./scripts/containers/build-rhel9.sh --validate
```

### RHEL 10 Container

```bash
# Interactive build with security scanning
./scripts/containers/build-rhel10.sh --validate --security-scan

# Build for enterprise registry
./scripts/containers/build-rhel10.sh \
  --registry quay.io \
  --name my-company/aider-lint-fixer \
  --tag v2.0-rhel10
```

## Build Script Options

### Common Options

| Option | Description | Example |
|--------|-------------|---------|
| `--name` | Container image name | `--name my-company/aider-lint-fixer` |
| `--tag` | Container image tag | `--tag v1.0-rhel9` |
| `--registry` | Container registry URL | `--registry quay.io` |
| `--validate` | Validate built image | `--validate` |
| `--dry-run` | Show build command without executing | `--dry-run` |

### RHEL 9 Specific Options

```bash
./scripts/containers/build-rhel9.sh --help

Options:
  -n, --name NAME         Container image name
  -t, --tag TAG          Container image tag (default: rhel9)
  -r, --registry URL     Container registry URL
  -u, --username USER    RHEL subscription username
  -p, --password PASS    RHEL subscription password
  -f, --file FILE        Build args file
  --no-cache             Build without using cache
  --dry-run              Show build command without executing
  --validate             Validate built image functionality
```

### RHEL 10 Specific Options

```bash
./scripts/containers/build-rhel10.sh --help

Additional RHEL 10 options:
  --security-scan        Run security scan on built image
```

## Credential Management

### Environment Variables

```bash
export RHEL_USERNAME=your-username
export RHEL_PASSWORD=your-password
./scripts/containers/build-rhel9.sh
```

### Build Args File

```bash
# Create secure credential file
echo "RHEL_USERNAME=your-username" > .build-args.rhel9
echo "RHEL_PASSWORD=your-password" >> .build-args.rhel9
chmod 600 .build-args.rhel9

# Use credential file
./scripts/containers/build-rhel9.sh --file .build-args.rhel9
```

### Interactive Prompting

```bash
# Script will prompt for credentials
./scripts/containers/build-rhel9.sh
# Enter RHEL subscription username: your-username
# Enter RHEL subscription password: [hidden]
```

## Manual Build Process

### RHEL 9 Manual Build

```bash
# Using Podman (recommended)
podman build \
  --build-arg RHEL_USERNAME=your-username \
  --build-arg RHEL_PASSWORD=your-password \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  -f Dockerfile.rhel9 \
  -t my-company/aider-lint-fixer:rhel9 .

# Using Docker (fallback)
docker build \
  --build-arg RHEL_USERNAME=your-username \
  --build-arg RHEL_PASSWORD=your-password \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  -f Dockerfile.rhel9 \
  -t my-company/aider-lint-fixer:rhel9 .
```

### RHEL 10 Manual Build

```bash
# Using Podman (recommended)
podman build \
  --build-arg RHEL_USERNAME=your-username \
  --build-arg RHEL_PASSWORD=your-password \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  --label org.opencontainers.image.title=aider-lint-fixer \
  --label org.opencontainers.image.description="AI-powered lint fixer for RHEL 10" \
  -f Dockerfile.rhel10 \
  -t my-company/aider-lint-fixer:rhel10 .

# Using Docker (fallback)
docker build \
  --build-arg RHEL_USERNAME=your-username \
  --build-arg RHEL_PASSWORD=your-password \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  --label org.opencontainers.image.title=aider-lint-fixer \
  --label org.opencontainers.image.description="AI-powered lint fixer for RHEL 10" \
  -f Dockerfile.rhel10 \
  -t my-company/aider-lint-fixer:rhel10 .
```

## Validation and Testing

### Built-in Validation

```bash
# RHEL 9 validation
./scripts/containers/build-rhel9.sh --validate

# RHEL 10 validation with security scan
./scripts/containers/build-rhel10.sh --validate --security-scan
```

### Manual Testing

```bash
# Test basic functionality (using Podman)
podman run --rm my-company/aider-lint-fixer:rhel9 --version

# Test ansible-core version
podman run --rm my-company/aider-lint-fixer:rhel9 \
  sh -c "python3 -c 'import ansible; print(ansible.__version__)'"

# Test user permissions
podman run --rm my-company/aider-lint-fixer:rhel9 id

# Using Docker (fallback)
docker run --rm my-company/aider-lint-fixer:rhel9 --version
```

### Expected Validation Results

**RHEL 9 Container**:
- ansible-core version: 2.14.x
- Python version: 3.9.x
- User ID: 1001 (non-root)
- RHEL version: Red Hat Enterprise Linux release 9

**RHEL 10 Container**:
- ansible-core version: 2.16.x or higher
- Python version: 3.12.x
- User ID: 1001 (non-root)
- RHEL version: Red Hat Enterprise Linux release 10

## Security Scanning

### Trivy Security Scan

```bash
# Install Trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Run security scan
./scripts/containers/build-rhel10.sh --security-scan
```

### Grype Security Scan

```bash
# Install Grype
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin

# Run security scan
./scripts/containers/build-rhel10.sh --security-scan
```

## Enterprise Registry Integration

### Quay.io Integration

```bash
# Build and push to Quay.io
./scripts/containers/build-rhel9.sh \
  --registry quay.io \
  --name my-company/aider-lint-fixer \
  --tag v1.0-rhel9

# Push to registry (using Podman)
podman push quay.io/my-company/aider-lint-fixer:v1.0-rhel9

# Push to registry (using Docker)
docker push quay.io/my-company/aider-lint-fixer:v1.0-rhel9
```

### Harbor Registry

```bash
# Build for Harbor registry
./scripts/containers/build-rhel10.sh \
  --registry harbor.company.com \
  --name infrastructure/aider-lint-fixer \
  --tag v2.0-rhel10

# Push with Podman
podman push harbor.company.com/infrastructure/aider-lint-fixer:v2.0-rhel10
```

## CI/CD Integration

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    environment {
        RHEL_USERNAME = credentials('rhel-username')
        RHEL_PASSWORD = credentials('rhel-password')
    }
    stages {
        stage('Build RHEL Container') {
            steps {
                sh './scripts/containers/build-rhel9.sh --validate'
            }
        }
        stage('Security Scan') {
            steps {
                sh './scripts/containers/build-rhel10.sh --security-scan'
            }
        }
    }
}
```

### GitLab CI

```yaml
build-rhel-container:
  stage: build
  script:
    - ./scripts/containers/build-rhel9.sh --validate
  variables:
    RHEL_USERNAME: $RHEL_USERNAME
    RHEL_PASSWORD: $RHEL_PASSWORD
  only:
    - main
```

## Troubleshooting

### Subscription Issues

**Error: "This system is not registered"**
```bash
# Verify credentials
subscription-manager status

# Manual registration test
subscription-manager register --username=your-username --password=your-password
```

**Error: "No matches found for ansible-core"**
```bash
# Check repository access
dnf repolist
subscription-manager repos --list-enabled
```

### Build Failures

**Podman/Docker build fails with permission denied**
```bash
# For Podman (rootless by default)
podman system info

# For Docker - check daemon and permissions
sudo systemctl status docker
sudo usermod -aG docker $USER
newgrp docker
```

**Container fails to start**
```bash
# Check container logs (Podman)
podman logs <container-id>

# Check container logs (Docker)
docker logs <container-id>

# Debug interactively (Podman)
podman run -it --entrypoint /bin/bash my-company/aider-lint-fixer:rhel9

# Debug interactively (Docker)
docker run -it --entrypoint /bin/bash my-company/aider-lint-fixer:rhel9
```

### Network Issues

**Cannot reach Red Hat repositories**
```bash
# Test network connectivity
curl -I https://cdn.redhat.com

# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

## Best Practices

### Security

- Use build args files instead of command-line credentials
- Scan containers for vulnerabilities before deployment
- Regularly update base images and dependencies
- Use private registries for enterprise containers
- Prefer Podman for rootless container operations

### Performance

- Use `--no-cache` for clean builds in CI/CD
- Leverage Podman/Docker layer caching for development
- Use multi-stage builds for smaller production images
- Podman offers better performance for rootless operations

### Maintenance

- Automate container builds in CI/CD pipelines
- Monitor Red Hat security advisories
- Update containers when new RHEL versions are released
- Test containers in staging before production deployment
- Use Podman for better RHEL ecosystem integration

### Container Runtime Selection

- **Podman (Recommended)**: Native RHEL container tool, rootless by default, better security
- **Docker (Fallback)**: Widely supported, requires daemon, root privileges typically needed

## Related Documentation

- [Container Deployment Tutorial](../tutorials/container-deployment.md)
- [Container Architecture](../explanation/container-architecture.md)
- [Production Deployment](deploy-to-production.md)
