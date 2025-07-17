#!/bin/bash
# Automated installation script for aider-lint-fixer
# Usage: curl -fsSL https://raw.githubusercontent.com/tosin2013/aider-lint-fixer/main/scripts/install.sh | bash

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/tosin2013/aider-lint-fixer.git"
INSTALL_DIR="$HOME/aider-lint-fixer"
VENV_NAME="venv"

echo -e "${BLUE}🚀 Aider Lint Fixer - Automated Installation${NC}"
echo "=============================================="
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Python 3.11+
    if command_exists python3; then
        python_version=$(python3 --version | cut -d' ' -f2)
        python_major=$(echo $python_version | cut -d'.' -f1)
        python_minor=$(echo $python_version | cut -d'.' -f2)

        if [ "$python_major" -eq 3 ] && [ "$python_minor" -ge 11 ]; then
            print_status "Python $python_version found"
        else
            print_error "Python 3.11+ required, found $python_version"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.11+"
        exit 1
    fi
    
    # Check Git
    if command_exists git; then
        print_status "Git found"
    else
        print_error "Git not found. Please install Git"
        exit 1
    fi
    
    # Check pip3
    if command_exists pip3; then
        print_status "pip3 found"
    else
        print_warning "pip3 not found, trying pip"
        if command_exists pip; then
            alias pip3=pip
            print_status "Using pip as pip3"
        else
            print_error "pip not found. Please install pip"
            exit 1
        fi
    fi
    
    # Check Node.js (optional)
    if command_exists node && command_exists npm; then
        node_version=$(node --version)
        print_status "Node.js $node_version found"
        NODE_AVAILABLE=true
    else
        print_warning "Node.js/npm not found. Node.js linters will not be available"
        NODE_AVAILABLE=false
    fi
}

# Install system dependencies based on OS
install_system_deps() {
    print_info "Installing system dependencies..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get; then
            # Ubuntu/Debian
            print_info "Detected Ubuntu/Debian system"
            sudo apt-get update
            sudo apt-get install -y python3-venv python3-pip git
            
            if [ "$NODE_AVAILABLE" = false ]; then
                print_info "Installing Node.js..."
                curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
                sudo apt-get install -y nodejs
                NODE_AVAILABLE=true
            fi
            
        elif command_exists yum; then
            # RHEL/CentOS
            print_info "Detected RHEL/CentOS system"
            sudo yum install -y python3 python3-pip git
            
            if [ "$NODE_AVAILABLE" = false ]; then
                print_info "Installing Node.js..."
                curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
                sudo yum install -y nodejs
                NODE_AVAILABLE=true
            fi
            
        elif command_exists dnf; then
            # Fedora
            print_info "Detected Fedora system"
            sudo dnf install -y python3 python3-pip git nodejs npm
            NODE_AVAILABLE=true
        fi
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        print_info "Detected macOS system"
        if command_exists brew; then
            brew install python3 git node
            NODE_AVAILABLE=true
        else
            print_warning "Homebrew not found. Please install dependencies manually"
        fi
    fi
}

# Clone repository
clone_repository() {
    print_info "Cloning aider-lint-fixer repository..."
    
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Directory $INSTALL_DIR already exists"
        read -p "Remove existing directory and continue? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
        else
            print_error "Installation cancelled"
            exit 1
        fi
    fi
    
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    print_status "Repository cloned to $INSTALL_DIR"
}

# Create virtual environment
create_venv() {
    print_info "Creating virtual environment..."
    
    python3 -m venv "$VENV_NAME"
    source "$VENV_NAME/bin/activate"
    
    # Upgrade pip
    pip3 install --upgrade pip
    
    print_status "Virtual environment created and activated"
}

# Install aider-lint-fixer
install_aider() {
    print_info "Installing aider-lint-fixer..."
    
    # Install in development mode
    pip3 install -e .
    
    # Install dependencies
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
    fi
    
    print_status "aider-lint-fixer installed successfully"
}

# Install linters
install_linters() {
    print_info "Installing supported linters..."
    
    # Python linters
    print_info "Installing Python linters..."
    pip3 install flake8==7.3.0 pylint==3.3.7
    
    # Ansible linters
    print_info "Installing Ansible linters..."
    pip3 install ansible-lint==25.6.1
    
    # Node.js linters (if Node.js is available)
    if [ "$NODE_AVAILABLE" = true ]; then
        print_info "Installing Node.js linters..."
        npm install -g eslint@8.57.1 jshint@2.13.6 prettier@3.6.2
    else
        print_warning "Skipping Node.js linters (Node.js not available)"
    fi
    
    print_status "Linters installed successfully"
}

# Setup environment
setup_environment() {
    print_info "Setting up environment..."
    
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status "Environment file created (.env)"
        print_warning "Please edit .env file and add your API keys"
    fi
    
    # Make scripts executable
    if [ -d "scripts" ]; then
        chmod +x scripts/*.sh
        print_status "Scripts made executable"
    fi
}

# Verify installation
verify_installation() {
    print_info "Verifying installation..."
    
    # Check aider-lint-fixer
    if python3 -m aider_lint_fixer --version >/dev/null 2>&1; then
        version=$(python3 -m aider_lint_fixer --version 2>/dev/null || echo "unknown")
        print_status "aider-lint-fixer $version is working"
    else
        print_error "aider-lint-fixer installation verification failed"
        return 1
    fi
    
    # Check linters
    if [ -f "scripts/check_supported_versions.sh" ]; then
        print_info "Checking linter versions..."
        ./scripts/check_supported_versions.sh | head -20
    fi
    
    print_status "Installation verification completed"
}

# Main installation function
main() {
    echo "This script will install aider-lint-fixer and its dependencies."
    echo "Installation directory: $INSTALL_DIR"
    echo ""
    
    read -p "Continue with installation? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_info "Installation cancelled"
        exit 0
    fi
    
    check_prerequisites
    install_system_deps
    clone_repository
    create_venv
    install_aider
    install_linters
    setup_environment
    verify_installation
    
    echo ""
    echo -e "${GREEN}🎉 Installation completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. cd $INSTALL_DIR"
    echo "2. source $VENV_NAME/bin/activate"
    echo "3. Edit .env file and add your API keys"
    echo "4. Run: python3 -m aider_lint_fixer --help"
    echo ""
    echo "For usage examples, see: README.md"
    echo "For detailed documentation, see: docs/"
    echo ""
    echo -e "${BLUE}Happy linting! 🚀${NC}"
}

# Run main function
main "$@"
