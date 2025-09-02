#!/bin/bash
# Generate fallback release notes when AI generation fails

VERSION="$1"
PREV_VERSION="$2"
OUTPUT_FILE="${3:-release_notes.md}"

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> [prev_version] [output_file]"
    exit 1
fi

if [ -z "$PREV_VERSION" ]; then
    PREV_VERSION=$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null | sed 's/v//' || echo "0.0.0")
fi

cat > "$OUTPUT_FILE" << EOF
# Release v$VERSION

## Changes

$(git log v$PREV_VERSION..HEAD --oneline --no-merges | head -20)

## Installation

\`\`\`bash
pip install aider-lint-fixer==$VERSION
\`\`\`
EOF

echo "✅ Fallback release notes generated: $OUTPUT_FILE"