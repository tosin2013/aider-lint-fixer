# 🔧 Contributor Version Guide

## 📋 **Overview**

This guide helps contributors understand the supported linter versions for aider-lint-fixer and how to set up their development environment correctly.

## 🎯 **Supported Linter Versions (v1.3.0)**

### **Ansible Linters**
| Linter | Tested Version | Supported Versions | Installation |
|--------|----------------|-------------------|--------------|
| **ansible-lint** | `25.6.1` | `25.6.1`, `25.6.x`, `25.x` | `pip install ansible-lint==25.6.1` |

### **Python Linters**
| Linter | Tested Version | Supported Versions | Installation |
|--------|----------------|-------------------|--------------|
| **flake8** | `7.3.0` | `7.3.0`, `7.2.x`, `7.1.x`, `7.0.x`, `6.x` | `pip install flake8==7.3.0` |
| **pylint** | `3.3.7` | `3.3.7`, `3.3.x`, `3.2.x`, `3.1.x`, `3.0.x`, `2.x` | `pip install pylint==3.3.7` |

### **Node.js Linters**
| Linter | Tested Version | Supported Versions | Installation |
|--------|----------------|-------------------|--------------|
| **ESLint** | `8.57.1` | `8.57.1`, `8.57.x`, `8.5.x`, `8.x`, `7.x` | `npm install -g eslint@8.57.1` |
| **JSHint** | `2.13.6` | `2.13.6`, `2.13.x`, `2.1.x`, `2.x` | `npm install -g jshint@2.13.6` |
| **Prettier** | `3.6.2` | `3.6.2`, `3.6.x`, `3.x`, `2.x` | `npm install -g prettier@3.6.2` |

## 🔧 **Quick Setup for Contributors**

### **1. Check Your Current Versions**
```bash
# Run our version checker
./scripts/check_supported_versions.sh
```

### **2. Install Supported Versions**
```bash
# Python linters
pip install flake8==7.3.0 pylint==3.3.7 ansible-lint==25.6.1

# Node.js linters (global)
npm install -g eslint@8.57.1 jshint@2.13.6 prettier@3.6.2

# Or install locally in test projects
npm install --save-dev eslint@8.57.1 jshint@2.13.6 prettier@3.6.2
```

### **3. Verify Installation**
```bash
# Test Python linters
./scripts/version_tests/python_linters_test.sh

# Test Node.js linters
./scripts/version_tests/nodejs_linters_test.sh

# Run integration tests
python -m pytest tests/ -v
```

## 📚 **Version Management System**

### **Centralized Version Information**
All supported versions are defined in:
```python
# aider_lint_fixer/supported_versions.py
from aider_lint_fixer.supported_versions import get_linter_info, is_version_supported

# Check if a version is supported
is_supported = is_version_supported('flake8', '7.3.0')  # True
is_supported = is_version_supported('flake8', '5.0.0')  # False

# Get linter information
info = get_linter_info('eslint')
print(info.tested_version)      # "8.57.1"
print(info.supported_versions)  # ["8.57.1", "8.57", "8.5", "8.", "7."]
```

### **Version Checking Tools**
- **`./scripts/check_supported_versions.sh`**: Check installed versions
- **`aider_lint_fixer/supported_versions.py`**: Programmatic version checking
- **Version test scripts**: Validate specific linter integrations

## 🧪 **Testing Guidelines**

### **Before Contributing**
1. **Check versions**: Run `./scripts/check_supported_versions.sh`
2. **Run tests**: Execute `python -m pytest tests/ -v`
3. **Test specific linters**: Use version-specific test scripts

### **Adding New Linter Support**
1. **Update version constants**: Add to `supported_versions.py`
2. **Create linter implementation**: Follow modular pattern in `linters/`
3. **Add integration tests**: Create test in `tests/`
4. **Update documentation**: Add to README and guides
5. **Create version test script**: Add to `scripts/version_tests/`

### **Version Testing Matrix**
```bash
# Test all supported versions for a linter
for version in "7.3.0" "7.2.1" "7.1.0" "6.0.0"; do
    pip install flake8==$version
    python -m pytest tests/test_python_lint_integration.py::test_flake8 -v
done
```

## 🎯 **Profile Support**

All linters support multiple profiles:

### **Profile Types**
- **`basic`**: Essential checks for development
- **`default`**: Balanced checking for general use
- **`strict`**: Comprehensive checks for production
- **`production`**: Ansible-specific production profile

### **Testing Profiles**
```bash
# Test different profiles
python -m aider_lint_fixer . --linters flake8 --profile basic
python -m aider_lint_fixer . --linters flake8 --profile strict
```

## 🔄 **Version Update Process**

### **When to Update Versions**
1. **Security updates**: Critical security fixes in linters
2. **Major releases**: New linter major versions with significant improvements
3. **Compatibility issues**: When current versions have known issues

### **How to Update Versions**
1. **Update `supported_versions.py`**: Add new versions to supported lists
2. **Test thoroughly**: Run all integration tests with new versions
3. **Update documentation**: Update README, guides, and scripts
4. **Update test scripts**: Modify version-specific test scripts
5. **Test in CI/CD**: Ensure all automated tests pass

### **Version Deprecation**
1. **Mark as deprecated**: Add deprecation notice in documentation
2. **Maintain support**: Keep supporting for at least one minor release
3. **Remove support**: Remove from supported versions list
4. **Update tests**: Remove deprecated version tests

## 📖 **Documentation References**

### **For Contributors**
- **`README.md`**: Main documentation with version table
- **`docs/LINTER_TESTING_GUIDE.md`**: Comprehensive testing methodology
- **`docs/NODEJS_LINTERS_GUIDE.md`**: Node.js specific implementation guide
- **`aider_lint_fixer/supported_versions.py`**: Programmatic version reference

### **For Users**
- **Version compatibility**: Check README supported versions table
- **Installation**: Use exact versions from installation commands
- **Troubleshooting**: Run `./scripts/check_supported_versions.sh`

## 🚀 **Best Practices**

### **For Contributors**
1. **Always test with supported versions**: Don't assume newer versions work
2. **Use version checking tools**: Leverage our automated version checking
3. **Document version changes**: Update all relevant documentation
4. **Test across versions**: Validate with multiple supported versions

### **For Maintainers**
1. **Regular version audits**: Periodically review and update supported versions
2. **Security monitoring**: Watch for security updates in supported linters
3. **Compatibility testing**: Test new releases against supported versions
4. **Clear deprecation**: Provide clear migration paths for deprecated versions

---

**This version guide ensures consistent, reliable linter integration across all contributors and environments!** 🎯✨
