#!/bin/bash
# Development container management script for aider-lint-fixer
# Provides easy Podman-based development environment

set -e

# Configuration
CONTAINER_NAME="aider-lint-fixer-dev"
IMAGE_NAME="aider-lint-fixer:dev"
CONTAINERFILE="scripts/containers/Containerfile.dev"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() { echo -e "${BLUE}[DEV]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Show usage
usage() {
    echo "aider-lint-fixer Development Container Manager"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  build          Build the development container image"
    echo "  run            Run development container (interactive)"
    echo "  shell          Start interactive shell in container"
    echo "  exec <cmd>     Execute command in running container"
    echo "  stop           Stop the running container"
    echo "  remove         Remove the container (keeps image)"
    echo "  clean          Remove container and image"
    echo "  rebuild        Clean build (remove + build)"
    echo "  logs           Show container logs"
    echo "  status         Show container status"
    echo ""
    echo "Options (for run command):"
    echo "  --env-file     Use specific .env file (default: .env)"
    echo "  --api-key      Set DEEPSEEK_API_KEY directly"
    echo "  --mount        Additional volume mount (format: host:container)"
    echo ""
    echo "Examples:"
    echo "  $0 build                     # Build development image"
    echo "  $0 run                       # Start interactive development session"
    echo "  $0 shell                     # Get shell access"
    echo "  $0 exec 'make test'          # Run tests"
    echo "  $0 run --api-key sk-xxx      # Run with API key"
}

# Check if podman is available
check_podman() {
    if ! command -v podman &> /dev/null; then
        error "Podman is not installed. Please install podman first."
    fi
}

# Build development image
build_image() {
    log "Building development image: ${IMAGE_NAME}"
    
    if [[ ! -f "${CONTAINERFILE}" ]]; then
        error "Containerfile not found: ${CONTAINERFILE}"
    fi
    
    # Build with context from project root
    podman build \
        -f "${CONTAINERFILE}" \
        -t "${IMAGE_NAME}" \
        --label "build-date=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --label "version=$(grep '^__version__' aider_lint_fixer/__init__.py | cut -d'"' -f2 2>/dev/null || echo 'unknown')" \
        .
    
    success "Development image built successfully"
}

# Run development container
run_container() {
    log "Starting development container: ${CONTAINER_NAME}"
    
    # Stop existing container if running
    if podman container exists "${CONTAINER_NAME}" 2>/dev/null; then
        warn "Stopping existing container"
        podman stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
        podman rm "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    fi
    
    # Prepare environment variables
    local env_args=()
    local env_file=".env"
    local api_key=""
    local extra_mounts=()
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --env-file)
                env_file="$2"
                shift 2
                ;;
            --api-key)
                api_key="$2"
                shift 2
                ;;
            --mount)
                extra_mounts+=("$2")
                shift 2
                ;;
            *)
                warn "Unknown option: $1"
                shift
                ;;
        esac
    done
    
    # Load environment file if exists
    if [[ -f "${env_file}" ]]; then
        log "Loading environment from: ${env_file}"
        while IFS= read -r line; do
            if [[ ! "${line}" =~ ^#.* ]] && [[ -n "${line}" ]]; then
                env_args+=("-e" "${line}")
            fi
        done < "${env_file}"
    else
        warn "Environment file not found: ${env_file}"
    fi
    
    # Override API key if provided
    if [[ -n "${api_key}" ]]; then
        env_args+=("-e" "DEEPSEEK_API_KEY=${api_key}")
    fi
    
    # Default volume mounts
    local volume_args=(
        "-v" "$(pwd):/workspace:Z"
        "-v" "$(pwd)/.aider-lint-cache:/workspace/.aider-lint-cache:Z"
    )
    
    # Add extra mounts
    for mount in "${extra_mounts[@]}"; do
        volume_args+=("-v" "${mount}:Z")
    done
    
    # Run container interactively
    podman run \
        --name "${CONTAINER_NAME}" \
        --rm \
        -it \
        "${env_args[@]}" \
        "${volume_args[@]}" \
        -w /workspace \
        "${IMAGE_NAME}" \
        bash
    
    success "Development session completed"
}

# Start shell in running container
start_shell() {
    if ! podman container exists "${CONTAINER_NAME}" 2>/dev/null; then
        error "Container ${CONTAINER_NAME} is not running. Use 'run' command first."
    fi
    
    log "Starting shell in container: ${CONTAINER_NAME}"
    podman exec -it "${CONTAINER_NAME}" bash
}

# Execute command in container
exec_command() {
    local cmd="$1"
    if [[ -z "${cmd}" ]]; then
        error "No command specified for exec"
    fi
    
    if ! podman container exists "${CONTAINER_NAME}" 2>/dev/null; then
        error "Container ${CONTAINER_NAME} is not running. Use 'run' command first."
    fi
    
    log "Executing in container: ${cmd}"
    podman exec -it "${CONTAINER_NAME}" bash -c "${cmd}"
}

# Stop container
stop_container() {
    if podman container exists "${CONTAINER_NAME}" 2>/dev/null; then
        log "Stopping container: ${CONTAINER_NAME}"
        podman stop "${CONTAINER_NAME}"
        success "Container stopped"
    else
        warn "Container ${CONTAINER_NAME} is not running"
    fi
}

# Remove container
remove_container() {
    if podman container exists "${CONTAINER_NAME}" 2>/dev/null; then
        log "Removing container: ${CONTAINER_NAME}"
        podman stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
        podman rm "${CONTAINER_NAME}"
        success "Container removed"
    else
        warn "Container ${CONTAINER_NAME} does not exist"
    fi
}

# Clean everything
clean_all() {
    log "Cleaning container and image"
    remove_container
    
    if podman image exists "${IMAGE_NAME}" 2>/dev/null; then
        log "Removing image: ${IMAGE_NAME}"
        podman rmi "${IMAGE_NAME}"
        success "Image removed"
    else
        warn "Image ${IMAGE_NAME} does not exist"
    fi
}

# Show container status
show_status() {
    log "Container Status"
    echo ""
    
    if podman image exists "${IMAGE_NAME}" 2>/dev/null; then
        echo "Image: ✅ ${IMAGE_NAME} exists"
        podman images "${IMAGE_NAME}" --format "table {{.Repository}}:{{.Tag}}\t{{.Created}}\t{{.Size}}"
    else
        echo "Image: ❌ ${IMAGE_NAME} not found"
    fi
    
    echo ""
    
    if podman container exists "${CONTAINER_NAME}" 2>/dev/null; then
        echo "Container: ✅ ${CONTAINER_NAME} exists"
        podman ps -a --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Created}}"
    else
        echo "Container: ❌ ${CONTAINER_NAME} not found"
    fi
}

# Show logs
show_logs() {
    if podman container exists "${CONTAINER_NAME}" 2>/dev/null; then
        log "Showing logs for: ${CONTAINER_NAME}"
        podman logs "${CONTAINER_NAME}"
    else
        warn "Container ${CONTAINER_NAME} does not exist"
    fi
}

# Main script logic
main() {
    check_podman
    
    if [[ $# -eq 0 ]]; then
        usage
        exit 0
    fi
    
    local command="$1"
    shift
    
    case "${command}" in
        build)
            build_image
            ;;
        run)
            run_container "$@"
            ;;
        shell)
            start_shell
            ;;
        exec)
            exec_command "$*"
            ;;
        stop)
            stop_container
            ;;
        remove)
            remove_container
            ;;
        clean)
            clean_all
            ;;
        rebuild)
            clean_all
            build_image
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            error "Unknown command: ${command}. Use '--help' for usage information."
            ;;
    esac
}

main "$@"