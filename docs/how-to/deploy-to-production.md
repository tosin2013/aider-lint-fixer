---
title: Deploy To Production
---

# Deploy To Production

This guide covers production deployment strategies for aider-lint-fixer across different environments, including containerized deployments and CI/CD integration.

## Prerequisites

- **Container Runtime**: Docker (macOS/Ubuntu) or Podman (RHEL)
- **Python 3.11+**: For local installations
- **Node.js 16+**: For JavaScript linter support
- **Production Environment**: Target deployment platform configured
- **Credentials**: Container registry access and RHEL subscriptions (if applicable)

## Deployment Strategies

### Container-Based Deployment (Recommended)

#### Default Container (macOS/Ubuntu)

**1. Build Production Container**
```bash
# Clone and build
git clone <repository-url>
cd aider-lint-fixer
docker build -t aider-lint-fixer:latest .
```

**2. Deploy to Container Registry**
```bash
# Tag for registry
docker tag aider-lint-fixer:latest your-registry/aider-lint-fixer:v1.0.0

# Push to registry
docker push your-registry/aider-lint-fixer:v1.0.0
```

**3. Deploy to Production**
```bash
# Pull and run in production
docker pull your-registry/aider-lint-fixer:v1.0.0
docker run -d --name aider-lint-fixer \
  -v /path/to/projects:/workspace:ro \
  -e AIDER_LINT_CONFIG=/workspace/.aider-lint.yaml \
  your-registry/aider-lint-fixer:v1.0.0
```

#### RHEL Enterprise Deployment

**1. Build RHEL Container**
```bash
# RHEL 9 production build
./scripts/containers/build-rhel9.sh --production \
  --registry your-registry.redhat.com \
  --tag aider-lint-fixer-rhel9:v1.0.0

# RHEL 10 production build  
./scripts/containers/build-rhel10.sh --production \
  --registry your-registry.redhat.com \
  --tag aider-lint-fixer-rhel10:v1.0.0
```

**2. Deploy with Podman (RHEL)**
```bash
# Pull and run with Podman
podman pull your-registry.redhat.com/aider-lint-fixer-rhel9:v1.0.0
podman run -d --name aider-lint-fixer \
  -v /path/to/projects:/workspace:ro,Z \
  -e AIDER_LINT_CONFIG=/workspace/.aider-lint.yaml \
  your-registry.redhat.com/aider-lint-fixer-rhel9:v1.0.0
```

### Direct Installation Deployment

**1. Prepare Production Environment**
```bash
# Create production user
sudo useradd -m -s /bin/bash aider-lint-fixer
sudo su - aider-lint-fixer

# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Install Node.js Dependencies**
```bash
# Install Node.js linters
npm install -g eslint@^8.0.0 prettier@^3.0.0 jshint@^2.13.0
```

**3. Configure Production Settings**
```bash
# Create production config
cat > /home/aider-lint-fixer/.aider-lint.yaml << EOF
profile: production
linters:
  python:
    - flake8
    - pylint
    - mypy
  javascript:
    - eslint
    - prettier
logging:
  level: INFO
  format: json
EOF
```

## CI/CD Integration

### GitHub Actions Deployment

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production
on:
  push:
    tags: ['v*']

jobs:
  deploy-default:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build container
        run: docker build -t aider-lint-fixer:${{ github.ref_name }} .
      - name: Push to registry
        run: |
          echo ${{ secrets.REGISTRY_PASSWORD }} | docker login -u ${{ secrets.REGISTRY_USERNAME }} --password-stdin
          docker push aider-lint-fixer:${{ github.ref_name }}

  deploy-rhel:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build RHEL containers
        env:
          RHEL_USERNAME: ${{ secrets.RHEL_USERNAME }}
          RHEL_PASSWORD: ${{ secrets.RHEL_PASSWORD }}
        run: |
          ./scripts/containers/build-rhel9.sh --tag aider-lint-fixer-rhel9:${{ github.ref_name }}
          ./scripts/containers/build-rhel10.sh --tag aider-lint-fixer-rhel10:${{ github.ref_name }}
```

### GitLab CI Deployment

Create `.gitlab-ci.yml`:
```yaml
stages:
  - build
  - deploy

build-containers:
  stage: build
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG
  only:
    - tags

deploy-production:
  stage: deploy
  script:
    - docker pull $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG
    - docker stop aider-lint-fixer || true
    - docker rm aider-lint-fixer || true
    - docker run -d --name aider-lint-fixer $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG
  environment:
    name: production
  only:
    - tags
```

