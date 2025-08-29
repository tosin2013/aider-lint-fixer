---
title: Getting Started with Aider-Lint-Fixer
---

# Getting Started with Aider-Lint-Fixer

This tutorial will guide you through installing, configuring, and running aider-lint-fixer for the first time. By the end, you'll have successfully linted and fixed code issues in a sample project.

## Prerequisites

Before you begin, ensure you have:
- **Python 3.11+** installed on your system
- **Git** for version control
- **OpenAI API key** (optional, for AI-powered fixes)
- A code project to test with (we'll provide a sample)

## Step 1: Installation

### Option A: Install via pip (Recommended)
```bash
pip install aider-lint-fixer
```

### Option B: Install from source
```bash
git clone https://github.com/your-org/aider-lint-fixer.git
cd aider-lint-fixer
pip install -e .
```

### Verify Installation
```bash
aider-lint-fixer --version
```

You should see output like: `aider-lint-fixer 2.0.0`

## Step 2: Basic Configuration

### Create a Configuration File
```bash
mkdir -p ~/.config/aider-lint-fixer
cat > ~/.config/aider-lint-fixer/config.yaml << EOF
profile: tutorial
linters:
  python: [flake8, pylint]
  javascript: [eslint]
logging:
  level: INFO
EOF
```

### Set Environment Variables (Optional)
```bash
# For AI-powered fixes (optional)
export OPENAI_API_KEY="your-api-key-here"

# Point to your config file
export AIDER_LINT_CONFIG="~/.config/aider-lint-fixer/config.yaml"
```

## Step 3: Create a Test Project

Let's create a simple Python project with some intentional issues:

```bash
mkdir aider-lint-tutorial
cd aider-lint-tutorial

# Create a Python file with linting issues
cat > example.py << 'EOF'
import os
import sys
import json

def hello_world( name ):
    print("Hello, "+name+"!")
    unused_var = "this will trigger a warning"
    return

class MyClass:
    def __init__(self,value):
        self.value=value
    
    def get_value( self ):
        return self.value

if __name__=="__main__":
    hello_world("World")
    obj=MyClass(42)
    print(obj.get_value())
EOF
```

## Step 4: Run Your First Lint Check

### Check for Issues (No Fixes)
```bash
aider-lint-fixer --path . --check-only
```

You should see output showing various linting issues:
- Missing spaces around operators
- Unused imports
- Unused variables
- Style violations

### View Detailed Results
```bash
aider-lint-fixer --path . --check-only --verbose
```

## Step 5: Auto-Fix Issues

### Fix Issues Automatically
```bash
aider-lint-fixer --path . --auto-fix
```

This will:
1. Run all configured linters
2. Identify fixable issues
3. Apply automatic fixes where possible
4. Show a summary of changes

### Review the Changes
```bash
cat example.py
```

Notice how the code has been automatically formatted and improved!

## Step 6: Advanced Features (Optional)

### Use AI-Powered Fixes
If you have an OpenAI API key configured:
```bash
aider-lint-fixer --path . --ai-fix --interactive
```

This will:
- Use AI to suggest more complex fixes
- Allow you to review and approve changes
- Handle issues that simple linters can't fix

### Generate a Report
```bash
aider-lint-fixer --path . --report --output-format json > lint-report.json
```

## Step 7: Verification

Let's verify everything is working correctly:

```bash
# Run a final check
aider-lint-fixer --path . --check-only

# Should show minimal or no issues now
echo "Exit code: $?"
```

## Summary

In this tutorial, you learned how to:
- **Install** aider-lint-fixer using pip or from source
- **Configure** basic linting settings for your project
- **Run lint checks** to identify code quality issues
- **Auto-fix** common problems automatically
- **Use AI features** for advanced code improvements (optional)
- **Generate reports** for tracking code quality

## Next Steps

Now that you have aider-lint-fixer working, explore these guides:

- **[Configure Linters](../how-to/configure-linters.md)** - Customize linting rules for your project
- **[Container Deployment](./container-deployment.md)** - Use aider-lint-fixer in containers
- **[Development Environment Setup](./setting-up-your-development-environment.md)** - Full development workflow
- **[Debug Common Issues](../how-to/how-to-debug-common-issues.md)** - Troubleshooting guide

## Troubleshooting

**Installation Issues:**
```bash
# Upgrade pip if you encounter installation problems
pip install --upgrade pip
pip install aider-lint-fixer
```

**Permission Errors:**
```bash
# Use user installation if you don't have admin rights
pip install --user aider-lint-fixer
```

**Configuration Not Found:**
```bash
# Check if config file exists
aider-lint-fixer --check-config
```

Congratulations! You've successfully completed your first aider-lint-fixer workflow.