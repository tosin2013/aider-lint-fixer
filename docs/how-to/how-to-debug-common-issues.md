# How to Debug Common Issues

This guide helps you troubleshoot and debug common issues in aider-lint-fixer, covering Python debugging, linter problems, container issues, and AI integration failures.

## Debugging Tools

### Python Debugging

**1. Built-in Python Debugger (pdb)**
```bash
# Add breakpoint in code
import pdb; pdb.set_trace()

# Run with debugger
python -m pdb aider_lint_fixer/__main__.py --file test.py
```

**2. VS Code Python Debugging**
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug aider-lint-fixer",
            "type": "python",
            "request": "launch",
            "module": "aider_lint_fixer",
            "args": ["--file", "test.py", "--linters", "flake8,pylint"],
            "console": "integratedTerminal"
        }
    ]
}
```

### Logging and Diagnostics

**Enable Verbose Logging**
```bash
# Environment variable
export AIDER_LINT_LOG_LEVEL=DEBUG

# Command line
aider-lint-fixer --log-level DEBUG --file test.py

# Python logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Structured Logging Output**
```bash
# JSON format for analysis
aider-lint-fixer --log-format json --file test.py > debug.log
```

## Common Issues and Solutions

### Issue: Linter Not Found

**Symptoms**: "Linter 'flake8' not found" or similar errors

**Solutions**:
```bash
# Check Python linters
pip list | grep -E "(flake8|pylint|mypy)"

# Install missing linters
pip install flake8 pylint mypy

# Check Node.js linters
npm list -g | grep -E "(eslint|prettier|jshint)"

# Install missing Node.js linters
npm install -g eslint prettier jshint

# Verify PATH
which flake8
which eslint
```

### Issue: Configuration Not Found

**Symptoms**: "Configuration file not found" or default settings used

**Solutions**:
```bash
# Check config file locations
ls -la .aider-lint.yaml
ls -la ~/.aider-lint.yaml
ls -la /etc/aider-lint/config.yaml

# Validate config syntax
python -c "import yaml; yaml.safe_load(open('.aider-lint.yaml'))"

# Use explicit config path
aider-lint-fixer --config /path/to/config.yaml --file test.py

# Debug config loading
aider-lint-fixer --log-level DEBUG --file test.py 2>&1 | grep -i config
```

### Issue: Permission Errors

**Symptoms**: "Permission denied" when accessing files or running linters

**Solutions**:
```bash
# Check file permissions
ls -la target_file.py

# Fix file permissions
chmod 644 target_file.py

# Check directory permissions
ls -ld /path/to/project

# Container permission issues (SELinux)
# For RHEL/CentOS with SELinux
ls -Z /path/to/project
podman run -v /path/to/project:/workspace:ro,Z aider-lint-fixer

# Docker permission mapping
docker run -v /path/to/project:/workspace:ro \
  --user $(id -u):$(id -g) aider-lint-fixer
```

### Issue: AI Integration Failures

**Symptoms**: "AI integration failed" or timeout errors

**Solutions**:
```bash
# Check API key
echo $OPENAI_API_KEY

# Test aider.chat directly
aider --help

# Check network connectivity
curl -I https://api.openai.com/v1/models

# Debug AI integration
aider-lint-fixer --log-level DEBUG --ai-enabled --file test.py

# Use fallback without AI
aider-lint-fixer --no-ai --file test.py
```

### Issue: Container Runtime Problems

**Symptoms**: Container fails to start or crashes

**Solutions**:
```bash
# Check container logs
docker logs aider-lint-fixer-container

# Run interactively for debugging
docker run -it --entrypoint /bin/bash aider-lint-fixer:latest

# Check container resource usage
docker stats aider-lint-fixer-container

# Verify container image
docker inspect aider-lint-fixer:latest

# Test with minimal command
docker run --rm aider-lint-fixer:latest --version
```

## Performance Debugging

### Slow Linting Performance

**Identify Bottlenecks**
```bash
# Profile linter execution
time aider-lint-fixer --file large_file.py --linters flake8

# Test individual linters
time flake8 large_file.py
time pylint large_file.py
time mypy large_file.py

# Check concurrent execution
aider-lint-fixer --concurrency 1 --file large_file.py
aider-lint-fixer --concurrency 4 --file large_file.py
```

**Optimize Performance**
```bash
# Use faster linters only
aider-lint-fixer --linters flake8 --file large_file.py

# Enable caching
export AIDER_LINT_CACHE_ENABLED=true

# Increase timeout for large files
aider-lint-fixer --timeout 600 --file large_file.py
```

### Memory Issues

