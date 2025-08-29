# ADR 0009: RHEL Container Build Requirements and Subscription Management

## Status

Accepted

## Context

Our research into RHEL-based container support for ansible-lint revealed critical subscription and licensing constraints that fundamentally impact how containers can be built and distributed. The Universal Base Images (UBI) provided by Red Hat do not include ansible-core packages by default, requiring full RHEL subscriptions for access to AppStream repositories during container builds.

**Strategic Decision**: The default container (`Dockerfile`) targets macOS and Ubuntu development with the latest ansible-lint, while RHEL users build their own containers using provided templates. This approach optimizes the developer experience for the majority of users while maintaining enterprise RHEL support.

### Key Findings

1. **UBI Limitations**: UBI 9 and UBI 10 images contain only base OS packages, not AppStream content like ansible-core
2. **Subscription Requirements**: ansible-core installation requires active RHEL subscription and registration via subscription-manager
3. **Licensing Constraints**: Cannot distribute pre-built containers with ansible-core due to Red Hat licensing requirements
4. **Version Incompatibilities**: RHEL 9 (ansible-core 2.14) and RHEL 10 (ansible-core 2.16+) represent incompatible automation ecosystems

### Enterprise Context

Enterprise customers typically have existing RHEL subscriptions and the infrastructure to build custom containers. This customer-build approach aligns with enterprise security practices of controlling their container supply chain while ensuring licensing compliance.

## Decision

We will implement a **customer-build container strategy** where enterprise customers build their own containers using provided Dockerfile templates and their RHEL subscriptions.

### Container Build Architecture

1. **Separate RHEL Version Templates**: Distinct Dockerfile templates for RHEL 9 and RHEL 10
2. **Customer Subscription Integration**: Build process requires customer's Red Hat credentials
3. **Version-Specific Optimization**: Each template optimized for its respective ansible-core version
4. **Clear Documentation**: Comprehensive build instructions and subscription requirements

## Implementation

### RHEL 9 Dockerfile Template

```dockerfile
# Dockerfile.rhel9
FROM registry.redhat.io/ubi9/ubi:latest

# Customer must provide their Red Hat credentials
ARG RHEL_USERNAME
ARG RHEL_PASSWORD

# Register with Red Hat subscription manager
RUN subscription-manager register --username=${RHEL_USERNAME} --password=${RHEL_PASSWORD}
RUN subscription-manager attach --auto

# Install ansible-core 2.14.x from AppStream
RUN dnf update -y && \
    dnf install -y ansible-core python3-pip && \
    dnf clean all

# Install aider-lint-fixer
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt
COPY aider_lint_fixer/ /opt/aider-lint-fixer/

# Security: Run as non-root user
RUN useradd -m -u 1001 aider
USER 1001

WORKDIR /workspace
ENTRYPOINT ["python3", "/opt/aider-lint-fixer"]
```

### RHEL 10 Dockerfile Template

```dockerfile
# Dockerfile.rhel10
FROM registry.redhat.io/ubi10/ubi:latest

# Customer must provide their Red Hat credentials
ARG RHEL_USERNAME
ARG RHEL_PASSWORD

# Register with Red Hat subscription manager
RUN subscription-manager register --username=${RHEL_USERNAME} --password=${RHEL_PASSWORD}
RUN subscription-manager attach --auto

# Install ansible-core 2.16+ from AppStream
RUN dnf update -y && \
    dnf install -y ansible-core python3-pip && \
    dnf clean all

# Install aider-lint-fixer
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt
COPY aider_lint_fixer/ /opt/aider-lint-fixer/

# Security: Run as non-root user
RUN useradd -m -u 1001 aider
USER 1001

WORKDIR /workspace
ENTRYPOINT ["python3", "/opt/aider-lint-fixer"]
```

### Customer Build Process

#### Automated Build Scripts

We provide comprehensive build scripts that handle credential management, validation, and security best practices:

**RHEL 9 Build Script**: `scripts/containers/build-rhel9.sh`
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

**RHEL 10 Build Script**: `scripts/containers/build-rhel10.sh`
```bash
# Interactive build (prompts for credentials)
./scripts/containers/build-rhel10.sh

# Build with security scanning
./scripts/containers/build-rhel10.sh \
  --name my-company/aider-lint-fixer \
  --tag v2.0-rhel10 \
  --validate \
  --security-scan

# Build with custom registry
./scripts/containers/build-rhel10.sh \
  --registry quay.io \
  --username myuser \
  --password mypass
```

#### Manual Build Commands

For customers preferring manual builds:

