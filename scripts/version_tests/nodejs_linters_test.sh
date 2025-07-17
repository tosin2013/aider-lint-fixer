#!/bin/bash
# Version-specific test for Node.js linters (eslint, jshint, prettier)
#
# Supported Versions (as of v1.3.0):
# - ESLint: 8.57.1 (tested), 8.57.x, 8.5.x, 8.x, 7.x (supported)
# - JSHint: 2.13.6 (tested), 2.13.x, 2.1.x, 2.x (supported)
# - Prettier: 3.6.2 (tested), 3.6.x, 3.x, 2.x (supported)

set -e

echo "🧪 Node.js Linters Integration Test"
echo "=================================="
echo "📋 Supported Versions:"
echo "  • ESLint: 8.57.1 (tested), 8.57.x, 8.5.x, 8.x, 7.x"
echo "  • JSHint: 2.13.6 (tested), 2.13.x, 2.1.x, 2.x"
echo "  • Prettier: 3.6.2 (tested), 3.6.x, 3.x, 2.x"
echo ""

# Check versions
echo "📋 Checking linter versions:"
linters=("eslint" "jshint" "prettier" "tslint")

for linter in "${linters[@]}"; do
    if command -v "$linter" &> /dev/null; then
        version=$($linter --version 2>&1 | head -1)
        echo "✅ $linter: $version"
    else
        echo "❌ $linter: Not installed"
    fi
done

echo ""

# Create test directory
TEST_DIR=$(mktemp -d)
echo "📁 Test directory: $TEST_DIR"
cd "$TEST_DIR"

# Create problematic JavaScript code
echo "📝 Creating problematic JavaScript code..."
cat > bad_code.js << 'EOF'
var fs = require('fs');
var unused = require('path');

function badFunction(x,y,z) {
    if (x == null) {
        return;
    }
    var unused_var = "not used";
    var result = x + y + z + 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12 + 13 + 14 + 15 + 16 + 17 + 18 + 19 + 20;
    
    var data = {key: "value", another_key:"another_value"}
    
    if (result == undefined) {
        console.log("result is undefined")
    }
    
    var message1 = "Hello world";
    var message2 = 'Hello world';
    
    return result
}

globalVar = "bad practice";
eval("console.log('bad')");

module.exports = badFunction;
EOF

# Create package.json
cat > package.json << 'EOF'
{
  "name": "test-project",
  "version": "1.0.0",
  "main": "bad_code.js"
}
EOF

echo "Content of bad_code.js:"
cat bad_code.js
echo ""

# Test each linter
echo "🔍 Testing linters on problematic code:"

# Test 1: ESLint
echo ""
echo "--- Testing ESLint ---"
if command -v eslint &> /dev/null; then
    echo "Standard output:"
    eslint bad_code.js || true
    echo ""
    
    echo "JSON output:"
    eslint --format=json bad_code.js > eslint_output.json 2>&1 || true
    if [ -s eslint_output.json ]; then
        echo "JSON output length: $(wc -c < eslint_output.json) characters"
        echo "First error:"
        jq '.[0].messages[0] // empty' eslint_output.json 2>/dev/null || echo "Could not parse JSON"
        
        ERROR_COUNT=$(jq '.[0].messages | length' eslint_output.json 2>/dev/null || echo "0")
        echo "Total errors found: $ERROR_COUNT"
    else
        echo "No JSON output generated"
    fi
    echo ""
else
    echo "❌ ESLint not available"
fi

# Test 2: JSHint
echo "--- Testing JSHint ---"
if command -v jshint &> /dev/null; then
    echo "Standard output:"
    jshint bad_code.js || true
    echo ""
    
    echo "JSON output:"
    jshint --reporter=json bad_code.js > jshint_output.json 2>&1 || true
    if [ -s jshint_output.json ]; then
        echo "JSON output length: $(wc -c < jshint_output.json) characters"
        echo "First error:"
        jq '.[0] // empty' jshint_output.json 2>/dev/null || echo "Could not parse JSON"
        
        ERROR_COUNT=$(jq '. | length' jshint_output.json 2>/dev/null || echo "0")
        echo "Total errors found: $ERROR_COUNT"
    else
        echo "No JSON output generated"
    fi
    echo ""
