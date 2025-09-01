#!/bin/bash
# Clean up coverage data files to prevent data combination errors

set -e

echo "🧹 Cleaning up coverage data files..."

# Remove all coverage data files
find . -name ".coverage*" -type f -delete 2>/dev/null || true

# Remove coverage HTML reports
rm -rf htmlcov/ 2>/dev/null || true

# Remove coverage XML reports  
rm -f coverage.xml 2>/dev/null || true

echo "✅ Coverage data cleanup complete!"