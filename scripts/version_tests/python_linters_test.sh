#!/bin/bash
# Version-specific test for Python linters (flake8, pylint, black, mypy)

set -e

echo "🧪 Python Linters Integration Test"
echo "=================================="

# Check versions
echo "📋 Checking linter versions:"
linters=("flake8" "pylint" "black" "mypy")

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

# Create problematic Python code
echo "📝 Creating problematic Python code..."
cat > bad_code.py << 'EOF'
import os,sys
import json
import requests
from typing import Dict

def bad_function(x,y,z):
    if x==None:
        return
    unused_var = "not used"
    result = x + y + z + 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12 + 13 + 14 + 15
    try:
        pass
    except:
        pass
    return result

class badClass:
    def __init__(self,name):
        self.name=name
    def method(self,x,y):
        if self.name==None:
            return False
        return True

def process_data(data):
    if data == None:
        return []
    return [item.upper() for item in data if item is not None]

print("Should be in main guard")
EOF

echo "Content of bad_code.py:"
cat bad_code.py
echo ""

# Test each linter
echo "🔍 Testing linters on problematic code:"

# Test 1: flake8
echo ""
echo "--- Testing flake8 ---"
if command -v flake8 &> /dev/null; then
    echo "Standard output:"
    flake8 bad_code.py || true
    echo ""
    
    echo "JSON output (if supported):"
    flake8 --format=json bad_code.py 2>/dev/null || echo "JSON format not supported"
    echo ""
else
    echo "❌ flake8 not available"
fi

# Test 2: pylint
echo "--- Testing pylint ---"
if command -v pylint &> /dev/null; then
    echo "Standard output:"
    pylint bad_code.py || true
    echo ""
    
    echo "JSON output:"
    pylint --output-format=json bad_code.py > pylint_output.json 2>&1 || true
    if [ -s pylint_output.json ]; then
        echo "JSON output length: $(wc -c < pylint_output.json) characters"
        echo "First JSON object:"
        jq '.[0]' pylint_output.json 2>/dev/null || echo "Could not parse JSON"
        
        ERROR_COUNT=$(jq '. | length' pylint_output.json 2>/dev/null || echo "0")
        echo "Total issues found: $ERROR_COUNT"
    else
        echo "No JSON output generated"
    fi
    echo ""
else
    echo "❌ pylint not available"
fi

# Test 3: black
echo "--- Testing black ---"
if command -v black &> /dev/null; then
    echo "Check mode:"
    black --check --diff bad_code.py || true
    echo ""
else
    echo "❌ black not available"
fi

# Test 4: mypy
echo "--- Testing mypy ---"
if command -v mypy &> /dev/null; then
    echo "Standard output:"
    mypy bad_code.py || true
    echo ""
    
    echo "JSON output:"
    mypy --output=json bad_code.py 2>/dev/null || echo "JSON output failed"
    echo ""
else
    echo "❌ mypy not available"
fi

# Test 5: Good Python code
echo "📝 Testing with good Python code..."
cat > good_code.py << 'EOF'
#!/usr/bin/env python3
"""A well-written Python module."""

from typing import List, Optional


def process_items(items: Optional[List[str]]) -> List[str]:
    """Process a list of items and return uppercase versions.
    
    Args:
        items: List of strings to process, or None
        
    Returns:
        List of uppercase strings
    """
    if items is None:
        return []
    
    return [item.upper() for item in items if item is not None]


class DataProcessor:
    """A class for processing data."""
    
    def __init__(self, name: str) -> None:
        """Initialize the processor.
        
        Args:
            name: Name of the processor
        """
        self.name = name
    
    def is_valid(self) -> bool:
        """Check if the processor is valid.
        
        Returns:
            True if valid, False otherwise
        """
        return self.name is not None


def main() -> None:
    """Main function."""
    processor = DataProcessor("test")
    items = ["hello", "world"]
    result = process_items(items)
    print(f"Processed {len(result)} items")


if __name__ == "__main__":
    main()
EOF

echo ""
echo "🔍 Testing linters on good code:"

for linter in flake8 pylint black mypy; do
    if command -v "$linter" &> /dev/null; then
        echo "--- $linter on good code ---"
        case $linter in
            flake8)
                flake8 good_code.py && echo "✅ No issues" || echo "❌ Issues found"
                ;;
            pylint)
                pylint good_code.py > /dev/null 2>&1 && echo "✅ No issues" || echo "❌ Issues found"
                ;;
            black)
                black --check good_code.py > /dev/null 2>&1 && echo "✅ No issues" || echo "❌ Issues found"
                ;;
            mypy)
                mypy good_code.py > /dev/null 2>&1 && echo "✅ No issues" || echo "❌ Issues found"
                ;;
        esac
    fi
done

echo ""
echo "📊 Summary of findings:"
echo "======================"

echo "1. Error detection capabilities:"
for linter in flake8 pylint; do
    if command -v "$linter" &> /dev/null; then
        case $linter in
            flake8)
                error_count=$(flake8 bad_code.py 2>/dev/null | wc -l || echo "0")
                echo "   $linter: $error_count errors"
                ;;
            pylint)
                error_count=$(pylint --output-format=json bad_code.py 2>/dev/null | jq '. | length' 2>/dev/null || echo "0")
                echo "   $linter: $error_count issues"
                ;;
        esac
    fi
done

echo ""
echo "2. Best commands for integration:"
echo "   flake8: flake8 --format=default file.py"
echo "   pylint: pylint --output-format=json file.py"
echo "   black: black --check --diff file.py"
echo "   mypy: mypy --output=json file.py"

echo ""
echo "3. JSON output structures:"
if command -v pylint &> /dev/null; then
    echo "   pylint JSON sample:"
    pylint --output-format=json bad_code.py 2>/dev/null | jq '.[0] // empty' 2>/dev/null || echo "   No JSON available"
fi

echo ""
echo "🧹 Cleaning up test directory: $TEST_DIR"
rm -rf "$TEST_DIR"

echo ""
echo "✅ Python linters test complete!"
