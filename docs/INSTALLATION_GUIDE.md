# 🚀 Complete Installation Guide

## 📋 **Overview**

This guide provides comprehensive installation instructions for aider-lint-fixer, covering multiple installation methods, platform-specific instructions, and troubleshooting.

## 🎯 **Prerequisites**

### **System Requirements**
- **Python 3.11 or higher**
- **Git**
- **pip3** (usually included with Python)
- **Node.js 16+ and npm** (for Node.js linters)
- **4GB+ RAM** (for AI processing)
- **Internet connection** (for LLM API calls)

### **Platform Support**
- ✅ **Linux** (Ubuntu 20.04+, RHEL 8+, CentOS 8+)
- ✅ **macOS** (10.15+)
- ✅ **Windows** (10/11 with WSL2 recommended)

## 🚀 **Installation Methods**

### **Method 1: Recommended (Git + Virtual Environment)**

#### **Step 1: Clone Repository**
```bash
# Clone the latest version
git clone https://github.com/tosin2013/aider-lint-fixer.git
cd aider-lint-fixer

# Or clone specific version
git clone --branch v1.3.0 https://github.com/tosin2013/aider-lint-fixer.git
```

#### **Step 2: Create Virtual Environment**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Windows (Command Prompt):
venv\Scripts\activate.bat
```

#### **Step 3: Install aider-lint-fixer**
```bash
# Upgrade pip first
pip3 install --upgrade pip

# Install in development mode (recommended)
pip3 install -e .

# Install dependencies
pip3 install -r requirements.txt
```

#### **Step 4: Install Linters**
```bash
# Python linters
pip3 install flake8==7.3.0 pylint==3.3.7

# Ansible linters
pip3 install ansible-lint==25.6.1

# Node.js linters (requires Node.js/npm)
npm install -g eslint@8.57.1 jshint@2.13.6 prettier@3.6.2
```

### **Method 2: Direct Git Installation**

```bash
# One-line installation
pip3 install git+https://github.com/tosin2013/aider-lint-fixer.git

# With virtual environment
python3 -m venv aider-env
source aider-env/bin/activate  # Linux/macOS
pip3 install git+https://github.com/tosin2013/aider-lint-fixer.git
```

### **Method 3: Development Installation**

```bash
# For contributors and developers
git clone https://github.com/tosin2013/aider-lint-fixer.git
cd aider-lint-fixer

# Create development environment
python3 -m venv dev-env
source dev-env/bin/activate

# Install in editable mode with dev dependencies
pip3 install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## 🔧 **Platform-Specific Instructions**

### **Ubuntu/Debian**

```bash
# Install system dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv git nodejs npm

# Install aider-lint-fixer
git clone https://github.com/tosin2013/aider-lint-fixer.git
cd aider-lint-fixer
python3 -m venv venv && source venv/bin/activate
pip3 install -e . && pip3 install -r requirements.txt

# Install linters
pip3 install flake8==7.3.0 pylint==3.3.7 ansible-lint==25.6.1
npm install -g eslint@8.57.1 jshint@2.13.6 prettier@3.6.2
```

### **RHEL/CentOS/Fedora**

```bash
# Install system dependencies
sudo dnf install python3 python3-pip git nodejs npm

# Or on older systems:
sudo yum install python3 python3-pip git

# Install Node.js if not available
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo dnf install nodejs

# Install aider-lint-fixer
git clone https://github.com/tosin2013/aider-lint-fixer.git
cd aider-lint-fixer
python3 -m venv venv && source venv/bin/activate
pip3 install -e . && pip3 install -r requirements.txt
```

### **macOS**

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 git node

# Install aider-lint-fixer
git clone https://github.com/tosin2013/aider-lint-fixer.git
cd aider-lint-fixer
python3 -m venv venv && source venv/bin/activate
pip3 install -e . && pip3 install -r requirements.txt

