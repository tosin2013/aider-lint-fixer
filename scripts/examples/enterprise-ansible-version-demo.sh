#!/bin/bash
# Example usage script demonstrating ansible-lint version selection
# This script shows how to use the new multi-version ansible-lint support

set -e

echo "🏢 Enterprise Ansible-lint Version Selection Demo"
echo "================================================="
echo ""
echo "This script demonstrates the new multi-version ansible-lint support"
echo "that addresses RHEL 9/10 enterprise compatibility issues."
echo ""

# Function to show usage example
show_usage_example() {
    local version="$1"
    local description="$2"
    local use_case="$3"
    
    echo "📋 $description"
    echo "   Use case: $use_case"
    echo "   Command:"
    echo "   podman run -e ANSIBLE_LINT_VERSION=$version \\"
    echo "     -v \$(pwd):/workspace:Z \\"
    echo "     quay.io/takinosh/aider-lint-fixer"
    echo ""
}

echo "Available ansible-lint versions:"
echo ""

show_usage_example "enterprise" \
    "Enterprise/RHEL 9 Compatible (ansible-lint 6.22.2 + ansible-core 2.15.13)" \
    "Production environments, RHEL 9 systems, enterprise standards"

show_usage_example "rhel10" \
    "RHEL 10 Compatible (ansible-lint 24.12.2 + ansible-core 2.18.8)" \
    "RHEL 10 systems (ansible-core 2.19 NOT supported on RHEL 10)"

show_usage_example "latest" \
    "Latest Version (ansible-lint 25.6.1 + ansible-core 2.19.0)" \
    "Technology Preview only, modern development environments"

echo "🔧 Alternative Version Specifications:"
echo ""
echo "You can also specify versions directly:"
echo "  ANSIBLE_LINT_VERSION=6.22.2   # Specific enterprise version"
echo "  ANSIBLE_LINT_VERSION=6.*       # Any 6.x version"
echo "  ANSIBLE_LINT_VERSION=rhel9     # Alias for enterprise"
echo "  ANSIBLE_LINT_VERSION=24.*      # Any 24.x version"
echo ""

echo "⚠️  Important Notes:"
echo "  • RHEL 10 does NOT support ansible-core 2.19"
echo "  • Enterprise environments typically use ansible-lint 6.x"
echo "  • Use 'enterprise' version for consistency with RHEL 9 environments"
echo "  • Use 'rhel10' version for RHEL 10 compatibility"
echo "  • Use 'latest' version only for testing (Technology Preview)"
echo ""

echo "📊 Version Compatibility Matrix:"
echo ""
echo "| Environment        | ansible-lint | ansible-core | Supported RHEL |"
echo "|--------------------|--------------|--------------|----------------|"
echo "| Enterprise/RHEL 9  | 6.22.2       | 2.15.13      | RHEL 9         |"
echo "| RHEL 10 Compatible | 24.12.2      | 2.18.8       | RHEL 10        |"
echo "| Latest (Preview)   | 25.6.1       | 2.19.0       | None (Preview) |"
echo ""

echo "🚀 Quick Start for Enterprise Users:"
echo ""
echo "1. For RHEL 9 / Enterprise environments:"
echo "   export ANSIBLE_LINT_VERSION=enterprise"
echo ""
echo "2. For RHEL 10 environments:"
echo "   export ANSIBLE_LINT_VERSION=rhel10"
echo ""
echo "3. Run aider-lint-fixer:"
echo "   podman run -e ANSIBLE_LINT_VERSION=\$ANSIBLE_LINT_VERSION \\"
echo "     -v \$(pwd):/workspace:Z \\"
echo "     quay.io/takinosh/aider-lint-fixer"
echo ""

echo "✅ This resolves the major ansible-lint version mismatch issue"
echo "   between enterprise environments and the latest container versions!"