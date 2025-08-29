# Deployment Environments and Runtime Requirements

* Status: accepted
* Deciders: Development Team
* Date: 2025-08-24

Technical Story: Define supported deployment environments and runtime requirements for aider-lint-fixer across different operational contexts.

## Context and Problem Statement

The aider-lint-fixer tool needs to run in diverse environments ranging from local development to enterprise CI/CD pipelines. Different environments have varying constraints, security requirements, and available runtimes. Clear environment support decisions are needed to ensure consistent operation and proper resource allocation.

## Decision Drivers

* Multi-environment deployment requirements (local, CI/CD, enterprise)
* Python 3.11+ requirement vs. system Python availability
* Container security and isolation needs
* Enterprise compatibility (RHEL 9, air-gapped systems)
* CI/CD integration requirements
* Development workflow efficiency

## Considered Options

* Local installation only (pip/pyproject.toml)
* Container-first approach (Docker/Podman)
* Hybrid approach (local + containerized options)
* Cloud-native deployment (serverless functions)

## Decision Outcome

Chosen option: "Hybrid approach (local + containerized options)", because it provides maximum flexibility while addressing the Python 3.11+ requirement constraint and enterprise security needs.

### Positive Consequences

* Flexible deployment options for different use cases
* Addresses Python version compatibility issues (RHEL 9 ships with Python 3.9)
* Container isolation for security and consistency
* Enterprise-friendly with RHEL/UBI base images
* CI/CD ready with pre-built images

### Negative Consequences

* Increased complexity with multiple deployment paths
* Container runtime dependency for some environments
* Maintenance overhead for multiple environment configurations
* Potential inconsistencies between local and containerized execution

## Supported Deployment Environments

### 1. Local Development Environment

**Requirements:**
- Python 3.11+ (required for aider-chat compatibility)
- Node.js 16+ (for JavaScript/TypeScript linting)
- Git (for aider integration)

**Installation Methods:**
```bash
# pip installation
pip install aider-lint-fixer[all]

# Development installation
pip install -e ".[all]"

# Conda/mamba (future support)
conda install -c conda-forge aider-lint-fixer
```

**Supported Platforms:**
- macOS 11+ (Intel/Apple Silicon)
- Linux (Ubuntu 20.04+, RHEL 9+, Fedora 36+)
- Windows 10+ (WSL2 recommended)

### 2. Containerized Development (Podman)

**Base Image:** Red Hat UBI 9 with Python 3.11
**Container Runtime:** Podman (recommended for development)

**Features:**
- All linters pre-installed (Python, JavaScript, Infrastructure)
- Development tools (black, isort, mypy, pytest, vim)
- Live code mounting for real-time development
- Non-root user execution for security

**Usage:**
```bash
# Interactive development
./scripts/containers/dev-container.sh run

# Execute specific commands
./scripts/containers/dev-container.sh exec 'make test'
```

### 3. Production/CI Containerized (Docker)

**Default Container Strategy (macOS/Ubuntu):**
The default container (`Dockerfile`) provides the latest ansible-lint and linting tools, optimized for general development on macOS and Ubuntu:

```bash
# Build default container with latest tools
docker build -t aider-lint-fixer:latest .

# Run with mounted project directory
docker run --rm -v $(pwd):/workspace:ro \
  aider-lint-fixer:latest \
  --linters flake8,eslint --dry-run

# CI/CD integration
./scripts/containers/docker-run.sh --ci --max-files 20
```

**Key Benefits:**
- Latest ansible-lint with newest rules and features
- No subscription requirements or licensing constraints
- Simplified build process for development teams
- Optimized for macOS and Ubuntu development workflows

### 4. Enterprise Environments

**RHEL Version-Specific Container Strategy:**

Due to fundamental ansible-core version incompatibilities between RHEL versions, separate container build templates are required:

**RHEL Users: Customer-Build Required**

For RHEL environments, users must build their own containers due to subscription requirements:

**RHEL 9 Environment:**
- ansible-core 2.14 (frozen for RHEL 9 lifecycle until May 2032)
- Python 3.9 system dependency
- UBI 9 base image with customer subscription required
- Customer-build strategy: `Dockerfile.rhel9`