else
    echo "❌ JSHint not available"
fi

# Test 3: Prettier
echo "--- Testing Prettier ---"
if command -v prettier &> /dev/null; then
    echo "Check mode:"
    prettier --check bad_code.js || true
    echo ""
    
    echo "List different:"
    prettier --list-different bad_code.js || true
    echo ""
else
    echo "❌ Prettier not available"
fi

# Test 4: Good JavaScript code
echo "📝 Testing with good JavaScript code..."
cat > good_code.js << 'EOF'
'use strict';

const fs = require('fs');
const path = require('path');

/**
 * Process items and return uppercase versions
 * @param {Array<string>} items - Array of strings to process
 * @returns {Array<string>} Array of uppercase strings
 */
function processItems(items) {
    if (!items || !Array.isArray(items)) {
        return [];
    }
    
    return items
        .filter(item => item !== null && item !== undefined)
        .map(item => item.toString().toUpperCase());
}

/**
 * Data processor class
 */
class DataProcessor {
    /**
     * Create a data processor
     * @param {string} name - Name of the processor
     */
    constructor(name) {
        this.name = name;
    }
    
    /**
     * Check if processor is valid
     * @returns {boolean} True if valid
     */
    isValid() {
        return this.name !== null && this.name !== undefined;
    }
}

module.exports = {
    processItems,
    DataProcessor
};
EOF

echo ""
echo "🔍 Testing linters on good code:"

for linter in eslint jshint prettier; do
    if command -v "$linter" &> /dev/null; then
        echo "--- $linter on good code ---"
        case $linter in
            eslint)
                eslint good_code.js && echo "✅ No issues" || echo "❌ Issues found"
                ;;
            jshint)
                jshint good_code.js && echo "✅ No issues" || echo "❌ Issues found"
                ;;
            prettier)
                prettier --check good_code.js && echo "✅ No issues" || echo "❌ Issues found"
                ;;
        esac
    fi
done

echo ""
echo "📊 Summary of findings:"
echo "======================"

echo "1. Error detection capabilities:"
for linter in eslint jshint; do
    if command -v "$linter" &> /dev/null; then
        case $linter in
            eslint)
                if [ -s eslint_output.json ]; then
                    error_count=$(jq '.[0].messages | length' eslint_output.json 2>/dev/null || echo "0")
                    echo "   $linter: $error_count errors"
                fi
                ;;
            jshint)
                if [ -s jshint_output.json ]; then
                    error_count=$(jq '. | length' jshint_output.json 2>/dev/null || echo "0")
                    echo "   $linter: $error_count errors"
                fi
                ;;
        esac
    fi
done

echo ""
echo "2. Best commands for integration:"
echo "   eslint: eslint --format=json file.js"
echo "   jshint: jshint --reporter=json file.js"
echo "   prettier: prettier --check --list-different file.js"

echo ""
echo "3. JSON output structures:"
if command -v eslint &> /dev/null && [ -s eslint_output.json ]; then
    echo "   ESLint JSON sample:"
    jq '.[0].messages[0] // empty' eslint_output.json 2>/dev/null || echo "   No JSON available"
fi

if command -v jshint &> /dev/null && [ -s jshint_output.json ]; then
    echo "   JSHint JSON sample:"
    jq '.[0] // empty' jshint_output.json 2>/dev/null || echo "   No JSON available"
fi

echo ""
echo "🧹 Cleaning up test directory: $TEST_DIR"
rm -rf "$TEST_DIR"

echo ""
echo "✅ Node.js linters test complete!"
