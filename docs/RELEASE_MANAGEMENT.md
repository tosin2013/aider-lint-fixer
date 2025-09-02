# Release Management Guide

This guide explains how to create and manage releases using our AI-powered automation system.

## 🚀 Overview

We use **Gemini AI** to automatically generate professional release notes from Git commit history, combined with GitHub Actions for fully automated releases.

## 📋 Prerequisites

1. **GEMINI_API_KEY**: Set as GitHub repository secret
2. **PYPI_API_TOKEN**: Set as GitHub repository secret for PyPI publishing
3. **Git tags**: Use semantic versioning (v1.2.3)

## 🤖 AI-Powered Release Flow

### Automatic Release (Recommended)

1. **Update version** in `aider_lint_fixer/__init__.py`
2. **Create and push tag**:
   ```bash
   git tag v2.1.0
   git push origin v2.1.0
   ```
3. **AI generates release notes** automatically using Gemini
4. **GitHub release** created with AI-generated content
5. **PyPI publication** happens automatically

### Manual Release (Alternative)

Trigger via GitHub Actions UI:

1. Go to **Actions** → **AI-Powered Release**
2. Click **Run workflow**
3. Enter version and previous version
4. AI generates release notes and creates release

## 📝 Release Notes Generation

Our system uses **Gemini 2.0 Flash** to analyze:

- **Git commit history** between versions
- **Code diff statistics**
- **Commit classification** (features, fixes, improvements)
- **Project context** (linter tool, AI-powered features)

### AI Prompt Template

The AI receives context about:
- Project purpose and features
- Commit history with automatic classification
- Diff statistics
- Style guidelines for professional release notes

### Fallback System

If Gemini API fails, the system automatically falls back to:
- Basic changelog extraction from CHANGELOG.md
- Structured release notes with manual commit classification

## 📁 File Organization

```
releases/
├── README.md                    # Release directory overview
├── TEMPLATE.md                  # Manual release template
├── RELEASE_NOTES_v2.0.1.md     # AI-generated release notes
├── RELEASE_NOTES_v2.0.0.md     # Previous releases
└── ...

scripts/
├── generate_release_notes.py   # AI release notes generator
├── get_version.py              # Version utilities
└── create_release.py           # Manual release helper

.github/workflows/
└── release.yml                 # AI-powered release automation
```

## 🛠️ Manual Tools

### Generate Release Notes Locally

```bash
# Install dependencies
pip install google-genai

# Set API key
export GEMINI_API_KEY="your-api-key"

# Generate release notes
python scripts/generate_release_notes.py \
  --version 2.1.0 \
  --prev-version 2.0.1
```

### Create Release Manually

```bash
# Create release notes from template
python scripts/create_release.py \
  --version 2.1.0 \
  --type minor \
  --create-notes \
  --update-version
```

### Get Current Version

```bash
python scripts/get_version.py
# Output: 2.0.1
```

## 🔄 Release Process

1. **Development**: Work on features, fixes, improvements
2. **Preparation**: 
   - Update version in `__init__.py`
   - Ensure all tests pass
3. **Release**:
   - Push git tag → Triggers AI automation
   - OR use manual workflow dispatch
4. **Publication**:
   - AI generates professional release notes
   - GitHub release created automatically
   - PyPI package published
   - CHANGELOG.md updated

## ✅ Benefits of AI-Powered Releases

- **Professional Release Notes**: Consistent, well-formatted, user-focused
- **Automatic Classification**: Features, fixes, improvements identified
- **Context Awareness**: Understands project purpose and technical details
- **Time Saving**: No manual release note writing
- **Consistency**: Same quality and format across all releases
- **Fallback Safety**: Always works even if AI fails

## 🔗 GitHub Secrets Configuration

Required secrets in repository settings:

```
GEMINI_API_KEY=your-gemini-api-key
PYPI_API_TOKEN=pypi-...
GITHUB_TOKEN=auto-generated
```

## 📊 Release Metrics

The system tracks:
- **Commit count** between versions
- **Files changed** statistics  
- **Lines added/removed**
- **Release type** classification (major/minor/patch)
- **AI generation success** rate

## 🚨 Troubleshooting

**AI generation fails**: System automatically falls back to basic release notes
**Version mismatch**: Release validation catches inconsistencies
**PyPI failure**: Check PYPI_API_TOKEN secret
**Missing tag**: Create and push git tag first

This AI-powered system ensures consistent, professional releases while saving significant time on manual release note creation.