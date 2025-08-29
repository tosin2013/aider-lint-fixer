# macOS and Ubuntu Developer Guide

This guide provides macOS and Ubuntu developers with streamlined workflows for using aider-lint-fixer, optimized for modern development environments with the latest tools and features.

## Prerequisites

### macOS Requirements
- **macOS 12+** (Monterey or later)
- **Docker Desktop** or **Homebrew + Docker**
- **Python 3.11+** (via Homebrew recommended)
- **Git**
- **Xcode Command Line Tools**

### Ubuntu Requirements
- **Ubuntu 20.04 LTS+** (22.04 LTS recommended)
- **Docker** or **Podman**
- **Python 3.11+**
- **Git**
- **Build essentials**

## Installation

### macOS Setup

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 git docker

# Start Docker Desktop or install Docker via Homebrew
brew install --cask docker
# OR
brew install docker docker-compose

# Clone aider-lint-fixer
git clone https://github.com/your-org/aider-lint-fixer.git
cd aider-lint-fixer
```

### Ubuntu Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip git curl

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Clone aider-lint-fixer
git clone https://github.com/your-org/aider-lint-fixer.git
cd aider-lint-fixer
```

## Quick Start

### Container-Based Development (Recommended)

```bash
# Build the default container (includes latest ansible-lint)
docker build -t aider-lint-fixer:latest .

# Run on your project
docker run --rm -v $(pwd):/workspace:ro \
  aider-lint-fixer:latest \
  --linters flake8,ansible-lint,eslint --dry-run

# Interactive mode
docker run --rm -it -v $(pwd):/workspace \
  aider-lint-fixer:latest \
  --interactive
```

### Native Installation

```bash
# Create virtual environment
python3.11 -m venv ~/.venv/aider-lint-fixer
source ~/.venv/aider-lint-fixer/bin/activate

# Install with latest dependencies
pip install -e .

# Install additional linters
pip install ansible-lint flake8 pylint mypy
npm install -g eslint jshint prettier

# Verify installation
aider-lint-fixer --version
```

## Development Workflows

### Modern Ansible Development

```bash
# Use latest ansible-lint with cutting-edge rules
docker run --rm -v $(pwd):/workspace:ro \
  aider-lint-fixer:latest \
  --linters ansible-lint \
  --profile modern \
  --enable-experimental

# Auto-fix common issues
docker run --rm -v $(pwd):/workspace \
  aider-lint-fixer:latest \
  --linters ansible-lint \
  --auto-fix \
  --backup
```

### Multi-Language Projects

```bash
# Lint Python, JavaScript, and Ansible in one pass
docker run --rm -v $(pwd):/workspace:ro \
  aider-lint-fixer:latest \
  --linters flake8,pylint,mypy,eslint,ansible-lint \
  --parallel

# Generate comprehensive report
docker run --rm -v $(pwd):/workspace:ro \
  -v $(pwd)/reports:/reports \
  aider-lint-fixer:latest \
  --output-format html \
  --output-file /reports/lint-report.html
```

### VS Code Integration

Create `.vscode/tasks.json`:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Aider Lint Check",
            "type": "shell",
            "command": "docker",
            "args": [
                "run", "--rm", "-v", "${workspaceFolder}:/workspace:ro",
                "aider-lint-fixer:latest",
                "--linters", "flake8,ansible-lint,eslint",
                "--format", "vscode"
            ],
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "problemMatcher": "$eslint-stylish"
        },
        {
            "label": "Aider Lint Fix",
            "type": "shell",
            "command": "docker",
            "args": [
                "run", "--rm", "-v", "${workspaceFolder}:/workspace",
                "aider-lint-fixer:latest",
                "--auto-fix",
                "--backup"
            ],
            "group": "build"
        }
    ]
}
```

### GitHub Actions Integration

Create `.github/workflows/lint.yml`:

```yaml
name: Lint Code

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  lint:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Build aider-lint-fixer
      run: docker build -t aider-lint-fixer:latest .
    
    - name: Run linting
      run: |
        docker run --rm -v ${{ github.workspace }}:/workspace:ro \
          aider-lint-fixer:latest \
          --linters flake8,ansible-lint,eslint \
          --output-format github-actions
    
    - name: Upload lint results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: lint-results
        path: lint-results.json