### Jenkins Pipeline

Create `Jenkinsfile`:
```groovy
pipeline {
    agent any
    
    stages {
        stage('Build') {
            steps {
                script {
                    def image = docker.build("aider-lint-fixer:${env.BUILD_NUMBER}")
                }
            }
        }
        
        stage('Test') {
            steps {
                sh 'python -m pytest tests/'
            }
        }
        
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                script {
                    docker.withRegistry('https://your-registry.com', 'registry-credentials') {
                        def image = docker.image("aider-lint-fixer:${env.BUILD_NUMBER}")
                        image.push()
                        image.push('latest')
                    }
                }
            }
        }
    }
}
```

## Production Configuration

### Environment Variables

```bash
# Core configuration
export AIDER_LINT_CONFIG=/etc/aider-lint/config.yaml
export AIDER_LINT_PROFILE=production
export AIDER_LINT_LOG_LEVEL=INFO

# AI integration
export OPENAI_API_KEY=your-api-key
export AIDER_CHAT_MODEL=gpt-4

# Container-specific
export AIDER_LINT_WORKSPACE=/workspace
export AIDER_LINT_OUTPUT_FORMAT=json
```

### Production Configuration File

```yaml
# /etc/aider-lint/config.yaml
profile: production
concurrency: 4
timeout: 300

linters:
  python:
    - flake8
    - pylint
    - mypy
    - bandit
  javascript:
    - eslint
    - prettier
  infrastructure:
    - ansible-lint

output:
  format: json
  file: /var/log/aider-lint/results.json

logging:
  level: INFO
  format: json
  file: /var/log/aider-lint/application.log

ai:
  enabled: true
  model: gpt-4
  max_tokens: 2000
  cache_enabled: true
```

## Verification and Health Checks

### Container Health Check

```bash
# Check container status
docker ps | grep aider-lint-fixer

# Check container logs
docker logs aider-lint-fixer --tail 50

# Run health check
docker exec aider-lint-fixer python -c "
import aider_lint_fixer
print('Health check passed')
"
```

### Functional Testing

```bash
# Test linting functionality
docker exec aider-lint-fixer aider-lint-fixer \
  --file /workspace/test_file.py \
  --linters flake8,pylint \
  --output json

# Test AI integration
docker exec aider-lint-fixer aider-lint-fixer \
  --file /workspace/test_file.py \
  --fix \
  --ai-enabled
```

### Performance Monitoring

```bash
# Monitor resource usage
docker stats aider-lint-fixer

# Check processing metrics
curl -s http://localhost:8080/metrics | grep aider_lint
```

## Troubleshooting

### Container Issues

**Container won't start:**
```bash
# Check container logs
docker logs aider-lint-fixer

# Inspect container configuration
docker inspect aider-lint-fixer

# Run interactively for debugging
docker run -it --entrypoint /bin/bash aider-lint-fixer:latest
```

**Permission issues (RHEL/SELinux):**
```bash
# Fix SELinux volume labels
podman run -v /path/to/projects:/workspace:ro,Z aider-lint-fixer

# Check SELinux context
ls -Z /path/to/projects
```

### RHEL Subscription Issues

**Subscription not found:**
```bash
# Check subscription status
subscription-manager status

# Register system
subscription-manager register --username your-username

# Attach subscription
subscription-manager attach --auto
```

### Performance Issues

**Slow linting performance:**
```bash
# Increase concurrency
export AIDER_LINT_CONCURRENCY=8

# Use faster linters only
export AIDER_LINT_LINTERS=flake8,eslint

# Enable caching
export AIDER_LINT_CACHE_ENABLED=true
```

## Security Considerations

### Container Security

- **Non-root execution**: Containers run as UID 1001
- **Read-only volumes**: Mount project code read-only
- **Network isolation**: Use custom networks for container communication
- **Secret management**: Use environment variables or secret management systems

### Credential Management

```bash
# Use Docker secrets (Swarm mode)
echo "your-api-key" | docker secret create openai-api-key -

# Use Kubernetes secrets
kubectl create secret generic aider-lint-secrets \
  --from-literal=openai-api-key=your-api-key
```

## Related Guides

- [Configure Linters](./configure-linters.md) - Linter configuration options
- [RHEL Container Builds](./rhel-container-builds.md) - RHEL-specific deployment
- [Red Hat Developer Guide](./red-hat-developer-guide.md) - RHEL development workflows
- [Container Architecture](../explanation/container-architecture.md) - Container strategy overview