# Container Guide for aider-lint-fixer

This guide covers running aider-lint-fixer in containerized environments using Podman (development) and Docker (production/CI).

## 🎯 Why Containers?

- **RHEL 9 Compatibility**: RHEL 9 ships with Python 3.9, but aider-lint-fixer requires Python 3.11+
- **Isolated Environment**: No conflicts with system Python or dependencies
- **CI/CD Ready**: Perfect for GitHub Actions, GitLab CI, Jenkins, etc.
- **Consistent Results**: Same environment across development and production

## 📋 Prerequisites

### Podman (Recommended for Development)
```bash
# RHEL/CentOS/Fedora
sudo dnf install podman

# Ubuntu/Debian
sudo apt install podman

# macOS
brew install podman
```

### Docker (For CI/CD and Production)
```bash
# Follow instructions at https://docs.docker.com/get-docker/
# Or use package manager:

# RHEL/CentOS/Fedora
sudo dnf install docker

# Ubuntu/Debian
sudo apt install docker.io

# Start Docker daemon
sudo systemctl start docker
```

## 🚀 Quick Start

### 1. Setup (One-time)
```bash
# Run the setup script
./scripts/containers/setup-containers.sh

# Or setup individual components
./scripts/containers/setup-containers.sh --podman-only
./scripts/containers/setup-containers.sh --docker-only
```

### 2. Development with Podman
```bash
# Start interactive development session
./scripts/containers/dev-container.sh run

# Inside container, you can:
make test                    # Run tests
make lint                    # Run linting
python -m aider_lint_fixer   # Use the tool
```

### 3. Production with Docker
```bash
# Run on current project
./scripts/containers/docker-run.sh --linters flake8,eslint

# CI/CD mode
./scripts/containers/docker-run.sh --ci --dry-run --linters flake8
```

## 🔧 Development Environment (Podman)

### Container Features
- **Base**: Red Hat UBI 9 with Python 3.11
- **All Linters**: flake8, pylint, ansible-lint, eslint, jshint, prettier
- **Development Tools**: black, isort, mypy, pytest, vim
- **Live Editing**: Your code is mounted for real-time development

### Basic Commands
```bash
# Build development image
./scripts/containers/dev-container.sh build

# Start interactive session
./scripts/containers/dev-container.sh run

# Get shell access (if container is running)
./scripts/containers/dev-container.sh shell

# Execute commands in container
./scripts/containers/dev-container.sh exec 'make test'

# Stop and remove container
./scripts/containers/dev-container.sh stop
./scripts/containers/dev-container.sh remove

# Clean everything (container + image)
./scripts/containers/dev-container.sh clean
```

### Environment Configuration
```bash
# Use custom .env file
./scripts/containers/dev-container.sh run --env-file .env.production

# Set API key directly
./scripts/containers/dev-container.sh run --api-key sk-your-key-here

# Add custom volume mounts
./scripts/containers/dev-container.sh run --mount /host/path:/container/path
```

### Development Workflow
```bash
# 1. Start development session
./scripts/containers/dev-container.sh run

# 2. Inside container - normal development
make format      # Format code
make lint        # Run linters
make test        # Run tests
make qa          # Full quality assurance

# 3. Test the tool itself
python -m aider_lint_fixer . --dry-run --verbose

# 4. Exit container (Ctrl+D or exit)
```

## 🐳 Production Environment (Docker)

### Container Features
- **Base**: Python 3.11 slim (minimal size)
- **Multi-stage Build**: Optimized for production
- **Non-root User**: Security best practices
- **Health Checks**: Built-in monitoring

### Basic Usage
```bash
# Run on current directory
./scripts/containers/docker-run.sh

# Specify linters
./scripts/containers/docker-run.sh --linters flake8,eslint,ansible-lint

# Dry run (no changes made)
./scripts/containers/docker-run.sh --dry-run --verbose

# Interactive mode
./scripts/containers/docker-run.sh --interactive

# CI/CD mode
./scripts/containers/docker-run.sh --ci --max-files 20
```

### Advanced Options
```bash
# Build image first
./scripts/containers/docker-run.sh --build

# Custom workspace
./scripts/containers/docker-run.sh --workspace /path/to/project

# Custom output directory
./scripts/containers/docker-run.sh --output-dir ./results

# Custom cache directory
./scripts/containers/docker-run.sh --cache-dir ./.my-cache

# Use specific image
./scripts/containers/docker-run.sh --image my-registry/aider-lint-fixer:v1.9.0
```

### Environment Variables
```bash
# API Keys (choose one)
export DEEPSEEK_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here
export ANTHROPIC_API_KEY=your_key_here

# Tool Configuration
export AIDER_LINT_FIXER_LOG_LEVEL=INFO
export AIDER_LINT_FIXER_MAX_FILES=10
export AIDER_LINT_FIXER_MAX_ERRORS=5
export AIDER_LINT_FIXER_NO_BANNER=false
```

## 🔄 CI/CD Integration

### GitHub Actions
```bash
# Copy the template to your repository
cp scripts/github-actions/docker-lint.yml .github/workflows/aider-lint-fixer.yml

# Edit the workflow file and customize:
# - Repository owner name
# - Linters to run
# - API key secrets
# - Trigger conditions
```

