#!/bin/bash
# Production Docker runner for aider-lint-fixer
# Simplifies running aider-lint-fixer in Docker for CI/CD and production use

set -e

# Configuration
IMAGE_NAME="aider-lint-fixer:latest"
CONTAINER_NAME="aider-lint-fixer-$(date +%s)"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() { echo -e "${BLUE}[DOCKER]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Show usage
usage() {
    cat << 'EOF'
aider-lint-fixer Docker Runner

Usage: ./scripts/containers/docker-run.sh [OPTIONS] [AIDER_ARGS...]

DESCRIPTION:
    Run aider-lint-fixer in a Docker container with your project mounted.
    Perfect for CI/CD pipelines and systems without Python 3.11+.

OPTIONS:
    --build                 Build the Docker image first
    --image IMAGE          Use specific image (default: aider-lint-fixer:latest)
    --env-file FILE        Load environment variables from file (default: .env)
    --api-key KEY          Set DEEPSEEK_API_KEY directly
    --workspace DIR        Set workspace directory (default: current directory)
    --output-dir DIR       Directory to write output files (default: ./output)
    --cache-dir DIR        Cache directory for learning features (default: ./.aider-lint-cache)
    --dry-run              Run without making changes (implies --no-ai)
    --interactive          Run in interactive mode (not suitable for CI)
    --ci                   Run in CI mode (non-interactive, structured output)
    --debug                Enable debug output
    --help, -h             Show this help

AIDER_ARGS:
    All additional arguments are passed to aider-lint-fixer.
    Use --help after -- to see aider-lint-fixer options.

EXAMPLES:
    # Basic usage - analyze current directory
    ./scripts/containers/docker-run.sh

    # Build image and run with specific linters
    ./scripts/containers/docker-run.sh --build --linters flake8,eslint

    # CI/CD usage with API key
    ./scripts/containers/docker-run.sh --ci --api-key sk-xxx --max-files 10

    # Dry run for testing
    ./scripts/containers/docker-run.sh --dry-run --verbose

    # Interactive mode with custom workspace
    ./scripts/containers/docker-run.sh --interactive --workspace /path/to/project

    # GitHub Actions usage
    ./scripts/containers/docker-run.sh --ci --linters flake8 --max-errors 5 \
        --output-dir ./lint-results

ENVIRONMENT VARIABLES:
    DEEPSEEK_API_KEY       DeepSeek API key for AI features
    OPENAI_API_KEY         OpenAI API key (alternative)
    ANTHROPIC_API_KEY      Anthropic API key (alternative)
    AIDER_LINT_FIXER_*     Any aider-lint-fixer configuration

CI/CD INTEGRATION:
    This script is designed to work seamlessly in CI/CD pipelines:
    - Exits with appropriate error codes
    - Provides structured output in CI mode
    - Handles output files for artifacts
    - Supports all major CI systems (GitHub Actions, GitLab CI, Jenkins, etc.)

EOF
}

# Check Docker availability
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    if ! docker info >/dev/null 2>&1; then
        error "Docker daemon is not running or accessible."
    fi
}

# Build Docker image
build_image() {
    local dockerfile="scripts/containers/Dockerfile.prod"
    
    log "Building Docker image: ${IMAGE_NAME}"
    
    if [[ ! -f "${dockerfile}" ]]; then
        error "Dockerfile not found: ${dockerfile}"
    fi
    
    docker build \
        -f "${dockerfile}" \
        -t "${IMAGE_NAME}" \
        --label "build-date=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --label "version=$(grep '^__version__' aider_lint_fixer/__init__.py | cut -d'"' -f2 2>/dev/null || echo 'unknown')" \
        .
    
    success "Docker image built successfully"
}

