# Red Hat Developer Guide

This guide provides Red Hat developers with optimized workflows for using aider-lint-fixer in RHEL environments, leveraging native Red Hat tooling and enterprise features.

## Prerequisites

### Required Software
- **RHEL 9 or RHEL 10** (recommended)
- **Podman** (native Red Hat container tool)
- **Active Red Hat subscription**
- **Python 3.9+** (RHEL 9) or **Python 3.12+** (RHEL 10)
- **Git**

### Installation

```bash
# Install Podman (if not already installed)
sudo dnf install -y podman

# Install Python development tools
sudo dnf install -y python3-pip python3-venv

# Clone aider-lint-fixer
git clone https://github.com/your-org/aider-lint-fixer.git
cd aider-lint-fixer
```

## Quick Start

### Container-Based Development (Recommended)

```bash
# Build your RHEL-optimized container
./scripts/containers/build-rhel9.sh --validate
# or for RHEL 10
./scripts/containers/build-rhel10.sh --validate --security-scan

# Run on your Ansible project
podman run --rm -v $(pwd):/workspace:ro \
  my-company/aider-lint-fixer:rhel9 \
  --linters ansible-lint,flake8 --dry-run
```

### Native Installation

```bash
# Create virtual environment
python3 -m venv ~/.venv/aider-lint-fixer
source ~/.venv/aider-lint-fixer/bin/activate

# Install with RHEL-specific dependencies
pip install -e .

# Install ansible-core (requires subscription)
sudo dnf install -y ansible-core

# Verify installation
aider-lint-fixer --version
```

## RHEL-Specific Features

### Subscription Management Integration

```bash
# Check subscription status
subscription-manager status

# Register system if needed
sudo subscription-manager register --username=your-username

# Enable required repositories
sudo subscription-manager repos --enable=rhel-9-for-x86_64-appstream-rpms
```

### SELinux Considerations

```bash
# Check SELinux status
sestatus

# If using containers with SELinux enforcing
podman run --rm -v $(pwd):/workspace:ro,Z \
  my-company/aider-lint-fixer:rhel9 \
  --linters ansible-lint

# For persistent volumes
podman run --rm -v aider-cache:/tmp/aider:Z \
  my-company/aider-lint-fixer:rhel9
```

### Systemd Integration

Create a systemd service for automated linting:

```bash
# Create service file
sudo tee /etc/systemd/system/aider-lint-watcher.service > /dev/null <<EOF
[Unit]
Description=Aider Lint Watcher
After=network.target

[Service]
Type=simple
User=developer
WorkingDirectory=/home/developer/projects
ExecStart=/usr/bin/podman run --rm -v /home/developer/projects:/workspace:ro my-company/aider-lint-fixer:rhel9 --watch
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable aider-lint-watcher
sudo systemctl start aider-lint-watcher
```

## Development Workflows

### Enterprise Ansible Development

```bash
# Lint Ansible collections with RHEL-specific rules
podman run --rm -v $(pwd):/workspace:ro \
  my-company/aider-lint-fixer:rhel9 \
  --linters ansible-lint \
  --ansible-config /workspace/ansible.cfg \
  --profile production

# Generate compliance reports
podman run --rm -v $(pwd):/workspace:ro \
  -v $(pwd)/reports:/reports \
  my-company/aider-lint-fixer:rhel9 \
  --output-format junit \
  --output-file /reports/compliance.xml
```

### Red Hat Certified Content

```bash
# Validate against Red Hat certification requirements
podman run --rm -v $(pwd):/workspace:ro \
  my-company/aider-lint-fixer:rhel9 \
  --linters ansible-lint \
  --profile redhat-certified \
  --strict
```

### Multi-Architecture Support

```bash
# Build for multiple architectures
podman build --platform linux/amd64,linux/arm64 \
  -f Dockerfile.rhel9 \
  -t my-company/aider-lint-fixer:rhel9-multi .

# Run on ARM-based RHEL systems
podman run --rm -v $(pwd):/workspace:ro \
  my-company/aider-lint-fixer:rhel9-multi
```

## Container Registry Integration

### Red Hat Quay Integration

```bash
# Login to Red Hat Quay
podman login quay.io

# Build and push to enterprise registry
./scripts/containers/build-rhel9.sh \
  --registry quay.io \
  --name your-org/aider-lint-fixer \
  --tag v1.0-rhel9

podman push quay.io/your-org/aider-lint-fixer:v1.0-rhel9
```

### OpenShift Integration

```yaml
# openshift-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aider-lint-fixer
spec:
  replicas: 1
  selector:
    matchLabels:
      app: aider-lint-fixer
  template:
    metadata:
      labels:
        app: aider-lint-fixer
    spec:
      containers:
      - name: aider-lint-fixer
        image: quay.io/your-org/aider-lint-fixer:rhel9
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        securityContext:
          runAsNonRoot: true
          runAsUser: 1001
```

