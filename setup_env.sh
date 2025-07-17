#!/bin/bash
# Aider Lint Fixer v0.1.0 - Environment Setup Script

set -e

echo "🚀 Aider Lint Fixer v0.1.0 Setup"
echo "=================================="

# Check if .env already exists
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled."
        exit 1
    fi
fi

# Copy .env.example to .env
if [ ! -f ".env.example" ]; then
    echo "❌ .env.example file not found!"
    echo "Please run this script from the aider-lint-fixer directory."
    exit 1
fi

cp .env.example .env
echo "✅ Created .env file from .env.example"

# Prompt for DeepSeek API key
echo ""
echo "📝 Configuration Setup"
echo "====================="
echo ""
echo "You need a DeepSeek API key to use aider-lint-fixer."
echo "Get one from: https://platform.deepseek.com/"
echo ""
read -p "Enter your DeepSeek API key: " -r DEEPSEEK_KEY

if [ -z "$DEEPSEEK_KEY" ]; then
    echo "❌ No API key provided. You can edit .env manually later."
else
    # Replace the placeholder with the actual key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your_deepseek_api_key_here/$DEEPSEEK_KEY/" .env
    else
        # Linux
        sed -i "s/your_deepseek_api_key_here/$DEEPSEEK_KEY/" .env
    fi
    echo "✅ API key configured in .env"
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. Export environment variables:"
echo "   export \$(cat .env | grep -v '^#' | xargs)"
echo ""
echo "2. Test the installation:"
echo "   aider-lint-fixer --help"
echo ""
echo "3. Run on a project:"
echo "   aider-lint-fixer /path/to/your/project"
echo ""
echo "For more information, see: README.md"
