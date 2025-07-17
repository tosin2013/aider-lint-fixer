#!/bin/bash

# Aider Lint Fixer Installation Script
# This script installs aider-lint-fixer and its dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                 Aider Lint Fixer Installer                  ║"
    echo "║              Automated Lint Error Detection & Fixing         ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed."
        print_status "Please install Python 3.8 or higher and try again."
        exit 1
    fi
    
    # Check Python version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_status "Found Python $python_version"
    
    # Check pip
    if ! command_exists pip3; then
        print_error "pip3 is required but not installed."
        print_status "Please install pip3 and try again."
        exit 1
    fi
    
    # Check git
    if ! command_exists git; then
        print_warning "Git is not installed. Some features may not work properly."
        print_status "Consider installing git for full functionality."
    fi
    
    print_success "Prerequisites check completed"
}

# Install aider-lint-fixer
install_aider_lint_fixer() {
    print_status "Installing aider-lint-fixer..."
    
    # Create virtual environment if requested
    if [ "$USE_VENV" = "true" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv aider-lint-fixer-env
        source aider-lint-fixer-env/bin/activate
        print_success "Virtual environment created and activated"
    fi
    
    # Install from PyPI (when available) or from source
    if [ "$INSTALL_FROM_SOURCE" = "true" ]; then
        print_status "Installing from source..."
        
        # Clone repository
        if [ ! -d "aider-lint-fixer" ]; then
            git clone https://github.com/your-org/aider-lint-fixer.git
        fi
        
        cd aider-lint-fixer
        pip3 install -r requirements.txt
        pip3 install -e .
        cd ..
    else
        print_status "Installing from PyPI..."
        pip3 install aider-lint-fixer
    fi
    
    print_success "aider-lint-fixer installed successfully"
}

# Install common linters
install_linters() {
    print_status "Installing common linters..."
    
    # Python linters
    if command_exists python3; then
        print_status "Installing Python linters..."
        pip3 install flake8 black isort mypy pylint
        print_success "Python linters installed"
    fi
    
    # JavaScript linters (if Node.js is available)
    if command_exists npm; then
        print_status "Installing JavaScript linters..."
        npm install -g eslint prettier
        print_success "JavaScript linters installed"
    else
        print_warning "Node.js/npm not found. Skipping JavaScript linters."
    fi
    
    # Go linters (if Go is available)
    if command_exists go; then
        print_status "Installing Go linters..."
        go install golang.org/x/lint/golint@latest
        print_success "Go linters installed"
    else
        print_warning "Go not found. Skipping Go linters."
    fi
    
    # Rust linters (if Rust is available)
    if command_exists cargo; then
        print_status "Installing Rust linters..."
        rustup component add rustfmt clippy
        print_success "Rust linters installed"
    else
        print_warning "Rust not found. Skipping Rust linters."
    fi
    
    # Ansible linters (if Python is available)
    if command_exists python3; then
        print_status "Installing Ansible linters..."
        pip3 install ansible-lint
        print_success "Ansible linters installed"
    else
        print_warning "Python not found. Skipping Ansible linters."
    fi
}

# Setup configuration
setup_configuration() {
    print_status "Setting up configuration..."
    
    # Create config directory
    config_dir="$HOME/.config/aider-lint-fixer"
    mkdir -p "$config_dir"
    
    # Create default configuration if it doesn't exist
    config_file="$HOME/.aider-lint-fixer.yml"
    if [ ! -f "$config_file" ]; then
        cat > "$config_file" << 'EOF'
# Aider Lint Fixer Configuration
llm:
  provider: "deepseek"
  model: "deepseek/deepseek-chat"

linters:
  auto_detect: true
  enabled:
    - flake8
    - eslint
    - golint
    - rustfmt

aider:
  auto_commit: false
  backup_files: true
  max_retries: 3

project:
  exclude_patterns:
    - "*.min.js"
    - "node_modules/"
    - "__pycache__/"
    - ".git/"
EOF
        print_success "Default configuration created at $config_file"
    else
        print_status "Configuration file already exists at $config_file"
    fi
}

# Setup LLM provider
setup_llm_provider() {
    print_status "Setting up LLM provider..."
    
    echo "Choose your LLM provider:"
    echo "1) DeepSeek (Recommended)"
    echo "2) OpenRouter"
    echo "3) Ollama (Local)"
    echo "4) Skip for now"
    
    read -p "Enter your choice (1-4): " choice
    
    case $choice in
        1)
            echo "To use DeepSeek:"
            echo "1. Sign up at https://www.deepseek.com/"
            echo "2. Get your API key from the dashboard"
            echo "3. Set the environment variable:"
            echo "   export DEEPSEEK_API_KEY=your_api_key"
            echo ""
            read -p "Enter your DeepSeek API key (or press Enter to skip): " api_key
            if [ ! -z "$api_key" ]; then
                echo "export DEEPSEEK_API_KEY=$api_key" >> ~/.bashrc
                export DEEPSEEK_API_KEY=$api_key
                print_success "DeepSeek API key configured"
            fi
            ;;
        2)
            echo "To use OpenRouter:"
            echo "1. Sign up at https://openrouter.ai/"
            echo "2. Get your API key"
            echo "3. Set the environment variable:"
            echo "   export OPENROUTER_API_KEY=your_api_key"
            echo ""
            read -p "Enter your OpenRouter API key (or press Enter to skip): " api_key
            if [ ! -z "$api_key" ]; then
                echo "export OPENROUTER_API_KEY=$api_key" >> ~/.bashrc
                export OPENROUTER_API_KEY=$api_key
                print_success "OpenRouter API key configured"
            fi
            ;;
        3)
            echo "To use Ollama:"
            echo "1. Install Ollama from https://ollama.ai/"
            echo "2. Pull a coding model: ollama pull deepseek-coder:6.7b"
            echo "3. Start Ollama: OLLAMA_CONTEXT_LENGTH=8192 ollama serve"
            print_status "Ollama setup instructions provided"
            ;;
        4)
            print_status "Skipping LLM provider setup"
            ;;
        *)
            print_warning "Invalid choice. Skipping LLM provider setup"
            ;;
    esac
}

# Verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    if command_exists aider-lint-fixer; then
        print_success "aider-lint-fixer command is available"
        
        # Test basic functionality
        print_status "Testing basic functionality..."
        aider-lint-fixer --help > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            print_success "Basic functionality test passed"
        else
            print_warning "Basic functionality test failed"
        fi
    else
        print_error "aider-lint-fixer command not found"
        print_status "You may need to restart your shell or add the installation directory to your PATH"
    fi
}

# Print usage instructions
print_usage_instructions() {
    print_success "Installation completed!"
    echo ""
    echo "Quick start:"
    echo "1. Navigate to your project directory"
    echo "2. Run: aider-lint-fixer --dry-run"
    echo "3. If satisfied with the analysis, run: aider-lint-fixer"
    echo ""
    echo "For more information:"
    echo "- Run: aider-lint-fixer --help"
    echo "- Read the documentation in the docs/ directory"
    echo "- Visit: https://github.com/your-org/aider-lint-fixer"
    echo ""
    if [ "$USE_VENV" = "true" ]; then
        echo "Note: You're using a virtual environment. To activate it in the future:"
        echo "source aider-lint-fixer-env/bin/activate"
        echo ""
    fi
}

# Main installation function
main() {
    # Parse command line arguments
    USE_VENV=false
    INSTALL_FROM_SOURCE=false
    INSTALL_LINTERS=true
    SETUP_CONFIG=true
    SETUP_LLM=true
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --venv)
                USE_VENV=true
                shift
                ;;
            --source)
                INSTALL_FROM_SOURCE=true
                shift
                ;;
            --no-linters)
                INSTALL_LINTERS=false
                shift
                ;;
            --no-config)
                SETUP_CONFIG=false
                shift
                ;;
            --no-llm)
                SETUP_LLM=false
                shift
                ;;
            --help)
                echo "Aider Lint Fixer Installation Script"
                echo ""
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --venv          Create and use virtual environment"
                echo "  --source        Install from source instead of PyPI"
                echo "  --no-linters    Skip installing common linters"
                echo "  --no-config     Skip configuration setup"
                echo "  --no-llm        Skip LLM provider setup"
                echo "  --help          Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    print_banner
    
    check_prerequisites
    install_aider_lint_fixer
    
    if [ "$INSTALL_LINTERS" = "true" ]; then
        install_linters
    fi
    
    if [ "$SETUP_CONFIG" = "true" ]; then
        setup_configuration
    fi
    
    if [ "$SETUP_LLM" = "true" ]; then
        setup_llm_provider
    fi
    
    verify_installation
    print_usage_instructions
}

# Run main function
main "$@"