**Monitor Memory Usage**
```bash
# Python memory profiling
pip install memory-profiler
python -m memory_profiler aider_lint_fixer/__main__.py

# Container memory monitoring
docker stats --no-stream aider-lint-fixer-container

# Check for memory leaks
valgrind --tool=memcheck python -m aider_lint_fixer --file test.py
```

## Environment-Specific Debugging

### RHEL/CentOS Issues

**SELinux Problems**
```bash
# Check SELinux status
getenforce

# View SELinux denials
ausearch -m AVC -ts recent

# Temporarily disable SELinux (not recommended for production)
setenforce 0

# Fix SELinux contexts
restorecon -R /path/to/project
```

**Subscription Manager Issues**
```bash
# Check subscription status
subscription-manager status

# View available repositories
subscription-manager repos --list

# Enable required repositories
subscription-manager repos --enable rhel-9-for-x86_64-appstream-rpms
```

### macOS Issues

**Homebrew Path Problems**
```bash
# Check Homebrew installation
brew doctor

# Fix PATH issues
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Reinstall Python tools
brew reinstall python@3.11
pip3 install --upgrade aider-lint-fixer
```

### Ubuntu Issues

**Package Manager Conflicts**
```bash
# Check for conflicting packages
apt list --installed | grep -E "(python|node)"

# Clean package cache
sudo apt clean
sudo apt autoremove

# Reinstall Python
sudo apt update
sudo apt install python3.11 python3.11-pip
```

## Advanced Debugging Techniques

### Network Debugging

**API Connectivity Issues**
```bash
# Test network connectivity
ping api.openai.com
curl -v https://api.openai.com/v1/models

# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Test with different DNS
nslookup api.openai.com 8.8.8.8
```

### Container Network Debugging

```bash
# Check container networking
docker network ls
docker network inspect bridge

# Test container connectivity
docker run --rm --network host aider-lint-fixer:latest --version

# Debug DNS resolution in container
docker run --rm -it aider-lint-fixer:latest nslookup api.openai.com
```

### File System Debugging

**Permission and Access Issues**
```bash
# Check file system permissions
namei -l /path/to/file

# Test file access
python -c "open('/path/to/file', 'r').read()"

# Check disk space
df -h /path/to/project

# Monitor file access
strace -e trace=file python -m aider_lint_fixer --file test.py
```

## Collecting Debug Information

### System Information

```bash
# Create debug report
cat > debug_report.txt << EOF
=== System Information ===
OS: $(uname -a)
Python: $(python --version)
Node.js: $(node --version)
Docker: $(docker --version)
Podman: $(podman --version)

=== Package Versions ===
$(pip list | grep -E "(aider|flake8|pylint|mypy)")
$(npm list -g | grep -E "(eslint|prettier|jshint)")

=== Configuration ===
$(cat .aider-lint.yaml)

=== Environment Variables ===
$(env | grep -E "(AIDER|OPENAI|PATH)")

=== Recent Logs ===
$(tail -50 /var/log/aider-lint/application.log)
EOF
```

### Container Debug Information

```bash
# Container inspection
docker inspect aider-lint-fixer:latest > container_debug.json

# Container logs
docker logs aider-lint-fixer-container > container_logs.txt

# Container resource usage
docker stats --no-stream > container_stats.txt
```

## Getting Help

### Self-Service Resources

1. **Check FAQ**: [Reference FAQ](../reference/faq.md)
2. **Review ADRs**: [Architectural Decisions](../adrs/)
3. **Configuration Guide**: [Configure Linters](./configure-linters.md)

### Community Support

```bash
# Search existing issues
# GitHub: https://github.com/your-org/aider-lint-fixer/issues

# Create bug report with debug information
# Include:
# - System information
# - Configuration files
# - Error messages and logs
# - Steps to reproduce
```

### Enterprise Support

For RHEL enterprise customers:
- Red Hat Support Portal
- OpenShift documentation
- Enterprise container registry support

## Prevention Best Practices

### Regular Maintenance

```bash
# Update dependencies regularly
pip list --outdated
npm outdated -g

# Clean up old containers
docker system prune

# Monitor disk space
df -h
```

### Configuration Validation

```bash
# Validate configuration on changes
aider-lint-fixer --validate-config

# Test configuration in development
aider-lint-fixer --config test-config.yaml --dry-run
```

### Monitoring and Alerting

```bash
# Set up log monitoring
tail -f /var/log/aider-lint/application.log | grep ERROR

# Container health checks
docker healthcheck --interval=30s --timeout=3s \
  CMD aider-lint-fixer --health-check
```
