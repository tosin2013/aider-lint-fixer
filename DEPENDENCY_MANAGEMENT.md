# 🔒 Dependency Management Guide

This document explains how to use the dependency lock files for reproducible builds in aider-lint-fixer.

## 📋 Overview

The project uses **pip-tools** for dependency management with locked versions to ensure reproducible builds across different environments.

## 📁 Lock Files

### Runtime Dependencies
- **`requirements-lock.txt`** - Locked runtime dependencies with exact versions and hashes
- **`requirements.in`** - Source file for runtime dependencies (used to generate lock file)

### Development Dependencies  
- **`requirements-dev-lock.txt`** - Locked development dependencies with exact versions and hashes
- **`requirements-dev.in`** - Source file for development dependencies (used to generate lock file)

## 🚀 Quick Start

### For Production/Runtime
```bash
# Install exact locked runtime dependencies
pip install -r requirements-lock.txt

# Install the package in development mode
pip install -e .
```

### For Development
```bash
# Install both runtime and development dependencies
pip install -r requirements-lock.txt
pip install -r requirements-dev-lock.txt
pip install -e .
```

## 🔧 Updating Dependencies

### Adding New Dependencies

1. **Add to the appropriate source file**:
   - Runtime: Add to `requirements.in`
   - Development: Add to `requirements-dev.in`

2. **Regenerate lock files**:
   ```bash
   # Install pip-tools if not already installed
   pip install pip-tools
   
   # Regenerate runtime lock file
   pip-compile requirements.in --output-file=requirements-lock.txt --generate-hashes
   
   # Regenerate development lock file  
   pip-compile requirements-dev.in --output-file=requirements-dev-lock.txt --generate-hashes
   ```

### Updating Existing Dependencies

```bash
# Update all dependencies to latest compatible versions
pip-compile --upgrade requirements.in --output-file=requirements-lock.txt --generate-hashes
pip-compile --upgrade requirements-dev.in --output-file=requirements-dev-lock.txt --generate-hashes
```

## 🔄 CI/CD Integration

### GitHub Actions
The CI workflows now use lock files for reproducible builds:

- **`.github/workflows/test-build.yml`** - Uses `requirements-lock.txt` and `requirements-dev-lock.txt`
- **`.github/workflows/pr-check.yml`** - Uses lock files for consistent testing

### Local Development
For consistent local development:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install locked dependencies
pip install -r requirements-lock.txt
pip install -r requirements-dev-lock.txt
pip install -e .
```

## 📊 Benefits of Lock Files

### ✅ Reproducible Builds
- Exact same dependency versions across all environments
- Eliminates "works on my machine" issues
- Consistent CI/CD pipeline results

### 🔒 Security
- SHA256 hashes for all packages
- Protection against supply chain attacks
- Verified package integrity

### 📈 Performance
- Faster CI builds with cached dependencies
- Reduced dependency resolution time
- Predictable build times

## 🛠️ Troubleshooting

### Common Issues

#### "Package not found" errors
- Ensure you're using the correct Python version (3.11+)
- Check that lock files are up to date
- Verify package names in source files

#### Hash mismatches
- Regenerate lock files if packages have been updated
- Check for network issues during installation
- Verify package sources are accessible

#### Version conflicts
- Use `pip-compile --upgrade` to resolve conflicts
- Check for incompatible version ranges in source files
- Ensure all dependencies are compatible with Python 3.11+

### Regenerating Lock Files

If you encounter issues with lock files:

```bash
# Clean install
pip install --upgrade pip pip-tools

# Regenerate from scratch
rm requirements-lock.txt requirements-dev-lock.txt
pip-compile requirements.in --output-file=requirements-lock.txt --generate-hashes
pip-compile requirements-dev.in --output-file=requirements-dev-lock.txt --generate-hashes
```

## 📋 Best Practices

### For Contributors
1. **Always use lock files** for development setup
2. **Update lock files** when adding new dependencies
3. **Test with lock files** before submitting PRs
4. **Document dependency changes** in PR descriptions