# Install linters
pip3 install flake8==7.3.0 pylint==3.3.7 ansible-lint==25.6.1
npm install -g eslint@8.57.1 jshint@2.13.6 prettier@3.6.2
```

### **Windows (WSL2 Recommended)**

```bash
# Install WSL2 and Ubuntu
wsl --install -d Ubuntu

# Inside WSL2, follow Ubuntu instructions above
```

### **Windows (Native)**

```powershell
# Install Python from python.org
# Install Git from git-scm.com
# Install Node.js from nodejs.org

# Clone repository
git clone https://github.com/tosin2013/aider-lint-fixer.git
cd aider-lint-fixer

# Create virtual environment
python -m venv venv
venv\Scripts\Activate.ps1

# Install
pip install -e .
pip install -r requirements.txt
```

## 🔧 **Environment Configuration**

### **API Key Setup**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file and add your API keys
# DEEPSEEK_API_KEY=your_deepseek_api_key_here
# OPENAI_API_KEY=your_openai_api_key_here  # Optional

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Or use the setup script
./setup_env.sh
```

### **Configuration File**

```bash
# Create custom configuration (optional)
cp config/default.yaml config/custom.yaml

# Edit custom.yaml for your preferences
# - LLM provider settings
# - Linter configurations
# - Project-specific settings
```

## ✅ **Verification**

### **Check Installation**

```bash
# Verify aider-lint-fixer installation
python3 -m aider_lint_fixer --version

# Check supported linters
./scripts/check_supported_versions.sh

# Test basic functionality
python3 -m aider_lint_fixer --help
```

### **Test with Sample Project**

```bash
# Test Python linting
python3 -m aider_lint_fixer . --linters flake8 --dry-run --verbose

# Test Ansible linting (if you have Ansible files)
python3 -m aider_lint_fixer . --linters ansible-lint --dry-run --verbose

# Test Node.js linting (if you have JS files)
python3 -m aider_lint_fixer . --linters eslint --dry-run --verbose
```

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. Python Version Issues**
```bash
# Check Python version
python3 --version  # Should be 3.11+

# If python3 not found:
which python3
ls -la /usr/bin/python*

# Install Python 3.11+ if needed
sudo apt install python3.11 python3.11-venv  # Ubuntu
brew install python@3.11                      # macOS
```

#### **2. Virtual Environment Issues**
```bash
# If venv module not found:
sudo apt install python3-venv  # Ubuntu
pip3 install virtualenv        # Alternative

# If activation fails:
chmod +x venv/bin/activate
source venv/bin/activate
```

#### **3. Permission Issues**
```bash
# If pip install fails:
pip3 install --user -e .

# Or fix permissions:
sudo chown -R $USER:$USER ~/.local/
```

#### **4. Linter Installation Issues**
```bash
# Check linter availability:
which flake8 pylint ansible-lint eslint

# Install missing linters:
pip3 install flake8==7.3.0 --force-reinstall
npm install -g eslint@8.57.1 --force

# Check versions:
./scripts/check_supported_versions.sh
```

#### **5. Network/Proxy Issues**
```bash
# Configure pip for proxy:
pip3 install --proxy http://proxy.company.com:8080 -e .

# Configure npm for proxy:
npm config set proxy http://proxy.company.com:8080
npm config set https-proxy http://proxy.company.com:8080
```

### **Getting Help**

- **Documentation**: Check `docs/` directory
- **Version compatibility**: Run `./scripts/check_supported_versions.sh`
- **Verbose output**: Add `--verbose` to commands
- **Debug mode**: Set `DEBUG=1` environment variable
- **Issues**: Report at [GitHub Issues](https://github.com/tosin2013/aider-lint-fixer/issues)

## 🎯 **Next Steps**

After successful installation:

1. **Configure API keys**: Edit `.env` file
2. **Test with your project**: Run on a sample directory
3. **Read usage guide**: Check `README.md` for usage examples
4. **Explore advanced features**: See `docs/` for detailed guides

---

**Installation complete! You're ready to start using aider-lint-fixer for AI-powered code quality improvement.** 🎉
