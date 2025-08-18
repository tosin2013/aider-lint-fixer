#!/bin/bash
# Container setup script for aider-lint-fixer
# Automates initial setup for both Podman and Docker environments

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Logging functions
log() { echo -e "${BLUE}[SETUP]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
info() { echo -e "${PURPLE}[INFO]${NC} $1"; }

# Show banner
show_banner() {
    cat << 'EOF'
    ╔══════════════════════════════════════════════════════════════╗
    ║                aider-lint-fixer Container Setup              ║
    ║                                                              ║
    ║  Automated setup for Podman (dev) and Docker (production)   ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
EOF
    echo ""
}

# Show usage
usage() {
    cat << 'EOF'
Container Setup for aider-lint-fixer

Usage: ./scripts/containers/setup-containers.sh [OPTIONS]

OPTIONS:
    --podman-only      Setup only Podman development environment
    --docker-only      Setup only Docker production environment
    --no-build         Skip building images (just setup scripts)
    --env-setup        Setup environment file (.env)
    --check-deps       Check system dependencies
    --help, -h         Show this help

WHAT THIS SCRIPT DOES:
    1. Check system dependencies (Podman/Docker)
    2. Make container scripts executable
    3. Setup environment file if needed
    4. Build container images
    5. Verify installations
    6. Provide usage instructions

EXAMPLES:
    ./scripts/containers/setup-containers.sh           # Full setup
    ./scripts/containers/setup-containers.sh --podman-only
    ./scripts/containers/setup-containers.sh --docker-only
    ./scripts/containers/setup-containers.sh --check-deps

EOF
}

# Check system dependencies
check_dependencies() {
    log "Checking system dependencies..."
    
    local has_podman=false
    local has_docker=false
    local missing_deps=()
    
    # Check Podman
    if command -v podman &> /dev/null; then
        has_podman=true
        info "✅ Podman found: $(podman --version)"
    else
        missing_deps+=("podman")
        warn "❌ Podman not found"
    fi
    
    # Check Docker
    if command -v docker &> /dev/null; then
        if docker info >/dev/null 2>&1; then
            has_docker=true
            info "✅ Docker found: $(docker --version)"
        else
            warn "❌ Docker found but daemon not running"
        fi
    else
        missing_deps+=("docker")
        warn "❌ Docker not found"
    fi
    
    # Check other dependencies
    local other_tools=("git" "curl" "bash")
    for tool in "${other_tools[@]}"; do
        if command -v "${tool}" &> /dev/null; then
            info "✅ ${tool} found"
        else
            missing_deps+=("${tool}")
            warn "❌ ${tool} not found"
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        warn "Missing dependencies: ${missing_deps[*]}"
        echo ""
        echo "Installation instructions:"
        
        if [[ " ${missing_deps[*]} " =~ " podman " ]]; then
            echo ""
            echo "📦 Podman installation:"
            echo "  RHEL/CentOS/Fedora: sudo dnf install podman"
            echo "  Ubuntu/Debian:      sudo apt install podman"
            echo "  macOS:              brew install podman"
        fi
        
        if [[ " ${missing_deps[*]} " =~ " docker " ]]; then
            echo ""
            echo "🐳 Docker installation:"
            echo "  Visit: https://docs.docker.com/get-docker/"
            echo "  RHEL/CentOS:        sudo dnf install docker"
            echo "  Ubuntu/Debian:      sudo apt install docker.io"
            echo "  macOS:              brew install docker"
        fi
        
        echo ""
        return 1
    fi
    
    return 0
}

# Make scripts executable
setup_scripts() {
    log "Setting up container scripts..."
    
    local scripts=(
        "scripts/containers/dev-container.sh"
        "scripts/containers/docker-run.sh"
        "scripts/containers/setup-containers.sh"
        "scripts/containers/docker-entrypoint.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [[ -f "${script}" ]]; then
            chmod +x "${script}"
            info "✅ Made ${script} executable"
        else
            warn "❌ Script not found: ${script}"
        fi
    done
}

# Setup environment file
setup_environment() {
    log "Setting up environment file..."
    
    local env_file=".env"
    local env_example=".env.example"
    
    if [[ -f "${env_file}" ]]; then
        info "✅ Environment file already exists: ${env_file}"
        
        # Check if it contains template values
        if grep -q "your_.*_api_key_here" "${env_file}" 2>/dev/null; then
            warn "⚠️  Environment file contains template values"
            echo "   Please edit ${env_file} and add your actual API keys"
        else
            info "✅ Environment file appears configured"
        fi
    else
        if [[ -f "${env_example}" ]]; then
            cp "${env_example}" "${env_file}"
            success "Created ${env_file} from template"
            warn "⚠️  Please edit ${env_file} and add your API keys"
        else
            # Create basic environment file
            cat > "${env_file}" << 'EOF'
# aider-lint-fixer Environment Configuration
# Copy this file to .env and fill in your API keys

# Primary API key (choose one)
DEEPSEEK_API_KEY=your_deepseek_api_key_here
#OPENAI_API_KEY=your_openai_api_key_here
#ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: aider-lint-fixer settings
#AIDER_LINT_FIXER_LOG_LEVEL=INFO
#AIDER_LINT_FIXER_MAX_FILES=10
#AIDER_LINT_FIXER_MAX_ERRORS=5
#AIDER_LINT_FIXER_NO_BANNER=false
EOF
            success "Created basic ${env_file} template"
            warn "⚠️  Please edit ${env_file} and add your API keys"
        fi
    fi
}

# Build Podman development image
build_podman_image() {
    log "Building Podman development image..."
    
    if command -v podman &> /dev/null; then
        ./scripts/containers/dev-container.sh build
        success "Podman development image built"
    else
        warn "Podman not available, skipping development image build"
        return 1
    fi
}

# Build Docker production image
build_docker_image() {
    log "Building Docker production image..."
    
    if command -v docker &> /dev/null && docker info >/dev/null 2>&1; then
        ./scripts/containers/docker-run.sh --build
        success "Docker production image built"
    else
        warn "Docker not available or not running, skipping production image build"
        return 1
    fi
}

# Verify installations
verify_setup() {
    log "Verifying container setup..."
    
    local verification_passed=true
    
    # Test Podman setup
    if command -v podman &> /dev/null; then
        if podman image exists "aider-lint-fixer:dev" 2>/dev/null; then
            info "✅ Podman development image ready"
            
            # Quick test
            if podman run --rm "aider-lint-fixer:dev" --version >/dev/null 2>&1; then
                info "✅ Podman image functional"
            else
                warn "⚠️  Podman image exists but may have issues"
                verification_passed=false
            fi
        else
            warn "❌ Podman development image not found"
            verification_passed=false
        fi
    fi
    
    # Test Docker setup
    if command -v docker &> /dev/null && docker info >/dev/null 2>&1; then
        if docker image inspect "aider-lint-fixer:latest" >/dev/null 2>&1; then
            info "✅ Docker production image ready"
            
            # Quick test
            if docker run --rm "aider-lint-fixer:latest" --version >/dev/null 2>&1; then
                info "✅ Docker image functional"
            else
                warn "⚠️  Docker image exists but may have issues"
                verification_passed=false
            fi
        else
            warn "❌ Docker production image not found"
            verification_passed=false
        fi
    fi
    
    if [[ "${verification_passed}" == "true" ]]; then
        success "Container setup verification passed"
        return 0
    else
        warn "Some issues found during verification"
        return 1
    fi
}

# Show usage instructions
show_instructions() {
    cat << 'EOF'

╔═══════════════════════════════════════════════════════════════════════════════╗
║                            SETUP COMPLETE!                                   ║
║                                                                               ║
║  Your aider-lint-fixer container environment is ready to use.                ║
╚═══════════════════════════════════════════════════════════════════════════════╝

🚀 QUICK START:

   Development (Podman):
   └─ ./scripts/containers/dev-container.sh run

   Production (Docker):
   └─ ./scripts/containers/docker-run.sh

   Get Help:
   └─ ./scripts/containers/dev-container.sh --help
   └─ ./scripts/containers/docker-run.sh --help

📋 NEXT STEPS:

   1. Edit .env file and add your API keys:
      └─ vim .env

   2. Start development session:
      └─ ./scripts/containers/dev-container.sh run

   3. Or run on your project:
      └─ ./scripts/containers/docker-run.sh --linters flake8,eslint

🔧 COMMON COMMANDS:

   # Development workflow
   ./scripts/containers/dev-container.sh run
   ./scripts/containers/dev-container.sh shell
   ./scripts/containers/dev-container.sh exec 'make test'

   # Production usage
   ./scripts/containers/docker-run.sh --dry-run
   ./scripts/containers/docker-run.sh --ci --linters flake8
   ./scripts/containers/docker-run.sh --interactive

📚 Documentation: See scripts/docs/CONTAINER_GUIDE.md

EOF
}

# Main setup function
main() {
    local podman_only=false
    local docker_only=false
    local no_build=false
    local env_setup_only=false
    local check_deps_only=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --podman-only)
                podman_only=true
                shift
                ;;
            --docker-only)
                docker_only=true
                shift
                ;;
            --no-build)
                no_build=true
                shift
                ;;
            --env-setup)
                env_setup_only=true
                shift
                ;;
            --check-deps)
                check_deps_only=true
                shift
                ;;
            --help|-h)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1. Use --help for usage."
                ;;
        esac
    done
    
    show_banner
    
    # Check dependencies only
    if [[ "${check_deps_only}" == "true" ]]; then
        check_dependencies
        exit $?
    fi
    
    # Environment setup only
    if [[ "${env_setup_only}" == "true" ]]; then
        setup_environment
        exit $?
    fi
    
    # Check dependencies
    if ! check_dependencies; then
        error "Please install missing dependencies first"
    fi
    
    # Setup scripts
    setup_scripts
    
    # Setup environment
    setup_environment
    
    # Build images if requested
    if [[ "${no_build}" != "true" ]]; then
        local build_podman=true
        local build_docker=true
        
        if [[ "${docker_only}" == "true" ]]; then
            build_podman=false
        elif [[ "${podman_only}" == "true" ]]; then
            build_docker=false
        fi
        
        if [[ "${build_podman}" == "true" ]]; then
            build_podman_image || warn "Podman image build failed"
        fi
        
        if [[ "${build_docker}" == "true" ]]; then
            build_docker_image || warn "Docker image build failed"
        fi
        
        # Verify setup
        verify_setup || warn "Verification had issues"
    fi
    
    # Show instructions
    show_instructions
    
    success "Container setup completed successfully!"
}

main "$@"