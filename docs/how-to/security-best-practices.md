# Security Best Practices

This guide outlines security best practices when using aider-lint-fixer in development and production environments.

## Code Security

### Secure Coding Practices

1. **Input Validation**
   - Validate all external inputs
   - Sanitize file paths and names
   - Check file permissions before processing

2. **Error Handling**
   - Don't expose sensitive information in error messages
   - Log security events appropriately
   - Implement proper exception handling

### Static Analysis Security

```bash
# Run security-focused linters
python -m aider_lint_fixer --enable-security-checks

# Use bandit for security analysis
pip install bandit
bandit -r aider_lint_fixer/
```

## API Key Security

### Environment Variables

```bash
# Never commit API keys to repository
export OPENAI_API_KEY=your_key_here
export ANTHROPIC_API_KEY=your_key_here

# Use .env files (add to .gitignore)
echo "OPENAI_API_KEY=your_key" >> .env
echo ".env" >> .gitignore
```

### Key Rotation

```bash
# Regularly rotate API keys
# Update environment variables
# Test key validity
python -c "import openai; print('Key valid')"
```

## File System Security

### Secure File Handling

1. **Path Traversal Prevention**
   ```python
   import os.path
   
   # Validate paths
   safe_path = os.path.abspath(user_path)
   if not safe_path.startswith(allowed_directory):
       raise SecurityError("Path traversal attempt")
   ```

2. **File Permissions**
   ```bash
   # Set restrictive permissions
   chmod 600 config/secrets.yml
   chmod 755 scripts/
   ```

### Temporary Files

```python
import tempfile
import os

# Use secure temporary files
with tempfile.NamedTemporaryFile(delete=True) as tmp:
    # Process file securely
    pass
```

## Network Security

### HTTPS Usage

```python
# Always use HTTPS for API calls
api_base = "https://api.openai.com/v1"
# Never: http://api.openai.com/v1
```

### Certificate Validation

```python
import requests

# Enable SSL verification
response = requests.get(url, verify=True)
```

## Container Security

### Docker Security

```dockerfile
# Use non-root user
FROM python:3.11-slim
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Minimal base image
FROM python:3.11-alpine

# Security scanning
RUN apk add --no-cache security-scanner
```

### Container Scanning

```bash
# Scan for vulnerabilities
docker scan aider-lint-fixer:latest

# Use security-focused base images
FROM gcr.io/distroless/python3
```

## CI/CD Security

### GitHub Actions Security

```yaml
name: Secure CI
on: [push, pull_request]
jobs:
  security-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Security Scan
        uses: securecodewarrior/github-action-add-sarif@v1
        
      - name: Secret Scanning
        run: |
          pip install detect-secrets
          detect-secrets scan --all-files
```

### Secret Management

```yaml
# Use GitHub Secrets
env:
  API_KEY: ${{ secrets.OPENAI_API_KEY }}

# Mask sensitive values
run: |
  echo "::add-mask::$API_KEY"
```

## Dependency Security

### Vulnerability Scanning

```bash
# Scan dependencies
pip install safety
safety check

# Check for known vulnerabilities
pip-audit
```

### Dependency Pinning

```txt
# requirements.txt - pin versions
requests==2.28.1
pydantic==1.10.2
click==8.1.3
```

### Regular Updates

```bash
# Update dependencies regularly
pip list --outdated
pip install --upgrade package_name

# Use dependabot for automated updates
```

## Configuration Security

### Secure Configuration

```yaml
# config/security.yml
security:
  enable_audit_logging: true
  max_file_size: 10MB
  allowed_extensions: ['.py', '.js', '.ts']
  blocked_patterns:
    - '*.secret'
    - '*.key'
```

### Environment-Specific Settings

```python
# Different configs for different environments
if os.getenv('ENV') == 'production':
    DEBUG = False
    ALLOWED_HOSTS = ['your-domain.com']
else:
    DEBUG = True
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
```

## Monitoring and Auditing

### Security Logging

```python
import logging

# Security event logging
security_logger = logging.getLogger('security')
security_logger.info(f"User {user} accessed {resource}")
```

### Audit Trails

```bash
# Enable audit logging
export AUDIT_LOG_ENABLED=true
export AUDIT_LOG_LEVEL=INFO
```

## Incident Response

### Security Incident Plan

1. **Detection**: Monitor for security events
2. **Containment**: Isolate affected systems
3. **Eradication**: Remove threats
4. **Recovery**: Restore normal operations
5. **Lessons Learned**: Document and improve

### Emergency Procedures

```bash
# Revoke compromised keys immediately
# Rotate all credentials
# Review access logs
# Update security measures
```

## Compliance

### Data Protection

- Follow GDPR/CCPA requirements
- Implement data retention policies
- Secure data transmission
- Regular security assessments

### Security Standards

- SOC 2 Type II compliance
- ISO 27001 guidelines
- OWASP security practices
- Industry-specific requirements

## Regular Security Tasks

### Weekly
- Review access logs
- Check for security updates
- Scan for new vulnerabilities

### Monthly
- Rotate API keys
- Update dependencies
- Security training review

### Quarterly
- Full security audit
- Penetration testing
- Policy updates
- Risk assessment

## Next Steps

- [Monitor Performance](./monitor-performance.md)
- [Integrate with Aider](./integrate-with-aider.md)
- [Run Tests](./run-tests.md)