```

## Platform-Specific Features

### macOS Optimizations

```bash
# Use macOS-specific paths
docker run --rm \
  -v $(pwd):/workspace:ro \
  -v ~/.ansible:/home/aider/.ansible:ro \
  -v ~/.ssh:/home/aider/.ssh:ro \
  aider-lint-fixer:latest

# Leverage macOS filesystem performance
docker run --rm \
  -v $(pwd):/workspace:ro,cached \
  aider-lint-fixer:latest \
  --cache-dir /tmp/aider-cache
```

### Ubuntu Optimizations

```bash
# Use Ubuntu-specific package versions
docker run --rm \
  -v $(pwd):/workspace:ro \
  -v ~/.cache/pip:/home/aider/.cache/pip \
  aider-lint-fixer:latest

# Leverage systemd for service management
sudo tee /etc/systemd/user/aider-lint-watcher.service > /dev/null <<EOF
[Unit]
Description=Aider Lint File Watcher
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/docker run --rm -v %h/projects:/workspace:ro aider-lint-fixer:latest --watch
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

systemctl --user enable aider-lint-watcher
systemctl --user start aider-lint-watcher
```

## Performance Optimization

### Container Performance

```bash
# Use multi-stage builds for faster rebuilds
docker build --target development -t aider-lint-fixer:dev .

# Leverage BuildKit for better caching
DOCKER_BUILDKIT=1 docker build -t aider-lint-fixer:latest .

# Use bind mounts for development
docker run --rm \
  --mount type=bind,source=$(pwd),target=/workspace \
  aider-lint-fixer:latest \
  --watch
```

### Resource Management

```bash
# Optimize for development machine
docker run --rm \
  --memory=2g \
  --cpus=4 \
  -v $(pwd):/workspace:ro \
  aider-lint-fixer:latest \
  --parallel --jobs=4
```

## IDE Integration

### PyCharm/IntelliJ Integration

```bash
# Configure external tool
# Program: docker
# Arguments: run --rm -v $FileDir$:/workspace:ro aider-lint-fixer:latest --file /workspace/$FileName$
# Working directory: $ProjectFileDir$
```

### Sublime Text Integration

Create `aider-lint.sublime-build`:

```json
{
    "shell_cmd": "docker run --rm -v $folder:/workspace:ro aider-lint-fixer:latest --file /workspace/$file_name",
    "file_regex": "^(.+):([0-9]+):([0-9]+): (.+)$",
    "selector": "source.python, source.yaml, source.js"
}
```

### Vim/Neovim Integration

Add to `.vimrc` or `init.vim`:

```vim
" Aider Lint integration
function! AiderLint()
    let l:current_file = expand('%:p')
    let l:workspace = getcwd()
    let l:cmd = 'docker run --rm -v ' . l:workspace . ':/workspace:ro aider-lint-fixer:latest --file /workspace/' . expand('%')
    let l:output = system(l:cmd)
    echo l:output
endfunction

command! AiderLint call AiderLint()
nnoremap <leader>al :AiderLint<CR>
```

## Testing and Quality Assurance

### Pre-commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: aider-lint-fixer
        name: Aider Lint Fixer
        entry: docker run --rm -v $(pwd):/workspace:ro aider-lint-fixer:latest
        language: system
        files: \.(py|yml|yaml|js|ts)$
        pass_filenames: false
```

### Test Integration

