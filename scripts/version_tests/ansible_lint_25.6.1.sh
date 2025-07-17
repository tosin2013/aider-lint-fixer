#!/bin/bash
# Version-specific test for ansible-lint 25.6.1
# This script validates that our ansible-lint integration works correctly
# with this specific version.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🧪 Ansible-lint 25.6.1 Integration Test"
echo "======================================="

# Check version
EXPECTED_VERSION="25.6.1"
ACTUAL_VERSION=$(ansible-lint --version | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -1)

if [[ "$ACTUAL_VERSION" != "$EXPECTED_VERSION" ]]; then
    echo "⚠️  Warning: Expected version $EXPECTED_VERSION, found $ACTUAL_VERSION"
    echo "   This test was designed for $EXPECTED_VERSION"
fi

echo "✅ ansible-lint version: $ACTUAL_VERSION"

# Create test directory
TEST_DIR=$(mktemp -d)
echo "📁 Test directory: $TEST_DIR"
cd "$TEST_DIR"

# Test 1: Basic profile with problematic playbook
echo ""
echo "📝 Test 1: Basic profile error detection"
cat > test_basic.yml << 'EOF'
---
- hosts: localhost
  tasks:
  - shell: echo "test"
  - debug: msg="test"
EOF

echo "Running: ansible-lint --format=json --strict --profile=basic test_basic.yml"
if ansible-lint --format=json --strict --profile=basic test_basic.yml > basic_output.json 2>&1; then
    echo "❌ Expected errors but got success"
    exit 1
else
    # Extract JSON from output (it's at the end after warnings)
    JSON_CONTENT=$(grep -E '^\[.*\]$' basic_output.json | tail -1)
    if [[ -n "$JSON_CONTENT" ]]; then
        ERROR_COUNT=$(echo "$JSON_CONTENT" | jq '. | length' 2>/dev/null || echo "0")
        echo "✅ Found $ERROR_COUNT errors (expected > 0)"

        if [[ "$ERROR_COUNT" -eq 0 ]]; then
            echo "❌ No errors found, but expected some"
            echo "Full output:"
            cat basic_output.json
            exit 1
        fi
    else
        echo "❌ No JSON found in output"
        echo "Full output:"
        cat basic_output.json
        exit 1
    fi
fi

# Test 2: Production profile (should find more errors)
echo ""
echo "📝 Test 2: Production profile error detection"
echo "Running: ansible-lint --format=json --strict --profile=production test_basic.yml"
if ansible-lint --format=json --strict --profile=production test_basic.yml > production_output.json 2>&1; then
    echo "❌ Expected errors but got success"
    exit 1
else
    # Extract JSON from output
    PROD_JSON_CONTENT=$(grep -E '^\[.*\]$' production_output.json | tail -1)
    if [[ -n "$PROD_JSON_CONTENT" ]]; then
        PROD_ERROR_COUNT=$(echo "$PROD_JSON_CONTENT" | jq '. | length' 2>/dev/null || echo "0")
        echo "✅ Found $PROD_ERROR_COUNT errors with production profile"

        if [[ "$PROD_ERROR_COUNT" -le "$ERROR_COUNT" ]]; then
            echo "⚠️  Warning: Production profile should find more errors than basic"
        fi
    else
        echo "❌ No JSON found in production output"
        exit 1
    fi
fi

# Test 3: JSON structure validation
echo ""
echo "📝 Test 3: JSON output structure validation"
FIRST_ERROR=$(echo "$JSON_CONTENT" | jq '.[0]' 2>/dev/null)
if [[ "$FIRST_ERROR" == "null" ]]; then
    echo "❌ No errors in JSON output"
    exit 1
fi

# Check required fields
REQUIRED_FIELDS=("type" "check_name" "severity" "description" "location")
for field in "${REQUIRED_FIELDS[@]}"; do
    if ! echo "$FIRST_ERROR" | jq -e ".$field" > /dev/null 2>&1; then
        echo "❌ Missing required field: $field"
        echo "Error object: $FIRST_ERROR"
        exit 1
    fi
done

echo "✅ JSON structure is valid"

# Test 4: Good playbook (should pass or have minimal errors)
echo ""
echo "📝 Test 4: Good playbook validation"
cat > test_good.yml << 'EOF'
---
- name: Test playbook
  hosts: localhost
  tasks:
    - name: Print message
      ansible.builtin.debug:
        msg: "Hello World"
    
    - name: Create directory
      ansible.builtin.file:
        path: /tmp/test
        state: directory
        mode: '0755'
EOF

echo "Running: ansible-lint --format=json --strict --profile=basic test_good.yml"
if ansible-lint --format=json --strict --profile=basic test_good.yml > good_output.json 2>&1; then
    echo "✅ Good playbook passed"
else
    GOOD_ERROR_COUNT=$(jq '. | length' good_output.json 2>/dev/null || echo "0")
    echo "⚠️  Good playbook has $GOOD_ERROR_COUNT errors (should be minimal)"
    
    # Show first few errors for debugging
    if [[ "$GOOD_ERROR_COUNT" -gt 0 ]]; then
        echo "First error:"
        jq '.[0]' good_output.json 2>/dev/null || echo "Could not parse errors"
    fi
fi

# Test 5: Integration with our Python module
echo ""
echo "📝 Test 5: Python integration test"
cd "$PROJECT_ROOT"

python3 << EOF
import sys
import tempfile
from pathlib import Path

# Add project to path
sys.path.insert(0, '.')

from aider_lint_fixer.linters.ansible_lint import AnsibleLintLinter

# Create test playbook
test_dir = Path('$TEST_DIR')
playbook = test_dir / 'python_test.yml'
playbook.write_text('''---
- hosts: localhost
  tasks:
  - shell: echo "test"
  - debug: msg="test"
''')

# Test linter
linter = AnsibleLintLinter(str(test_dir))

# Check availability
if not linter.is_available():
    print("❌ Linter not available")
    sys.exit(1)

print(f"✅ Linter available, version: {linter.get_version()}")

# Test basic profile
result = linter.run_with_profile('basic', [str(playbook)])
print(f"✅ Basic profile: {len(result.errors)} errors, {len(result.warnings)} warnings")

if len(result.errors) == 0:
    print("❌ Expected errors but found none")
    print(f"Raw output: {result.raw_output[:200]}")
    sys.exit(1)

# Test production profile
result = linter.run_with_profile('production', [str(playbook)])
print(f"✅ Production profile: {len(result.errors)} errors, {len(result.warnings)} warnings")

print("✅ Python integration successful")
EOF

if [[ $? -ne 0 ]]; then
    echo "❌ Python integration test failed"
    exit 1
fi

# Cleanup
echo ""
echo "🧹 Cleaning up test directory: $TEST_DIR"
rm -rf "$TEST_DIR"

echo ""
echo "🎉 All tests passed for ansible-lint $ACTUAL_VERSION!"
echo ""
echo "📊 Summary:"
echo "   - Basic profile: $ERROR_COUNT errors detected"
echo "   - Production profile: $PROD_ERROR_COUNT errors detected"
echo "   - JSON structure: Valid"
echo "   - Python integration: Working"
echo ""
echo "✅ ansible-lint 25.6.1 integration is ready for production use!"