# Main function to run Docker container
run_docker() {
    local build_image=false
    local env_file=".env"
    local api_key=""
    local workspace="$(pwd)"
    local output_dir="./output"
    local cache_dir="./.aider-lint-cache"
    local dry_run=false
    local interactive=false
    local ci_mode=false
    local debug=false
    local custom_image=""
    local aider_args=()
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --build)
                build_image=true
                shift
                ;;
            --image)
                custom_image="$2"
                shift 2
                ;;
            --env-file)
                env_file="$2"
                shift 2
                ;;
            --api-key)
                api_key="$2"
                shift 2
                ;;
            --workspace)
                workspace="$2"
                shift 2
                ;;
            --output-dir)
                output_dir="$2"
                shift 2
                ;;
            --cache-dir)
                cache_dir="$2"
                shift 2
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --interactive)
                interactive=true
                shift
                ;;
            --ci)
                ci_mode=true
                shift
                ;;
            --debug)
                debug=true
                shift
                ;;
            --help|-h)
                usage
                exit 0
                ;;
            --)
                shift
                aider_args+=("$@")
                break
                ;;
            *)
                aider_args+=("$1")
                shift
                ;;
        esac
    done
    
    # Use custom image if provided
    if [[ -n "${custom_image}" ]]; then
        IMAGE_NAME="${custom_image}"
    fi
    
    # Build image if requested
    if [[ "${build_image}" == "true" ]]; then
        build_image
    fi
    
    # Check if image exists
    if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
        warn "Image ${IMAGE_NAME} not found. Building it now..."
        build_image
    fi
    
    # Prepare directories
    mkdir -p "${output_dir}"
    mkdir -p "${cache_dir}"
    
    # Prepare environment variables
    local env_args=()
    
    # Load environment file if exists
    if [[ -f "${env_file}" ]]; then
        log "Loading environment from: ${env_file}"
        env_args+=("--env-file" "${env_file}")
    elif [[ "${env_file}" != ".env" ]]; then
        warn "Environment file not found: ${env_file}"
    fi
    
    # Set API key if provided
    if [[ -n "${api_key}" ]]; then
        env_args+=("-e" "DEEPSEEK_API_KEY=${api_key}")
    fi
    
    # Set CI mode environment variables
    if [[ "${ci_mode}" == "true" ]]; then
        env_args+=("-e" "CI=true")
        env_args+=("-e" "AIDER_LINT_FIXER_NO_BANNER=true")
        env_args+=("-e" "PYTHONUNBUFFERED=1")
    fi
    
    # Set debug mode
    if [[ "${debug}" == "true" ]]; then
        env_args+=("-e" "AIDER_LINT_FIXER_DEBUG=true")
    fi
    
    # Prepare Docker run arguments
    local docker_args=(
        "--rm"
        "--name" "${CONTAINER_NAME}"
        "-v" "${workspace}:/workspace:ro"
        "-v" "${output_dir}:/output"
        "-v" "${cache_dir}:/workspace/.aider-lint-cache"
        "${env_args[@]}"
    )
    
    # Add interactive flag if needed
    if [[ "${interactive}" == "true" ]]; then
        docker_args+=("-it")
    fi
    
    # Prepare final aider-lint-fixer arguments
    local final_args=("/workspace")
    
    # Add dry-run if specified
    if [[ "${dry_run}" == "true" ]]; then
        final_args+=("--dry-run")
    fi
    
    # Add user-provided arguments
    final_args+=("${aider_args[@]}")
    
    # Log the command being executed
    log "Running aider-lint-fixer in Docker container"
    if [[ "${debug}" == "true" ]]; then
        echo "  Image: ${IMAGE_NAME}"
        echo "  Workspace: ${workspace}"
        echo "  Output: ${output_dir}"
        echo "  Cache: ${cache_dir}"
        echo "  Arguments: ${final_args[*]}"
    fi
    
    # Run the container
    docker run "${docker_args[@]}" "${IMAGE_NAME}" "${final_args[@]}"
    
    local exit_code=$?
    
    if [[ ${exit_code} -eq 0 ]]; then
        success "aider-lint-fixer completed successfully"
        if [[ -d "${output_dir}" ]] && [[ "$(ls -A "${output_dir}" 2>/dev/null)" ]]; then
            log "Output files available in: ${output_dir}"
        fi
    else
        error "aider-lint-fixer failed with exit code: ${exit_code}"
    fi
    
    return ${exit_code}
}

# Main script logic
main() {
    check_docker
    
    if [[ $# -eq 0 ]]; then
        log "No arguments provided. Running with default settings."
        log "Use --help for usage information."
        echo ""
    fi
    
    run_docker "$@"
}

main "$@"