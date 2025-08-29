# How to Deploy Aider-Lint-Fixer

This guide covers deployment patterns for aider-lint-fixer CLI tool in various environments, including CI/CD pipelines, development teams, and containerized execution environments.

## Deployment Scenarios

Aider-lint-fixer is a CLI tool with several deployment patterns depending on your use case:

### 1. **CI/CD Pipeline Integration** (Most Common)
Run aider-lint-fixer as part of your automated testing and code quality pipeline.

### 2. **Developer Workstation Setup**
Install aider-lint-fixer on development machines for local linting and fixing.

### 3. **Containerized Execution**
Use containers for consistent execution across different environments.

### 4. **Batch Processing Jobs**
Run aider-lint-fixer on large codebases or scheduled maintenance tasks.

## Pre-Deployment Checklist

- [ ] Container images built and tested (if using containers)
- [ ] Configuration files validated
- [ ] Environment variables configured
- [ ] API keys and credentials properly managed
- [ ] Target codebase access configured
- [ ] Output and logging destinations set up

## CI/CD Pipeline Integration

### GitHub Actions Integration

```yaml
# .github/workflows/lint-and-fix.yml
name: Lint and Fix Code

on:
  pull_request:
    branches: [ main, develop ]
  push:
    branches: [ main ]

jobs:
  lint-and-fix:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
      with:
        token: ${{ secrets.GITHUB_TOKEN }}
        
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install aider-lint-fixer
      run: |
        pip install aider-lint-fixer
        
    - name: Run linting and fixes
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        aider-lint-fixer --path . --auto-fix --profile ci
        
    - name: Commit fixes
      if: github.event_name == 'pull_request'
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add -A
        git diff --staged --quiet || git commit -m "Auto-fix linting issues"
        git push
```

### GitLab CI Integration

```yaml
# .gitlab-ci.yml
stages:
  - lint
  - fix

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip/

lint-code:
  stage: lint
  image: python:3.11-slim
  before_script:
    - pip install aider-lint-fixer
  script:
    - aider-lint-fixer --path . --check-only --profile ci
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

fix-code:
  stage: fix
  image: python:3.11-slim
  before_script:
    - pip install aider-lint-fixer
    - git config --global user.email "gitlab-ci@example.com"
    - git config --global user.name "GitLab CI"
  script:
    - aider-lint-fixer --path . --auto-fix --profile ci
    - |
      if [ -n "$(git status --porcelain)" ]; then
        git add -A
        git commit -m "Auto-fix linting issues [skip ci]"
        git push origin HEAD:$CI_COMMIT_REF_NAME
      fi
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  variables:
    OPENAI_API_KEY: $OPENAI_API_KEY
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    environment {
        OPENAI_API_KEY = credentials('openai-api-key')
        AIDER_LINT_PROFILE = 'ci'
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install aider-lint-fixer'
            }
        }
        
        stage('Lint Check') {
            steps {
                sh 'aider-lint-fixer --path . --check-only'
            }
        }
        
        stage('Auto Fix') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    aider-lint-fixer --path . --auto-fix
                    if [ -n "$(git status --porcelain)" ]; then
                        git config user.email "jenkins@example.com"
                        git config user.name "Jenkins CI"
                        git add -A
                        git commit -m "Auto-fix linting issues"
                        git push origin main
                    fi
                '''
            }
        }
    }
}
```

## Container-Based Deployment

### Docker Container Execution

```bash
# Run aider-lint-fixer in a container
docker run --rm \
  -v $(pwd):/workspace \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e AIDER_LINT_PROFILE=production \
  aider-lint-fixer:latest \
  aider-lint-fixer --path /workspace --auto-fix

# For RHEL environments
podman run --rm \
  -v $(pwd):/workspace:Z \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  your-registry.redhat.com/aider-lint-fixer-rhel9:latest \
  aider-lint-fixer --path /workspace --check-only
```

### Kubernetes Job for Batch Processing

```yaml
# k8s/lint-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: aider-lint-batch-job
spec:
  template:
    spec:
      containers:
      - name: aider-lint-fixer
        image: aider-lint-fixer:v1.0.0
        command: ["aider-lint-fixer"]
        args: ["--path", "/workspace", "--auto-fix", "--profile", "batch"]
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: aider-lint-secrets
              key: openai-api-key
        volumeMounts:
        - name: source-code
          mountPath: /workspace
        - name: config
          mountPath: /etc/aider-lint
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: source-code
        persistentVolumeClaim:
          claimName: source-code-pvc
      - name: config
        configMap:
          name: aider-lint-config
      restartPolicy: OnFailure
  backoffLimit: 3
```

### OpenShift Job (RHEL Enterprise)

