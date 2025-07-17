#!/bin/bash
# Check supported linter versions for aider-lint-fixer
# This script helps contributors verify they have compatible linter versions

set -e

echo "🔍 Aider Lint Fixer - Supported Linter Versions Check"
echo "====================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check version compatibility
check_version() {
    local linter=$1
    local current_version=$2
    local supported_versions=$3
    
    echo -e "${BLUE}Checking $linter version: $current_version${NC}"
    
    # Check if current version matches any supported pattern
    for pattern in $supported_versions; do
        if [[ $current_version == $pattern* ]]; then
            echo -e "  ${GREEN}✅ Compatible with supported pattern: $pattern${NC}"
            return 0
        fi
    done
    
    echo -e "  ${YELLOW}⚠️  Version may not be fully tested${NC}"
    echo -e "  ${YELLOW}   Supported versions: $supported_versions${NC}"
    return 1
}

echo "📋 Checking Ansible Linters..."
echo "------------------------------"

# ansible-lint
if command -v ansible-lint &> /dev/null; then
    version=$(ansible-lint --version 2>&1 | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [ -n "$version" ]; then
        check_version "ansible-lint" "$version" "25.6.1 25.6 25."
    else
        echo -e "${RED}❌ Could not determine ansible-lint version${NC}"
    fi
else
    echo -e "${RED}❌ ansible-lint: Not installed${NC}"
fi

echo ""
echo "🐍 Checking Python Linters..."
echo "-----------------------------"

# flake8
if command -v flake8 &> /dev/null; then
    version=$(flake8 --version 2>&1 | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [ -n "$version" ]; then
        check_version "flake8" "$version" "7.3.0 7.2 7.1 7.0 6."
    else
        echo -e "${RED}❌ Could not determine flake8 version${NC}"
    fi
else
    echo -e "${RED}❌ flake8: Not installed${NC}"
fi

# pylint
if command -v pylint &> /dev/null; then
    version=$(pylint --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [ -n "$version" ]; then
        check_version "pylint" "$version" "3.3.7 3.3 3.2 3.1 3.0 2."
    else
        echo -e "${RED}❌ Could not determine pylint version${NC}"
    fi
else
    echo -e "${RED}❌ pylint: Not installed${NC}"
fi

echo ""
echo "🟨 Checking Node.js Linters..."
echo "------------------------------"

# ESLint
if command -v npx &> /dev/null && npx eslint --version &> /dev/null; then
    version=$(npx eslint --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [ -n "$version" ]; then
        check_version "ESLint (npx)" "$version" "8.57.1 8.57 8.5 8. 7."
    else
        echo -e "${RED}❌ Could not determine ESLint version${NC}"
    fi
elif command -v eslint &> /dev/null; then
    version=$(eslint --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [ -n "$version" ]; then
        check_version "ESLint (global)" "$version" "8.57.1 8.57 8.5 8. 7."
    else
        echo -e "${RED}❌ Could not determine ESLint version${NC}"
    fi
else
    echo -e "${RED}❌ ESLint: Not installed (try: npm install -g eslint)${NC}"
fi

# JSHint
if command -v npx &> /dev/null && npx jshint --version &> /dev/null; then
    version=$(npx jshint --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [ -n "$version" ]; then
        check_version "JSHint (npx)" "$version" "2.13.6 2.13 2.1 2."
    else
        echo -e "${RED}❌ Could not determine JSHint version${NC}"
    fi
elif command -v jshint &> /dev/null; then
    version=$(jshint --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [ -n "$version" ]; then
        check_version "JSHint (global)" "$version" "2.13.6 2.13 2.1 2."
    else
        echo -e "${RED}❌ Could not determine JSHint version${NC}"
    fi
else
    echo -e "${RED}❌ JSHint: Not installed (try: npm install -g jshint)${NC}"
fi

# Prettier
if command -v npx &> /dev/null && npx prettier --version &> /dev/null; then
    version=$(npx prettier --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [ -n "$version" ]; then
        check_version "Prettier (npx)" "$version" "3.6.2 3.6 3. 2."
    else
        echo -e "${RED}❌ Could not determine Prettier version${NC}"
    fi
elif command -v prettier &> /dev/null; then
    version=$(prettier --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [ -n "$version" ]; then
        check_version "Prettier (global)" "$version" "3.6.2 3.6 3. 2."
    else
        echo -e "${RED}❌ Could not determine Prettier version${NC}"
    fi
else
    echo -e "${RED}❌ Prettier: Not installed (try: npm install -g prettier)${NC}"
fi

echo ""
echo "📚 Installation Instructions"
echo "============================"
echo ""
echo "🐍 Python Linters:"
echo "  pip install flake8==7.3.0 pylint==3.3.7"
echo ""
echo "📋 Ansible Linters:"
echo "  pip install ansible-lint==25.6.1"
echo ""
echo "🟨 Node.js Linters:"
echo "  npm install -g eslint@8.57.1 jshint@2.13.6 prettier@3.6.2"
echo "  # Or locally in your project:"
echo "  npm install --save-dev eslint@8.57.1 jshint@2.13.6 prettier@3.6.2"
echo ""
echo "📖 For more information, see:"
echo "  - README.md: Supported Linter Versions section"
echo "  - docs/LINTER_TESTING_GUIDE.md: Testing methodology"
echo "  - docs/NODEJS_LINTERS_GUIDE.md: Node.js specific guide"
echo ""
echo "✅ Version check complete!"