```bash
# Run tests with linting
docker run --rm -v $(pwd):/workspace:ro \
  aider-lint-fixer:latest \
  --test-mode \
  --coverage

# Generate test reports
docker run --rm -v $(pwd):/workspace:ro \
  -v $(pwd)/test-results:/test-results \
  aider-lint-fixer:latest \
  --output-format junit \
  --output-file /test-results/lint.xml
```

## Container Registry Integration

### Docker Hub

```bash
# Build and tag for Docker Hub
docker build -t your-username/aider-lint-fixer:latest .
docker push your-username/aider-lint-fixer:latest

# Use from Docker Hub
docker run --rm -v $(pwd):/workspace:ro \
  your-username/aider-lint-fixer:latest
```

### GitHub Container Registry

```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u your-username --password-stdin

# Build and push
docker build -t ghcr.io/your-username/aider-lint-fixer:latest .
docker push ghcr.io/your-username/aider-lint-fixer:latest
```

## Troubleshooting

### macOS Issues

**Docker Desktop Problems**:
```bash
# Reset Docker Desktop
docker system prune -a
# Restart Docker Desktop from Applications

# Check Docker daemon
docker info
```

**Permission Issues**:
```bash
# Fix volume mount permissions
docker run --rm -v $(pwd):/workspace:rw \
  --user $(id -u):$(id -g) \
  aider-lint-fixer:latest
```

### Ubuntu Issues

**Docker Permission Denied**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or use sudo temporarily
sudo docker run --rm -v $(pwd):/workspace:ro aider-lint-fixer:latest
```

**Python Version Issues**:
```bash
# Install specific Python version
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Use specific Python version
python3.11 -m venv ~/.venv/aider-lint-fixer
```

### Common Container Issues

**Out of Space**:
```bash
# Clean up Docker
docker system prune -a

# Remove unused images
docker image prune -a
```

**Slow Performance**:
```bash
# Use cached volumes
docker run --rm -v $(pwd):/workspace:ro,cached aider-lint-fixer:latest

# Increase Docker resources in Docker Desktop settings
```

## Advanced Configuration

### Custom Configuration

Create `aider-lint-config.yaml`:

```yaml
linters:
  - flake8
  - ansible-lint
  - eslint
  - mypy

profiles:
  development:
    strict: false
    auto_fix: true
    parallel: true
  
  ci:
    strict: true
    output_format: "junit"
    fail_fast: true

output:
  format: "json"
  file: "lint-results.json"
```

### Environment Variables

```bash
# Set default configuration
export AIDER_LINT_CONFIG=./aider-lint-config.yaml
export AIDER_LINT_PROFILE=development
export AIDER_LINT_CACHE_DIR=~/.cache/aider-lint-fixer

# Run with environment
docker run --rm \
  -v $(pwd):/workspace:ro \
  -e AIDER_LINT_PROFILE=ci \
  aider-lint-fixer:latest
```

## Best Practices

### Development Workflow
- Use the default container for latest features and tools
- Implement pre-commit hooks for consistent code quality
- Integrate with your IDE for real-time feedback
- Use parallel processing for large codebases

### Container Management
- Leverage Docker layer caching for faster builds
- Use bind mounts for development, volumes for production
- Implement proper resource limits for CI/CD
- Keep containers updated with latest security patches

### Performance
- Use cached volume mounts on macOS
- Implement parallel linting for multi-file projects
- Optimize container resource allocation
- Use local caching for dependencies

## Related Documentation

- [Container Deployment Tutorial](../tutorials/container-deployment.md)
- [Container Architecture](../explanation/container-architecture.md)
- [ADR 0008: Deployment Environments](../adrs/0008-deployment-environments.md)
- [API Documentation](../reference/api-documentation.md)

## Community Resources

- **GitHub Repository**: https://github.com/your-org/aider-lint-fixer
- **Docker Hub**: https://hub.docker.com/r/your-org/aider-lint-fixer
- **Documentation**: https://aider-lint-fixer.readthedocs.io
- **Community Forum**: https://github.com/your-org/aider-lint-fixer/discussions