```bash
# RHEL 9 Container
docker build \
  --build-arg RHEL_USERNAME=<customer-username> \
  --build-arg RHEL_PASSWORD=<customer-password> \
  -f Dockerfile.rhel9 \
  -t customer/aider-lint-fixer:rhel9 .

# RHEL 10 Container
docker build \
  --build-arg RHEL_USERNAME=<customer-username> \
  --build-arg RHEL_PASSWORD=<customer-password> \
  -f Dockerfile.rhel10 \
  -t customer/aider-lint-fixer:rhel10 .
```

#### Security Best Practices

1. **Credential Management**: Use build secrets or environment files instead of command-line arguments
2. **Multi-stage Builds**: Separate subscription registration from final image to avoid credential leakage
3. **Image Scanning**: Customers should scan built images for vulnerabilities
4. **Registry Security**: Push to private registries with proper access controls

### Documentation Requirements

#### Customer Build Guide

1. **Prerequisites**: Active RHEL subscription, container build environment
2. **Build Instructions**: Step-by-step commands with security considerations
3. **Version Selection**: Guidance on choosing RHEL 9 vs RHEL 10
4. **Troubleshooting**: Common subscription and build issues
5. **Validation**: Testing built containers for functionality

#### Support Materials

1. **Build Scripts**: 
   - `scripts/containers/build-rhel9.sh` - Automated RHEL 9 container builds
   - `scripts/containers/build-rhel10.sh` - Automated RHEL 10 container builds
   - Interactive credential prompting and validation
   - Security scanning integration (Trivy/Grype)
   - Dry-run capabilities for testing

2. **CI/CD Integration**: Templates for enterprise CI/CD pipelines
3. **Version Matrix**: ansible-core compatibility documentation
4. **Migration Guide**: Transitioning between RHEL versions

## Consequences

### Positive

- **Licensing Compliance**: Customers use their own subscriptions, ensuring legal compliance
- **Security Control**: Customers control their container supply chain and build environment
- **Version Optimization**: Each container optimized for its specific RHEL version and ansible-core
- **Enterprise Alignment**: Matches enterprise practices of building custom containers
- **Scalability**: Approach scales to future RHEL versions without distribution constraints

### Negative

- **Customer Complexity**: Requires customers to manage container builds and subscriptions
- **Support Overhead**: Additional support for build processes and subscription issues
- **Distribution Limitations**: Cannot provide ready-to-use containers for immediate testing
- **Documentation Burden**: Extensive documentation required for customer success

### Mitigation Strategies

1. **Comprehensive Documentation**: Detailed guides and troubleshooting resources
2. **Build Automation**: Scripts and templates to simplify customer build processes
3. **Support Training**: Prepare support team for subscription and build-related issues
4. **Alternative Options**: Maintain pip-based installation for non-containerized deployments

## Related ADRs

- [ADR 0008: Deployment Environments and Runtime Requirements](0008-deployment-environments.md) - Updated with customer-build strategy
- [ADR 0007: Infrastructure and DevOps Linter Ecosystem](0007-infrastructure-devops-linter-ecosystem.md) - ansible-lint version management
- [ADR 0003: Modular Plugin System](0003-modular-plugin-system.md) - Plugin architecture supporting multiple environments

## Implementation Evidence

### Research Validation

- **UBI Testing**: Confirmed ansible-core unavailability in UBI repositories
- **Subscription Requirements**: Validated subscription-manager registration necessity
- **Version Compatibility**: Documented ansible-core 2.14 vs 2.16+ incompatibilities
- **Performance Analysis**: UBI 10 provides 16% smaller images and modern security features

### Customer Feedback Integration

- **Enterprise Requirements**: Aligns with enterprise container build practices
- **Security Preferences**: Non-root execution and read-only mounts
- **Subscription Management**: Leverages existing customer RHEL infrastructure

### Technical Validation

- **Build Process**: Dockerfile templates and automated build scripts tested with subscription registration
- **Build Scripts**: Comprehensive automation with `scripts/containers/build-rhel9.sh` and `scripts/containers/build-rhel10.sh`
- **Security Features**: Non-root user execution, credential management, and minimal attack surface
- **Version Isolation**: Separate containers prevent ansible-core conflicts
- **Validation Tools**: Built-in image validation and security scanning capabilities
- **Documentation**: Comprehensive build guides and troubleshooting resources

## Notes

This ADR establishes the foundation for RHEL container support while respecting Red Hat's licensing model and enterprise customer requirements. The customer-build approach ensures legal compliance while providing optimized containers for each RHEL version.

Future considerations include monitoring Red Hat's container distribution policies and evaluating alternative base images if licensing constraints change.
