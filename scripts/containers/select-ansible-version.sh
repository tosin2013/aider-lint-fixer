#!/bin/bash
# Ansible-lint version selection script
# Selects the appropriate ansible-lint version based on environment variable

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo -e "${BLUE}[ansible-version-selector]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Default to latest if not specified
ANSIBLE_LINT_VERSION="${ANSIBLE_LINT_VERSION:-latest}"

case "${ANSIBLE_LINT_VERSION}" in
    "enterprise"|"6"*|"rhel9"|"6.22.2")
        if [[ -d "/opt/venv-enterprise" ]]; then
            export PATH="/opt/venv-enterprise/bin:$PATH"
            log "Using ansible-lint 6.22.2 (Enterprise/RHEL 9 compatible)"
            log "ansible-core: 2.15.13 (Enterprise compatible)"
        else
            error "Enterprise ansible-lint environment not found"
            error "This container may not support enterprise versions"
            exit 1
        fi
        ;;
    "rhel10"|"18"*|"2.18"|"24"*)
        if [[ -d "/opt/venv-rhel10" ]]; then
            export PATH="/opt/venv-rhel10/bin:$PATH"
            log "Using ansible-lint with ansible-core 2.18 (RHEL 10 compatible)"
        else
            error "RHEL 10 ansible-lint environment not found"
            error "This container may not support RHEL 10 versions"
            exit 1
        fi
        ;;
    "latest"|"25"*|"2.19"|"")
        if [[ -d "/opt/venv-latest" ]]; then
            export PATH="/opt/venv-latest/bin:$PATH"
            log "Using ansible-lint 25.6.1 (Latest - Technology Preview only)"
            log "ansible-core: 2.19.0 (Not supported on RHEL 10)"
        else
            # Fallback to system installation
            log "Using system ansible-lint installation"
        fi
        ;;
    *)
        error "Unknown ANSIBLE_LINT_VERSION: ${ANSIBLE_LINT_VERSION}"
        error "Supported values:"
        error "  - latest, 25.6.1, 25.* : Latest version (Technology Preview)"
        error "  - enterprise, rhel9, 6.22.2, 6.* : Enterprise/RHEL 9 compatible"
        error "  - rhel10, 24.*, 2.18 : RHEL 10 compatible"
        exit 1
        ;;
esac

# Verify ansible-lint is available
if ! command -v ansible-lint >/dev/null 2>&1; then
    error "ansible-lint not found in PATH after version selection"
    error "PATH: $PATH"
    exit 1
fi

# Show version information if debug mode is enabled
if [[ "${AIDER_LINT_FIXER_DEBUG}" == "true" ]]; then
    log "Version Information:"
    echo "  ansible-lint: $(ansible-lint --version 2>/dev/null | head -1 || echo 'Version check failed')"
    echo "  PATH: $PATH"
    echo "  Selected version: ${ANSIBLE_LINT_VERSION}"
fi

# Export the PATH for subsequent commands
export PATH