**RHEL 10 Environment:**
- ansible-core 2.16+ (modern version with latest features)
- Python 3.12 system dependency
- UBI 10 base image with customer subscription required
- Customer-build strategy: `Dockerfile.rhel10`

**Why Separate Strategy:**
- Default container uses latest ansible-lint for optimal development experience
- RHEL requires specific ansible-core versions tied to OS lifecycle
- Subscription licensing prevents distribution of pre-built RHEL containers
- Customer-build ensures compliance and version compatibility

**Customer Build Requirements:**
- RHEL subscription needed for ansible-core installation
- Cannot distribute pre-built containers due to licensing constraints
- Customers must build containers using their own subscriptions

**Automated Build Scripts:**
We provide comprehensive build automation to simplify the customer build process:

- **RHEL 9**: `scripts/containers/build-rhel9.sh`
  - Interactive credential prompting
  - Validation and security scanning
  - Dry-run capabilities for testing

- **RHEL 10**: `scripts/containers/build-rhel10.sh`
  - Enhanced security scanning with Trivy/Grype
  - RHEL 10 specific optimizations
  - Modern container features validation

**Manual Build Process:**

```dockerfile
# RHEL 9 Template (Dockerfile.rhel9)
FROM registry.redhat.io/ubi9/ubi:latest
RUN subscription-manager register --username=$RHEL_USER --password=$RHEL_PASS
RUN dnf install -y ansible-core python3-pip  # Gets 2.14.x
RUN pip install aider-lint-fixer
RUN subscription-manager unregister

# RHEL 10 Template (Dockerfile.rhel10)
FROM registry.redhat.io/ubi10/ubi:latest
RUN subscription-manager register --username=$RHEL_USER --password=$RHEL_PASS
RUN dnf install -y ansible-core python3-pip  # Gets 2.16.x+
RUN pip install aider-lint-fixer
RUN subscription-manager unregister
```

**Enterprise Build Process:**
```bash
# Customer builds with their subscription
docker build -f Dockerfile.rhel9 -t customer/aider-lint-fixer:rhel9 \
  --build-arg RHEL_USER=customer --build-arg RHEL_PASS=password .
```

**Security Features:**
- Non-root container execution
- Read-only source code mounts
- Customer-controlled subscription usage
- Clear licensing compliance

### 5. CI/CD Pipeline Integration

**GitHub Actions:**
```yaml
- name: Run aider-lint-fixer
  uses: docker://quay.io/takinosh/aider-lint-fixer:latest
  with:
    args: '--linters flake8,eslint --ci --max-files 10'
  env:
    DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
```

**GitLab CI:**
```yaml
aider-lint-fixer:
  stage: quality
  image: quay.io/takinosh/aider-lint-fixer:latest
  script:
    - aider-lint-fixer . --linters flake8,eslint --ci
```

**Jenkins:**
```groovy
docker.image('quay.io/takinosh/aider-lint-fixer:latest').inside {
    sh 'aider-lint-fixer . --linters flake8,eslint --ci'
}
```

## Runtime Requirements by Environment

### Minimum System Requirements
- **CPU**: 1 core (2+ recommended for parallel processing)
- **Memory**: 512MB (1GB+ recommended for large projects)
- **Storage**: 100MB for tool + 500MB for dependencies
- **Network**: Internet access for AI API calls (unless using local models)

### Python Runtime Requirements
- **Version**: Python 3.11+ (strict requirement)
- **Dependencies**: See pyproject.toml for complete list
- **Virtual Environment**: Recommended for local installations

### Node.js Runtime Requirements (for JavaScript linting)
- **Version**: Node.js 16+ (18+ recommended)
- **Package Manager**: npm or yarn
- **Global Packages**: ESLint, Prettier, JSHint (auto-installed in containers)

### Container Runtime Requirements
- **Podman**: 4.0+ (development environments)
- **Docker**: 20.10+ (CI/CD and production)
- **Container Storage**: 2GB for development image, 500MB for production
- **Volume Mounts**: Support for bind mounts and SELinux contexts

