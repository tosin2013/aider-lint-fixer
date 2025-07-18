# Aider Lint Fixer

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Automated lint error detection and fixing powered by aider.chat and AI**

Aider Lint Fixer is an intelligent tool that automatically detects lint errors in your codebase and fixes them using AI-powered code generation through [aider.chat](https://aider.chat).

**🎉 v1.3.0 Release**: Enterprise-ready with Node.js, Python, and Ansible support!

## ✨ Features (v1.3.0)

- � **Python Support**: Flake8, Pylint with profile support (basic/strict)
- 🟨 **Node.js Support**: ESLint, JSHint, Prettier with comprehensive error detection
- 📋 **Ansible Support**: ansible-lint with production-ready profiles
- 🤖 **AI-Powered Fixing**: Uses aider.chat with multiple LLM providers
- 🎯 **Smart Error Analysis**: Categorizes and prioritizes errors for optimal fixing
- � **Enterprise Scalability**: Handles 200+ lint issues with intelligent batching
- ⚙️ **Profile System**: Basic (development) vs Strict (production) configurations
- 📊 **Progress Tracking**: Real-time progress with detailed reporting

## 📋 **Supported Linter Versions**

### **Ansible Linters**
| Linter | Tested Version | Supported Versions | Profile Support |
|--------|----------------|-------------------|-----------------|
| **ansible-lint** | `25.6.1` | `25.6.1`, `25.6.x`, `25.x` | ✅ basic, production |

### **Python Linters**
| Linter | Tested Version | Supported Versions | Profile Support |
|--------|----------------|-------------------|-----------------|
| **flake8** | `7.3.0` | `7.3.0`, `7.2.x`, `7.1.x`, `7.0.x`, `6.x` | ✅ basic, strict |
| **pylint** | `3.3.7` | `3.3.7`, `3.3.x`, `3.2.x`, `3.1.x`, `3.0.x`, `2.x` | ✅ basic, strict |

### **Node.js Linters**
| Linter | Tested Version | Supported Versions | Profile Support |
|--------|----------------|-------------------|-----------------|
| **ESLint** | `8.57.1` | `8.57.1`, `8.57.x`, `8.5.x`, `8.x`, `7.x` | ✅ basic, strict |
| **JSHint** | `2.13.6` | `2.13.6`, `2.13.x`, `2.1.x`, `2.x` | ✅ basic, strict |
| **Prettier** | `3.6.2` | `3.6.2`, `3.6.x`, `3.x`, `2.x` | ✅ basic, strict |

### **Version Compatibility Notes**
- **Tested Version**: Explicitly tested and validated in our CI/CD
- **Supported Versions**: Expected to work based on API compatibility
- **Profile Support**: Configurable strictness levels for different environments

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [aider.chat](https://aider.chat) installed (`pip install aider-chat`)
- DeepSeek API key from [platform.deepseek.com](https://platform.deepseek.com/)

### Installation

```bash
# Install aider-lint-fixer from PyPI
pip install aider-lint-fixer
```

### 🚀 **Installation**

#### **Prerequisites**
- **Python 3.11 or higher**
- **Git**
- **pip3** (usually included with Python)
- **Node.js/npm** (for Node.js linters)
- **Supported platforms**: Linux, macOS (Windows has limited support)

#### **📦 Quick Installation (PyPI)**

```bash
# Install from PyPI (recommended)
pip install aider-lint-fixer

# Install with learning features (recommended for better accuracy)
pip install aider-lint-fixer[learning]

# Install with all optional features
pip install aider-lint-fixer[all]

# Verify installation
aider-lint-fixer --version
```

#### **🔧 Development Installation (Git + Virtual Environment)**

##### **1. Clone and Set Up Virtual Environment**
```bash
# Clone the repository
git clone https://github.com/tosin2013/aider-lint-fixer.git
cd aider-lint-fixer

# Create virtual environment
python3 -m venv venv

# Activate virtual environment (Linux/macOS)
source venv/bin/activate

# Upgrade pip
pip3 install --upgrade pip
```

##### **2. Install aider-lint-fixer**
```bash
# Install in development mode (recommended for latest features)
pip3 install -e .

# Install dependencies
pip3 install -r requirements.txt
```

##### **3. Install Required Linters**
```bash
# Python linters
pip3 install flake8==7.3.0 pylint==3.3.7

# Ansible linters
pip3 install ansible-lint==25.6.1

# Node.js linters (requires Node.js/npm)
npm install -g eslint@8.57.1 jshint@2.13.6 prettier@3.6.2
```

##### **4. Verify Installation**
```bash
# Check version
python3 -m aider_lint_fixer --version

# Check supported linters
./scripts/check_supported_versions.sh
```

#### **🐳 Alternative Installation Methods**

##### **Install from Git (Latest Development)**
```bash
# Install directly from Git (latest development version)
pip install git+https://github.com/tosin2013/aider-lint-fixer.git

# With virtual environment (recommended for development)
python3 -m venv aider-env && source aider-env/bin/activate && pip install git+https://github.com/tosin2013/aider-lint-fixer.git
```

##### **Install from Source (Development)**
```bash
git clone https://github.com/tosin2013/aider-lint-fixer.git
cd aider-lint-fixer
python3 -m venv venv && source venv/bin/activate
pip3 install -e .
```

#### **⚡ Quick Start (5 Minutes)**

```bash
# 1. Clone and setup
git clone https://github.com/tosin2013/aider-lint-fixer.git
cd aider-lint-fixer
python3 -m venv venv && source venv/bin/activate

# 2. Install
pip3 install -e . && pip3 install -r requirements.txt

# 3. Install linters (choose your language)
pip3 install flake8==7.3.0 pylint==3.3.7 ansible-lint==25.6.1
npm install -g eslint@8.57.1 jshint@2.13.6 prettier@3.6.2

# 4. Setup environment
cp .env.example .env
# Edit .env and add your API key

# 5. Test installation
python3 -m aider_lint_fixer --help
```

### **🔧 Environment Setup**

#### **API Key Configuration**
```bash
# Run the setup script (recommended)
./setup_env.sh

# Or manually create .env file
cp .env.example .env
# Edit .env and add your DeepSeek API key
# DEEPSEEK_API_KEY=your_actual_api_key_here

# Export environment variables
export $(cat .env | grep -v '^#' | xargs)
```

#### **Verify Your Setup**
```bash
# Check all supported linter versions
./scripts/check_supported_versions.sh

# Test with a sample project
python3 -m aider_lint_fixer . --linters flake8 --dry-run --verbose
```

#### **🔧 Troubleshooting Installation**

##### **Common Issues and Solutions**

**1. Python Version Issues**
```bash
# Check Python version
python3 --version  # Should be 3.11+

# If python3 not found, try:
python --version   # On some systems
```

**2. Virtual Environment Issues**
```bash
# If venv creation fails:
sudo apt-get install python3-venv  # Ubuntu/Debian
brew install python3               # macOS

# Alternative virtual environment tools:
pip3 install virtualenv
virtualenv venv
```

**3. Permission Issues**
```bash
# If pip install fails with permissions:
pip3 install --user -e .

# Or use virtual environment (recommended):
python3 -m venv venv && source venv/bin/activate
```

**4. Node.js Linter Issues**
```bash
# Install Node.js if missing:
# Ubuntu/Debian:
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS:
brew install node

# Verify installation:
node --version && npm --version
```

**5. Linter Version Conflicts**
```bash
# Check current versions:
./scripts/check_supported_versions.sh

# Install specific versions:
pip3 install flake8==7.3.0 --force-reinstall
npm install -g eslint@8.57.1 --force
```

##### **Getting Help**
- **Complete installation guide**: See [`docs/INSTALLATION_GUIDE.md`](docs/INSTALLATION_GUIDE.md)
- **Automated installation**: Run `curl -fsSL https://raw.githubusercontent.com/tosin2013/aider-lint-fixer/main/scripts/install.sh | bash`
- **Check supported versions**: `./scripts/check_supported_versions.sh`
- **Verbose output**: Add `--verbose` to any command
- **Debug mode**: Set `DEBUG=1` environment variable
- **Issues**: Report at [GitHub Issues](https://github.com/tosin2013/aider-lint-fixer/issues)

### Basic Usage

```bash
# Test on a small project first
python -m aider_lint_fixer /path/to/your/project --max-files 1

# Run on your project
python -m aider_lint_fixer /path/to/your/project

# Limit scope for large projects
python -m aider_lint_fixer /path/to/your/project --max-files 5 --max-errors 10

# Verbose output for debugging
python -m aider_lint_fixer /path/to/your/project --verbose
```

## 📋 Supported Linters

### Python
- **flake8** - Style guide enforcement
- **pylint** - Code analysis and quality
- **black** - Code formatting
- **isort** - Import sorting
- **mypy** - Type checking

### JavaScript/TypeScript
- **eslint** - Linting and code quality
- **prettier** - Code formatting

### Go
- **golint** - Go linting
- **gofmt** - Go formatting
- **go vet** - Static analysis

### Rust
- **rustfmt** - Rust formatting
- **clippy** - Rust linting

### Ansible
- **ansible-lint** - Ansible playbook linting

## ⚙️ Configuration

Create a `.aider-lint-fixer.yml` file in your project root:

```yaml
# LLM Configuration
llm:
  provider: "deepseek"  # Options: deepseek, openrouter, ollama
  model: "deepseek/deepseek-chat"
  fallback_providers:
    - "openrouter"
    - "ollama"

# Linter Configuration
linters:
  auto_detect: true
  enabled:
    - flake8
    - eslint
    - golint
    - rustfmt
    - ansible-lint

# Aider Configuration
aider:
  auto_commit: false
  backup_files: true
  max_retries: 3

# Project Settings
project:
  exclude_patterns:
    - "*.min.js"
    - "node_modules/"
    - "__pycache__/"
    - ".git/"
```

## 🎯 Command Line Options

```bash
python -m aider_lint_fixer [PROJECT_PATH] [OPTIONS]

Options:
  --config, -c PATH       Path to configuration file
  --llm TEXT             LLM provider (deepseek, openrouter, ollama)
  --model TEXT           Specific model to use
  --linters TEXT         Comma-separated list of linters to run
  --max-files INTEGER    Maximum number of files to process
  --max-errors INTEGER   Maximum errors to fix per file
  --dry-run              Show what would be fixed without making changes
  --interactive          Confirm each fix before applying
  --verbose, -v          Enable verbose output
  --log-file PATH        Path to log file
  --no-banner            Disable banner output
  --help                 Show this message and exit
  --stats                Show learning statistics and exit
```

## 🧠 Learning Features

### **Intelligent Error Classification**

Aider-lint-fixer includes an advanced learning system that improves accuracy over time by learning from successful and failed fix attempts.

#### **📦 Installation for Learning**
```bash
# Install with learning features (includes scikit-learn)
pip install aider-lint-fixer[learning]

# Or install learning dependencies manually
pip install scikit-learn>=1.0.0 requests>=2.25.0 beautifulsoup4>=4.9.0 pyahocorasick>=1.4.0
```

#### **🔍 How Learning Works**
- **Automatic**: Learning happens automatically during normal operation
- **No configuration needed**: Works out of the box once dependencies are installed
- **Language-specific**: Separate models for Python, JavaScript, Ansible, etc.
- **Persistent**: Learning data survives between runs

#### **📊 Monitor Learning Progress**
```bash
# View learning statistics
aider-lint-fixer --stats

# View in JSON format
aider-lint-fixer --stats --output-format json

# Detailed cache management
python -m aider_lint_fixer.cache_cli --action stats
```

#### **🎯 Learning Benefits**
- **Improved Accuracy**: 46.1% fixability rate on real projects
- **Faster Classification**: Sub-millisecond error analysis
- **Project-Specific**: Learns patterns specific to your codebase
- **Conservative Approach**: Avoids false positives

#### **📁 Learning Data Storage**
Learning data is stored in `.aider-lint-cache/`:
```
.aider-lint-cache/
├── ansible_training.json     # Ansible-specific learning
├── python_training.json      # Python-specific learning
├── javascript_training.json  # JavaScript-specific learning
└── scraped_rules.json       # Web-scraped rule knowledge
```

#### **🧹 Cache Management**
```bash
# Clean old learning data (30+ days)
python -m aider_lint_fixer.cache_cli --action cleanup --max-age-days 30

# Export learning data for backup
python -m aider_lint_fixer.cache_cli --action export --file backup.json

# Import learning data from backup
python -m aider_lint_fixer.cache_cli --action import --file backup.json
```

#### **🔧 Troubleshooting Learning Issues**

**Problem: "Found 0 fixable errors (0.0% of X total baseline errors)"**

This usually indicates missing learning dependencies. Check your setup:

```bash
# Quick diagnosis
python scripts/check_learning_setup.py

# Or check via stats
aider-lint-fixer --stats
```

**Common Issues:**
- **Missing scikit-learn**: `pip install aider-lint-fixer[learning]`
- **Missing Aho-Corasick**: Causes "using fallback pattern matching" warning
- **No scraped rules**: Tool will auto-create them if web dependencies are available

**Expected vs Actual:**
```bash
# ❌ Without learning dependencies
Found 0 fixable errors (0.0% of 58 total baseline errors)

# ✅ With learning dependencies
Found 27 fixable errors (46.1% of 58 total baseline errors)
```

## 📖 Examples

### Python Project
```bash
# Focus on Python linters
python -m aider_lint_fixer --linters flake8,black,isort

# Fix formatting issues only
python -m aider_lint_fixer --linters black,isort --max-errors 20
```

### JavaScript Project
```bash
# Focus on JavaScript linters
python -m aider_lint_fixer --linters eslint,prettier

# Interactive fixing for complex project
python -m aider_lint_fixer --linters eslint --interactive
```

### Ansible Project
```bash
# Focus on Ansible linting
python -m aider_lint_fixer --linters ansible-lint

# Dry run to see Ansible issues
python -m aider_lint_fixer --linters ansible-lint --dry-run
```

## 🔧 How It Works

1. **Project Detection**: Automatically scans your project to identify languages, package managers, and lint configurations
2. **Lint Execution**: Runs appropriate linters and collects error reports
3. **Error Analysis**: Categorizes errors by type and complexity, prioritizes them for fixing
4. **AI-Powered Fixing**: Uses aider.chat with your chosen LLM to generate and apply fixes
5. **Verification**: Re-runs linters to verify fixes and reports success rates

## 🛠️ Development

This project includes a comprehensive Makefile for development tasks:

```bash
# Show all available commands
make help

# Setup development environment
make dev-setup

# Code quality checks
make lint          # Run linters
make format        # Format code with black and isort
make type-check    # Run mypy type checking

# Testing
make test          # Run tests
make test-coverage # Run tests with coverage

# Security
make security      # Run security checks
make audit         # Comprehensive security audit

# Build and package
make build         # Build distribution packages
make clean         # Clean build artifacts

# Self-testing (test the tool on itself!)
make self-test     # Run aider-lint-fixer on its own code

# Complete quality assurance
make qa            # Run all quality checks
make ci            # Full CI pipeline
```

## 🤖 Automated Dependency Management

This project uses **Dependabot** for automated dependency updates and security monitoring:

### 📅 Update Schedule
- **Python dependencies**: Weekly (Mondays) - `pip` ecosystem
- **Node.js dependencies**: Weekly (Tuesdays) - `npm` ecosystem
- **GitHub Actions**: Weekly (Wednesdays) - Workflow dependencies
- **Docker images**: Weekly (Thursdays) - Base image updates
- **Security updates**: **Immediate** - Critical vulnerabilities

### 🔄 Auto-Merge Policy
- ✅ **Security updates**: Auto-merged after tests pass
- ✅ **Patch updates**: Auto-merged after validation
- ✅ **Testing dependencies**: Auto-merged (pytest, coverage, mock)
- ✅ **Code quality tools**: Auto-merged (black, isort, flake8, mypy)
- ✅ **GitHub Actions**: Auto-merged (actions/*, github/*)
- ⚠️ **Major updates**: Require manual review
- ⚠️ **Core dependencies**: Require manual review (aider-chat, click)

### 🔍 Weekly Health Checks (Sundays)
- **🔒 Security audit**: Vulnerability scanning with `safety`, `bandit`, `pip-audit`
- **📅 Outdated dependencies**: Tracking and automated PR creation
- **📄 License compliance**: Monitoring for license compatibility
- **🔍 Dependency conflicts**: Detecting version incompatibilities

### 🛡️ Security Features
- **Immediate security alerts**: Critical vulnerabilities trigger instant PRs
- **Automated testing**: All updates tested before merge
- **License monitoring**: GPL and unknown licenses flagged
- **Conflict detection**: Dependency version conflicts identified

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### 🔧 **Development Setup for Contributors**

#### **Quick Setup**
```bash
# Automated installation for contributors
curl -fsSL https://raw.githubusercontent.com/tosin2013/aider-lint-fixer/main/scripts/install.sh | bash

# Or manual setup
git clone https://github.com/tosin2013/aider-lint-fixer.git
cd aider-lint-fixer
python3 -m venv venv && source venv/bin/activate
pip3 install -e . && pip3 install -r requirements.txt
```

#### **Install Supported Linter Versions**
```bash
# Check your current versions
./scripts/check_supported_versions.sh

# Install supported versions
pip3 install flake8==7.3.0 pylint==3.3.7 ansible-lint==25.6.1
npm install -g eslint@8.57.1 jshint@2.13.6 prettier@3.6.2
```

### 📋 **Version Testing**
```bash
# Test Python linters
./scripts/version_tests/python_linters_test.sh

# Test Node.js linters
./scripts/version_tests/nodejs_linters_test.sh

# Run integration tests
python -m pytest tests/ -v
```

### 📚 **Version Reference**
- **Supported Versions**: See table above or `aider_lint_fixer/supported_versions.py`
- **Testing Guide**: `docs/LINTER_TESTING_GUIDE.md`
- **Node.js Guide**: `docs/NODEJS_LINTERS_GUIDE.md`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Tosin Akinosho**
- GitHub: [@tosin2023](https://github.com/tosin2023)
- Project: [aider-lint-fixer](https://github.com/tosin2023/aider-lint-fixer)

## 🙏 Acknowledgments

- [aider.chat](https://aider.chat) for the amazing AI-powered code editing capabilities
- The open-source community for the various linters and tools that make this project possible
- All the LLM providers (DeepSeek, OpenRouter, Ollama) for making AI accessible

## 📚 Documentation

For detailed usage instructions, configuration options, and troubleshooting, see:
- [Usage Guide](Aider%20Lint%20Fixer%20-%20Usage%20Guide.md)
- [Complete Solution Documentation](Aider%20Lint%20Fixer%20-%20Complete%20Solution%20Delivery.md)

---

**Made with ❤️ by Tosin Akinosho**