## Performance Optimization

### RHEL 10 Advantages

```bash
# Leverage RHEL 10 performance improvements
./scripts/containers/build-rhel10.sh --validate

# Compare performance between RHEL 9 and 10
time podman run --rm -v $(pwd):/workspace:ro \
  my-company/aider-lint-fixer:rhel9 --benchmark

time podman run --rm -v $(pwd):/workspace:ro \
  my-company/aider-lint-fixer:rhel10 --benchmark
```

### Resource Management

```bash
# Set container resource limits
podman run --rm \
  --memory=1g \
  --cpus=2 \
  -v $(pwd):/workspace:ro \
  my-company/aider-lint-fixer:rhel9
```

## Security Best Practices

### Container Security

```bash
# Run security scan on your container
podman run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image my-company/aider-lint-fixer:rhel9

# Use rootless containers (default with Podman)
podman run --rm --user 1001 \
  -v $(pwd):/workspace:ro \
  my-company/aider-lint-fixer:rhel9
```

### Credential Management

```bash
# Use Red Hat Vault for secrets
export RHEL_USERNAME=$(vault kv get -field=username secret/rhel-subscription)
export RHEL_PASSWORD=$(vault kv get -field=password secret/rhel-subscription)

# Build with secure credentials
./scripts/containers/build-rhel9.sh
```

### Network Security

```bash
# Run with restricted network access
podman run --rm --network=none \
  -v $(pwd):/workspace:ro \
  my-company/aider-lint-fixer:rhel9 \
  --offline-mode
```

## Troubleshooting

### Common RHEL Issues

**Subscription Problems**:
```bash
# Check subscription status
subscription-manager status

# Refresh subscriptions
sudo subscription-manager refresh

# Re-register if needed
sudo subscription-manager unregister
sudo subscription-manager register --username=your-username
```

**SELinux Denials**:
```bash
# Check for SELinux denials
sudo ausearch -m AVC -ts recent

# Generate SELinux policy if needed
sudo audit2allow -a -M aider-lint-fixer
sudo semodule -i aider-lint-fixer.pp
```

**Podman Issues**:
```bash
# Reset Podman if needed
podman system reset

# Check Podman configuration
podman info

# Update Podman
sudo dnf update -y podman
```

## CI/CD Integration

### Red Hat OpenShift Pipelines

```yaml
# .tekton/pipeline.yaml
apiVersion: tekton.dev/v1beta1
kind: Pipeline
metadata:
  name: aider-lint-pipeline
spec:
  tasks:
  - name: lint-ansible
    taskRef:
      name: aider-lint-task
    params:
    - name: image
      value: quay.io/your-org/aider-lint-fixer:rhel9
    - name: linters
      value: "ansible-lint,flake8"
```

### Red Hat Satellite Integration

```bash
# Register with Satellite
sudo subscription-manager register \
  --org="your-org" \
  --activationkey="your-key" \
  --serverurl=https://satellite.company.com

# Use Satellite-managed repositories
sudo dnf config-manager --enable satellite-tools-6.11-for-rhel-9-x86_64-rpms
```

## Enterprise Features

### Compliance Reporting

```bash
# Generate SCAP compliance reports
podman run --rm -v $(pwd):/workspace:ro \
  -v $(pwd)/compliance:/compliance \
  my-company/aider-lint-fixer:rhel9 \
  --compliance-scan \
  --output-dir /compliance
```

### Audit Logging

```bash
# Enable audit logging
podman run --rm \
  --log-driver=journald \
  --log-opt tag="aider-lint-fixer" \
  -v $(pwd):/workspace:ro \
  my-company/aider-lint-fixer:rhel9

# View logs
journalctl -t aider-lint-fixer
```

## Best Practices

### Container Management
- Use Podman for rootless, daemonless containers
- Leverage Red Hat UBI base images for compliance
- Implement proper resource limits and security contexts
- Use Red Hat Quay for enterprise container registry

### Development Workflow
- Build RHEL-specific containers with your subscription
- Use version-specific containers (RHEL 9 vs RHEL 10)
- Implement proper SELinux labeling for volumes
- Follow Red Hat security guidelines

### Performance
- Prefer RHEL 10 for better performance and security
- Use multi-stage builds to minimize image size
- Implement proper caching strategies
- Monitor resource usage with Red Hat Insights

## Related Documentation

- [RHEL Container Builds](rhel-container-builds.md)
- [Container Architecture](../explanation/container-architecture.md)
- [ADR 0009: RHEL Container Build Requirements](../adrs/0009-rhel-container-build-requirements.md)
- [Production Deployment](deploy-to-production.md)

## Support Resources

- **Red Hat Customer Portal**: https://access.redhat.com
- **Red Hat Developer Program**: https://developers.redhat.com
- **OpenShift Documentation**: https://docs.openshift.com
- **Podman Documentation**: https://docs.podman.io
