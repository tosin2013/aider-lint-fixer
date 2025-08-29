# Getting Started with Containers

This tutorial will guide you through using aider-lint-fixer in containerized environments, from basic Docker usage to enterprise RHEL deployments.

## Prerequisites

Before you begin, ensure you have:

- **Docker** or **Podman** installed
- **Git** for cloning repositories
- **OpenAI API key** (optional, for AI features)
- Basic familiarity with containers

## Quick Start with Docker

### 1. Pull the Container Image

```bash
# Pull the latest default container
docker pull aider-lint-fixer:latest

# Or for RHEL environments (customer-built)
podman pull your-registry.redhat.com/aider-lint-fixer-rhel9:latest
```

### 2. Run on Your Codebase

```bash
# Basic linting check
docker run --rm \
  -v $(pwd):/workspace \
  aider-lint-fixer:latest \
  aider-lint-fixer --path /workspace --check-only

# Auto-fix issues
docker run --rm \
  -v $(pwd):/workspace \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  aider-lint-fixer:latest \
  aider-lint-fixer --path /workspace --auto-fix
```

## Building Custom Containers

### Default Container (macOS/Ubuntu)

```bash
# Clone the repository
git clone https://github.com/your-org/aider-lint-fixer.git
cd aider-lint-fixer

# Build the container
docker build -t aider-lint-fixer:custom .

# Test the build
docker run --rm aider-lint-fixer:custom aider-lint-fixer --version
```

### RHEL Enterprise Containers

For RHEL environments, use the provided build scripts:

```bash
# RHEL 9 container
./scripts/containers/build-rhel9.sh

# RHEL 10 container  
./scripts/containers/build-rhel10.sh
```

These scripts handle:
- RHEL subscription management
- Version-specific ansible-core installation
- Security best practices
- Container registry integration

## Container Configuration

### Environment Variables

```bash
# Core configuration
AIDER_LINT_CONFIG=/etc/aider-lint/config.yaml
AIDER_LINT_PROFILE=production

# AI integration
OPENAI_API_KEY=your-api-key
AIDER_CHAT_MODEL=gpt-4

# Logging
AIDER_LINT_LOG_LEVEL=INFO
AIDER_LINT_LOG_FORMAT=json
```

### Volume Mounts

```bash
# Mount your codebase
-v $(pwd):/workspace

# Mount configuration
-v ~/.config/aider-lint-fixer:/etc/aider-lint

# For RHEL with SELinux
-v $(pwd):/workspace:Z
```

## Advanced Container Usage

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  aider-lint-fixer:
    image: aider-lint-fixer:latest
    volumes:
      - ./:/workspace
      - ./config:/etc/aider-lint
    environment:
      - AIDER_LINT_PROFILE=development
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    command: aider-lint-fixer --path /workspace --interactive
```

```bash
# Run with compose
docker-compose run --rm aider-lint-fixer
```

### Batch Processing Container

```bash
# Create a batch processing script
cat > batch-lint.sh << 'EOF'
#!/bin/bash
docker run --rm \
  -v $(pwd):/workspace \
  -v ~/.config/aider-lint-fixer:/etc/aider-lint:ro \
  -e AIDER_LINT_PROFILE=batch \
  aider-lint-fixer:latest \
  aider-lint-fixer --path /workspace --auto-fix --report
EOF

chmod +x batch-lint.sh
./batch-lint.sh
```

## Enterprise RHEL Deployment

### Customer Build Process

```bash
# Set up RHEL credentials
export RHEL_USERNAME="your-username"
export RHEL_PASSWORD="your-password"

# Build RHEL 9 container
./scripts/containers/build-rhel9.sh \
  --registry your-registry.redhat.com \
  --tag aider-lint-fixer-rhel9:v1.0.0

# Deploy to OpenShift
oc new-app your-registry.redhat.com/aider-lint-fixer-rhel9:v1.0.0
```

### Security Configuration

```bash
# Run with security constraints
podman run --rm \
  --security-opt no-new-privileges \
  --cap-drop ALL \
  --user 1001:1001 \
  -v $(pwd):/workspace:Z \
  your-registry.redhat.com/aider-lint-fixer-rhel9:latest \
  aider-lint-fixer --path /workspace --check-only
```

## Verifying Container Setup

### Health Checks

```bash
#!/bin/bash
# scripts/verify-container.sh

echo "Testing container functionality..."

# Test basic execution
if docker run --rm aider-lint-fixer:latest aider-lint-fixer --version; then
    echo "✓ Container executes successfully"
else
    echo "✗ Container execution failed"
    exit 1
fi

# Test volume mounting
if docker run --rm -v $(pwd):/workspace aider-lint-fixer:latest ls /workspace; then
    echo "✓ Volume mounting works"
else
    echo "✗ Volume mounting failed"
    exit 1
fi

echo "Container verification complete!"
```

## Next Steps

- Learn about [Container Architecture](../explanation/container-architecture.md)
- Explore [CI/CD Integration](../how-to/how-to-deploy-your-application.md)
- Review [RHEL Container Requirements](../adrs/0009-rhel-container-build-requirements.md)
- Check [Security Best Practices](../how-to/security-best-practices.md)
