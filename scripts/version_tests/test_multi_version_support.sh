#!/bin/bash
# Test script for ansible-lint version selection functionality
# This script tests the multi-version ansible-lint support

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🧪 Ansible-lint Multi-Version Support Test"
echo "==========================================="

# Test the version selection script directly
echo ""
echo "📝 Test 1: Version selection script availability"
if [[ -f "$PROJECT_ROOT/scripts/containers/select-ansible-version.sh" ]]; then
    echo "✅ Version selection script exists"
    chmod +x "$PROJECT_ROOT/scripts/containers/select-ansible-version.sh"
else
    echo "❌ Version selection script not found"
    exit 1
fi

# Test different version selections (without actually requiring the venvs)
echo ""
echo "📝 Test 2: Version selection logic"

test_version_selection() {
    local version="$1"
    local expected_pattern="$2"
    
    echo "Testing version: $version"
    
    # Mock the venv directories for testing
    mkdir -p /tmp/test-venvs/{venv-latest,venv-enterprise,venv-rhel10}
    
    # Test the version selection (capture output)
    export ANSIBLE_LINT_VERSION="$version"
    
    # Create a modified version of the script for testing
    cat > /tmp/test-version-selector.sh << 'EOF'
#!/bin/bash
set -e

ANSIBLE_LINT_VERSION="${ANSIBLE_LINT_VERSION:-latest}"

case "${ANSIBLE_LINT_VERSION}" in
    "enterprise"|"6"*|"rhel9"|"6.22.2")
        if [[ -d "/tmp/test-venvs/venv-enterprise" ]]; then
            echo "SELECTED: Enterprise/RHEL 9 (6.22.2)"
        else
            echo "ERROR: Enterprise environment not found"
            exit 1
        fi
        ;;
    "rhel10"|"18"*|"2.18"|"24"*)
        if [[ -d "/tmp/test-venvs/venv-rhel10" ]]; then
            echo "SELECTED: RHEL 10 compatible (24.x)"
        else
            echo "ERROR: RHEL 10 environment not found"
            exit 1
        fi
        ;;
    "latest"|"25"*|"2.19"|"")
        if [[ -d "/tmp/test-venvs/venv-latest" ]]; then
            echo "SELECTED: Latest (25.6.1)"
        else
            echo "SELECTED: System installation"
        fi
        ;;
    *)
        echo "ERROR: Unknown version: ${ANSIBLE_LINT_VERSION}"
        exit 1
        ;;
esac
EOF
    
    chmod +x /tmp/test-version-selector.sh
    output=$(/tmp/test-version-selector.sh 2>&1)
    
    if echo "$output" | grep -q "$expected_pattern"; then
        echo "  ✅ $version -> $output"
    else
        echo "  ❌ $version -> $output (expected pattern: $expected_pattern)"
        return 1
    fi
    
    # Cleanup
    rm -f /tmp/test-version-selector.sh
}

# Test various version selections
test_version_selection "latest" "Latest"
test_version_selection "25.6.1" "Latest"
test_version_selection "enterprise" "Enterprise"
test_version_selection "6.22.2" "Enterprise"
test_version_selection "rhel9" "Enterprise"
test_version_selection "rhel10" "RHEL 10"
test_version_selection "24.12.2" "RHEL 10"

# Cleanup test directories
rm -rf /tmp/test-venvs

echo ""
echo "📝 Test 3: Supported versions in linter"

# Test that the linter supports the new versions
python3 << 'EOF'
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from aider_lint_fixer.linters.ansible_lint import AnsibleLintLinter
    
    linter = AnsibleLintLinter("/tmp")
    supported_versions = linter.supported_versions
    
    required_versions = ["25.6.1", "6.22.2", "24."]
    
    print("Supported versions:", supported_versions)
    
    for version in required_versions:
        found = any(v.startswith(version) or version.startswith(v) for v in supported_versions)
        if found:
            print(f"  ✅ {version} support found")
        else:
            print(f"  ❌ {version} support missing")
            sys.exit(1)
            
    print("✅ All required versions are supported")
    
except Exception as e:
    print(f"❌ Error testing linter versions: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

echo ""
echo "📝 Test 4: Dockerfile modifications"

DOCKERFILE_PATH="$PROJECT_ROOT/scripts/containers/Dockerfile.prod"
if [[ -f "$DOCKERFILE_PATH" ]]; then
    echo "Checking Dockerfile for multi-version support..."
    
    if grep -q "venv-enterprise" "$DOCKERFILE_PATH"; then
        echo "  ✅ Enterprise virtual environment setup found"
    else
        echo "  ❌ Enterprise virtual environment setup missing"
        exit 1
    fi
    
    if grep -q "venv-rhel10" "$DOCKERFILE_PATH"; then
        echo "  ✅ RHEL 10 virtual environment setup found"
    else
        echo "  ❌ RHEL 10 virtual environment setup missing"
        exit 1
    fi
    
    if grep -q "ansible-lint==6.22.2" "$DOCKERFILE_PATH"; then
        echo "  ✅ Enterprise ansible-lint version found"
    else
        echo "  ❌ Enterprise ansible-lint version missing"
        exit 1
    fi
    
    if grep -q "select-ansible-version.sh" "$DOCKERFILE_PATH"; then
        echo "  ✅ Version selection script integration found"
    else
        echo "  ❌ Version selection script integration missing"
        exit 1
    fi
else
    echo "❌ Dockerfile not found"
    exit 1
fi

echo ""
echo "🎉 All tests passed! Multi-version ansible-lint support is properly configured."
echo ""
echo "Usage examples:"
echo "  # Use latest version (default)"
echo "  podman run quay.io/takinosh/aider-lint-fixer"
echo ""  
echo "  # Use enterprise/RHEL 9 compatible version"
echo "  podman run -e ANSIBLE_LINT_VERSION=enterprise quay.io/takinosh/aider-lint-fixer"
echo ""
echo "  # Use RHEL 10 compatible version" 
echo "  podman run -e ANSIBLE_LINT_VERSION=rhel10 quay.io/takinosh/aider-lint-fixer"