```yaml
# openshift/lint-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: aider-lint-enterprise-job
spec:
  template:
    spec:
      containers:
      - name: aider-lint-fixer
        image: your-registry.redhat.com/aider-lint-fixer-rhel9:latest
        command: ["aider-lint-fixer"]
        args: ["--path", "/workspace", "--profile", "enterprise"]
        securityContext:
          runAsNonRoot: true
          runAsUser: 1001
          allowPrivilegeEscalation: false
        env:
        - name: AIDER_LINT_PROFILE
          value: "enterprise"
        volumeMounts:
        - name: source-code
          mountPath: /workspace
      volumes:
      - name: source-code
        persistentVolumeClaim:
          claimName: enterprise-code-pvc
      restartPolicy: Never
```

## Developer Workstation Setup

### Direct Installation

```bash
# Install via pip
pip install aider-lint-fixer

# Install from source
git clone https://github.com/your-org/aider-lint-fixer.git
cd aider-lint-fixer
pip install -e .

# Verify installation
aider-lint-fixer --version
```

### Configuration for Development Teams

```bash
# Create team configuration
mkdir -p ~/.config/aider-lint-fixer
cat > ~/.config/aider-lint-fixer/config.yaml << EOF
profile: development
linters:
  python: [flake8, pylint, mypy]
  javascript: [eslint, prettier]
  ansible: [ansible-lint]
ai_integration:
  enabled: true
  model: gpt-4
  max_tokens: 2000
logging:
  level: INFO
  file: ~/.local/share/aider-lint-fixer/logs/aider-lint.log
EOF

# Set up environment variables
echo 'export OPENAI_API_KEY="your-api-key"' >> ~/.bashrc
echo 'export AIDER_LINT_CONFIG="~/.config/aider-lint-fixer/config.yaml"' >> ~/.bashrc
```

## Batch Processing and Scheduled Jobs

### Cron Job for Regular Maintenance

```bash
# Add to crontab (crontab -e)
# Run aider-lint-fixer on main codebase every night at 2 AM
0 2 * * * cd /path/to/codebase && /usr/local/bin/aider-lint-fixer --path . --auto-fix --profile batch >> /var/log/aider-lint-cron.log 2>&1

# Weekly comprehensive scan on Sundays at 3 AM
0 3 * * 0 cd /path/to/codebase && /usr/local/bin/aider-lint-fixer --path . --comprehensive --profile batch >> /var/log/aider-lint-weekly.log 2>&1
```

### Systemd Service for Enterprise

```ini
# /etc/systemd/system/aider-lint-batch.service
[Unit]
Description=Aider Lint Fixer Batch Processing
After=network.target

[Service]
Type=oneshot
User=aider-lint
Group=aider-lint
WorkingDirectory=/opt/codebase
Environment=AIDER_LINT_PROFILE=enterprise
Environment=OPENAI_API_KEY_FILE=/etc/aider-lint/api-key
ExecStart=/usr/local/bin/aider-lint-fixer --path /opt/codebase --auto-fix --profile enterprise
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/aider-lint-batch.timer
[Unit]
Description=Run Aider Lint Fixer Batch Processing
Requires=aider-lint-batch.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
# Enable and start the timer
sudo systemctl enable aider-lint-batch.timer
sudo systemctl start aider-lint-batch.timer
```

## Verification and Testing

### CLI Tool Verification

```bash
#!/bin/bash
# scripts/verify-deployment.sh

echo "Verifying aider-lint-fixer deployment..."

# Check installation
if command -v aider-lint-fixer &> /dev/null; then
    echo "✓ aider-lint-fixer is installed"
    aider-lint-fixer --version
else
    echo "✗ aider-lint-fixer not found in PATH"
    exit 1
fi

# Test basic functionality
echo "Testing basic linting functionality..."
if aider-lint-fixer --help &> /dev/null; then
    echo "✓ Help command works"
else
    echo "✗ Help command failed"
    exit 1
fi

# Test configuration loading
if aider-lint-fixer --check-config &> /dev/null; then
    echo "✓ Configuration loads successfully"
else
    echo "✗ Configuration loading failed"
    exit 1
fi

# Test AI integration (if API key available)
if [[ -n "$OPENAI_API_KEY" ]]; then
    echo "Testing AI integration..."
    if aider-lint-fixer --test-ai &> /dev/null; then
        echo "✓ AI integration working"
    else
        echo "⚠ AI integration test failed (check API key)"
    fi
fi

echo "Deployment verification complete!"
```

### Performance Testing

```bash
#!/bin/bash
# scripts/performance-test.sh

CODEBASE_PATH="/path/to/test/codebase"
ITERATIONS=5

echo "Running performance tests..."

for i in $(seq 1 $ITERATIONS); do
    echo "Iteration $i/$ITERATIONS"
    
    start_time=$(date +%s)
    aider-lint-fixer --path "$CODEBASE_PATH" --check-only --profile performance
    end_time=$(date +%s)
    
    duration=$((end_time - start_time))
    echo "Duration: ${duration}s"
done
```

## Related Guides

- [Deploy to Production](./deploy-to-production.md) - Production deployment strategies
- [Configure Linters](./configure-linters.md) - Configuration management
- [Debug Common Issues](./how-to-debug-common-issues.md) - Troubleshooting deployment issues
- [Container Architecture](../explanation/container-architecture.md) - Container strategy overview