### GitLab CI
```yaml
# .gitlab-ci.yml
aider-lint-fixer:
  stage: quality
  image: docker:latest
  services:
    - docker:dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker build -f scripts/containers/Dockerfile.prod -t aider-lint-fixer:ci .
  script:
    - |
      docker run --rm \
        -v $CI_PROJECT_DIR:/workspace:ro \
        -v $CI_PROJECT_DIR/results:/output \
        -e DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY \
        -e CI=true \
        aider-lint-fixer:ci \
        /workspace --linters flake8,eslint --ci --max-files 10
  artifacts:
    paths:
      - results/
    expire_in: 1 week
  only:
    - merge_requests
    - main
```

### Jenkins
```groovy
pipeline {
    agent any
    
    stages {
        stage('Lint with aider-lint-fixer') {
            steps {
                script {
                    // Build image
                    sh 'docker build -f scripts/containers/Dockerfile.prod -t aider-lint-fixer:ci .'
                    
                    // Run linting
                    sh '''
                        docker run --rm \
                            -v ${WORKSPACE}:/workspace:ro \
                            -v ${WORKSPACE}/results:/output \
                            -e DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY} \
                            -e CI=true \
                            aider-lint-fixer:ci \
                            /workspace --linters flake8,eslint --ci --max-files 10
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'results/**/*', fingerprint: true
                }
            }
        }
    }
}
```

## 🔒 Security Considerations

### Container Security
- **Non-root User**: Production container runs as non-root user `aider`
- **Read-only Mounts**: Source code mounted read-only by default
- **Minimal Base**: Uses slim/minimal base images
- **No Secrets in Layers**: API keys only via environment variables

### API Key Management
```bash
# Use environment files (never commit these!)
echo "DEEPSEEK_API_KEY=your_key_here" > .env

# Use CI/CD secrets
# GitHub: Repository Settings → Secrets and variables → Actions
# GitLab: Project Settings → CI/CD → Variables
# Jenkins: Manage Jenkins → Configure System → Global Properties

# Use external secret managers
# HashiCorp Vault, AWS Secrets Manager, etc.
```

### Network Security
```bash
# Air-gapped environments - build locally
docker build -f scripts/containers/Dockerfile.prod -t aider-lint-fixer:local .

# Private registries
docker tag aider-lint-fixer:latest your-registry.com/aider-lint-fixer:1.9.0
docker push your-registry.com/aider-lint-fixer:1.9.0
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Permission Denied Errors
```bash
# Fix script permissions
chmod +x scripts/containers/*.sh

# SELinux issues (RHEL/CentOS)
# Add :Z to volume mounts (already included in scripts)
-v $(pwd):/workspace:Z
```

#### 2. API Key Not Found
```bash
# Check environment file
cat .env

# Test with explicit API key
./scripts/containers/docker-run.sh --api-key your_key_here

# Use dry-run mode for testing
./scripts/containers/docker-run.sh --dry-run
```

#### 3. Container Build Failures
```bash
# Clean Docker system
docker system prune -f

# Build with verbose output
docker build -f scripts/containers/Dockerfile.prod --progress=plain -t aider-lint-fixer:debug .

# Check disk space
docker system df
```

#### 4. Podman Issues on RHEL
```bash
# Enable lingering for user sessions
sudo loginctl enable-linger $USER

# Configure registries
cat ~/.config/containers/registries.conf

# Reset Podman
podman system reset
```

#### 5. Network Issues
```bash
# Test with direct Docker run
docker run --rm python:3.11-slim python --version

# Check proxy settings
docker run --rm -e http_proxy=$http_proxy python:3.11-slim curl -I http://google.com
```

### Debug Mode
```bash
# Enable debug output
export AIDER_LINT_FIXER_DEBUG=true

# Run with debug
./scripts/containers/docker-run.sh --debug

# Check container logs
docker logs <container_name>
```

### Getting Help
```bash
# Script help
./scripts/containers/dev-container.sh --help
./scripts/containers/docker-run.sh --help

# Container status
./scripts/containers/dev-container.sh status

# System info
podman info
docker info
```

## 📊 Performance Optimization

### Image Size Optimization
```bash
# Check image sizes
docker images aider-lint-fixer

# Multi-stage builds already implemented
# Production image is ~300MB vs ~1GB development image
```

### Caching Strategy
```bash
# Use persistent cache directory
mkdir -p .aider-lint-cache

# In CI, cache this directory between runs
# GitHub Actions: uses actions/cache@v4
# GitLab CI: cache: paths: [.aider-lint-cache]
```

### Parallel Execution
```bash
# Run multiple linters in parallel (coming soon)
./scripts/containers/docker-run.sh --linters flake8,eslint --parallel

# Process multiple projects
for project in project1 project2 project3; do
  ./scripts/containers/docker-run.sh --workspace $project &
done
wait
```

## 🔄 Maintenance

### Regular Updates
```bash
# Update base images
./scripts/containers/dev-container.sh rebuild
./scripts/containers/docker-run.sh --build

# Update dependencies
# Edit requirements.txt, then rebuild images
```

### Cleanup
```bash
# Clean development environment
./scripts/containers/dev-container.sh clean

# Clean Docker system
docker system prune -f
docker volume prune -f

# Clean Podman system
podman system prune -f
```

---

## 📚 Additional Resources

- [aider-lint-fixer README](../../README.md)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Podman Tutorials](https://github.com/containers/podman/tree/main/docs/tutorials)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

For issues or questions, please visit our [GitHub Issues](https://github.com/tosin2013/aider-lint-fixer/issues).