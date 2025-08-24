#!/bin/bash
# Docker entrypoint script for aider-lint-fixer
# Handles environment setup and command execution

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo -e "${BLUE}[aider-lint-fixer]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if we're running in a CI environment
if [[ "${CI}" == "true" ]] || [[ "${GITHUB_ACTIONS}" == "true" ]]; then
    log "Running in CI environment"
    export AIDER_LINT_FIXER_NO_BANNER=true
    export PYTHONUNBUFFERED=1
fi

# Validate required environment variables for AI features
if [[ -z "${DEEPSEEK_API_KEY}" ]] && [[ -z "${OPENAI_API_KEY}" ]] && [[ -z "${ANTHROPIC_API_KEY}" ]]; then
    if [[ "$1" != "--help" ]] && [[ "$1" != "--version" ]] && [[ "$1" != "--dry-run"* ]]; then
        warn "No API keys found in environment variables"
        warn "Set one of: DEEPSEEK_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY"
        warn "Or use --dry-run for testing without AI features"
    fi
fi

# Check if workspace is mounted
if [[ ! -d "/workspace" ]] || [[ -z "$(ls -A /workspace 2>/dev/null)" ]]; then
    if [[ "$1" != "--help" ]] && [[ "$1" != "--version" ]]; then
        warn "Workspace appears empty. Mount your project with: -v \$(pwd):/workspace"
    fi
fi

# Set up cache directory permissions
if [[ -d "/workspace/.aider-lint-cache" ]]; then
    # Use mounted cache if available
    export AIDER_LINT_CACHE_DIR="/workspace/.aider-lint-cache"
else
    # Use container cache
    export AIDER_LINT_CACHE_DIR="/app/.aider-lint-cache"
fi

# Ensure cache directory exists and is writable
mkdir -p "${AIDER_LINT_CACHE_DIR}"

# Set up ansible temp directories and ensure they're writable
# Set default ansible environment variables if not already set
if [[ -z "${ANSIBLE_LOCAL_TEMP}" ]]; then
    export ANSIBLE_LOCAL_TEMP="/tmp/ansible-local"
fi
if [[ -z "${ANSIBLE_REMOTE_TEMP}" ]]; then
    export ANSIBLE_REMOTE_TEMP="/tmp/ansible-local"  
fi
if [[ -z "${ANSIBLE_GALAXY_CACHE_DIR}" ]]; then
    export ANSIBLE_GALAXY_CACHE_DIR="/tmp/ansible-galaxy-cache"
fi
if [[ -z "${ANSIBLE_LOG_PATH}" ]]; then
    export ANSIBLE_LOG_PATH="/tmp/ansible.log"
fi

# Ensure ansible temp directories exist and are writable
for ansible_dir in "${ANSIBLE_LOCAL_TEMP}" "${ANSIBLE_REMOTE_TEMP}" "${ANSIBLE_GALAXY_CACHE_DIR}"; do
    if [[ -n "${ansible_dir}" ]]; then
        mkdir -p "${ansible_dir}" 2>/dev/null || true
        if [[ ! -w "${ansible_dir}" ]]; then
            warn "Ansible temp directory ${ansible_dir} is not writable"
            # Try to create in /tmp as fallback
            fallback_dir="/tmp/$(basename "${ansible_dir}")"
            mkdir -p "${fallback_dir}" 2>/dev/null || true
            if [[ -w "${fallback_dir}" ]]; then
                log "Using fallback ansible temp directory: ${fallback_dir}"
                case "${ansible_dir}" in
                    "${ANSIBLE_LOCAL_TEMP}")
                        export ANSIBLE_LOCAL_TEMP="${fallback_dir}"
                        ;;
                    "${ANSIBLE_REMOTE_TEMP}")
                        export ANSIBLE_REMOTE_TEMP="${fallback_dir}"
                        ;;
                    "${ANSIBLE_GALAXY_CACHE_DIR}")
                        export ANSIBLE_GALAXY_CACHE_DIR="${fallback_dir}"
                        ;;
                esac
            fi
        fi
    fi
done

# Version info logging
if [[ "${AIDER_LINT_FIXER_DEBUG}" == "true" ]]; then
    log "Container Environment:"
    echo "  Python: $(python --version)"
    echo "  Node.js: $(node --version 2>/dev/null || echo 'Not available')"
    echo "  aider-lint-fixer: $(python -m aider_lint_fixer --version)"
    echo "  Working directory: $(pwd)"
    echo "  Cache directory: ${AIDER_LINT_CACHE_DIR}"
    echo "  Ansible Local Temp: ${ANSIBLE_LOCAL_TEMP:-'Not set'}"
    echo "  Ansible Remote Temp: ${ANSIBLE_REMOTE_TEMP:-'Not set'}"
    echo "  Ansible Galaxy Cache: ${ANSIBLE_GALAXY_CACHE_DIR:-'Not set'}"
    echo "  Ansible Log Path: ${ANSIBLE_LOG_PATH:-'Not set'}"
    echo "  Mounted files: $(ls -la /workspace 2>/dev/null | wc -l) entries"
    echo "  Ansible-lint availability: $(ansible-lint --version 2>&1 | head -1 || echo 'Not available')"
fi

# Handle special commands
case "$1" in
    --help|help|-h)
        exec python -m aider_lint_fixer --help
        ;;
    --version|version|-v)
        exec python -m aider_lint_fixer --version
        ;;
    --stats|stats)
        exec python -m aider_lint_fixer --stats
        ;;
    bash|shell)
        log "Starting interactive shell"
        exec bash
        ;;
    test)
        log "Running self-test"
        exec python -m aider_lint_fixer /workspace --dry-run --verbose --linters flake8 "${@:2}"
        ;;
esac

# Default behavior: run aider-lint-fixer with provided arguments
# If no arguments provided, show help
if [[ $# -eq 0 ]]; then
    log "No arguments provided, showing help"
    exec python -m aider_lint_fixer --help
else
    log "Running aider-lint-fixer with arguments: $*"
    exec python -m aider_lint_fixer "$@"
fi