## Environment-Specific Configurations

### Development Environment Variables
```bash
# API Configuration
export DEEPSEEK_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here
export ANTHROPIC_API_KEY=your_key_here

# Tool Configuration
export AIDER_LINT_FIXER_LOG_LEVEL=DEBUG
export AIDER_LINT_FIXER_MAX_FILES=50
export AIDER_LINT_FIXER_NO_BANNER=false

# Ansible Configuration
export ANSIBLE_LINT_VERSION=enterprise
export ANSIBLE_LOCAL_TEMP=/tmp/ansible-local
```

### CI/CD Environment Variables
```bash
# CI Mode
export CI=true
export AIDER_LINT_FIXER_MAX_FILES=10
export AIDER_LINT_FIXER_MAX_ERRORS=5
export AIDER_LINT_FIXER_LOG_LEVEL=INFO

# Performance Optimization
export AIDER_LINT_FIXER_PARALLEL=true
export AIDER_LINT_FIXER_CACHE_DIR=./.aider-lint-cache
```

## Pros and Cons of the Options

### Local installation only

* Good, because simple setup for compatible systems
* Good, because direct access to system tools and configurations
* Good, because no container overhead
* Bad, because Python 3.11+ requirement blocks many systems
* Bad, because dependency conflicts with system packages
* Bad, because inconsistent environments across team members

### Container-first approach

* Good, because consistent environment across all deployments
* Good, because addresses Python version compatibility
* Good, because isolated dependencies and security
* Good, because enterprise-ready with RHEL/UBI images
* Bad, because container runtime dependency
* Bad, because potential performance overhead
* Bad, because complexity for simple local development

### Hybrid approach (local + containerized)

* Good, because flexibility for different use cases
* Good, because addresses Python compatibility issues
* Good, because supports both development and production workflows
* Good, because enterprise and CI/CD ready
* Bad, because increased maintenance complexity
* Bad, because potential behavior differences between environments
* Bad, because documentation and support overhead

### Cloud-native deployment

* Good, because serverless scalability
* Good, because no infrastructure management
* Bad, because vendor lock-in concerns
* Bad, because cold start latency issues
* Bad, because limited control over runtime environment
* Bad, because cost implications for frequent usage

## Implementation Evidence

### Container Infrastructure
- ✅ `Containerfile.dev`: RHEL UBI 9 development environment
- ✅ `Dockerfile.prod`: Python 3.11 slim production image
- ✅ `Dockerfile.rhel9`: RHEL 9 customer-build template with ansible-core 2.14
- ✅ `Dockerfile.rhel10`: RHEL 10 customer-build template with ansible-core 2.16+
- ✅ Pre-built images on quay.io registry (non-RHEL variants)
- ✅ Multi-architecture support (amd64, arm64)

### Automation Scripts
- ✅ `dev-container.sh`: Development container management
- ✅ `docker-run.sh`: Production container execution
- ✅ `setup-containers.sh`: Environment setup automation
- ✅ Customer build documentation and templates

### CI/CD Templates
- ✅ GitHub Actions workflow template
- ✅ GitLab CI configuration examples
- ✅ Jenkins pipeline examples
- ✅ RHEL enterprise build instructions

### Research Validation
- ✅ Testing confirmed UBI images require RHEL subscription for ansible-core
- ✅ RHEL 9 ansible-core frozen at 2.14 for lifecycle (until May 2032)
- ✅ RHEL 10 expected to ship with ansible-core 2.16+
- ✅ Customer-build strategy preserves architectural benefits while ensuring licensing compliance

## Links

* [ADR-0004](0004-hybrid-python-javascript-architecture.md) - Hybrid architecture enabling multi-runtime support
* [ADR-0005](0005-python-linter-ecosystem.md) - Python linter requirements
* [ADR-0006](0006-javascript-typescript-linter-ecosystem.md) - Node.js runtime requirements
* [Container Deployment Tutorial](../tutorials/container-deployment.md) - Comprehensive container usage documentation
