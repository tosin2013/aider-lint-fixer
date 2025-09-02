#!/usr/bin/env python3
"""
Generate release notes using Gemini AI from Git commit history with smart version resolution.

Usage:
    python scripts/generate_release_notes.py --version 2.1.0 --prev-version 2.0.1
    python scripts/generate_release_notes.py --auto-resolve  # Smart version detection
    
Environment Variables:
    GEMINI_API_KEY: Required for AI-powered release note generation
"""
import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from google import genai
except ImportError:
    print("❌ Error: google-genai not installed. Run: pip install google-genai")
    sys.exit(1)


def get_git_commits(prev_version, current_version="HEAD"):
    """Get commit messages between two versions."""
    try:
        # Get commits between versions
        cmd = ["git", "log", f"{prev_version}..{current_version}", "--oneline", "--no-merges"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                # Format: "hash message"
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1]
                    })
        
        return commits
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting git commits: {e}")
        return []


def get_git_diff_stats(prev_version, current_version="HEAD"):
    """Get diff statistics between versions."""
    try:
        cmd = ["git", "diff", "--stat", f"{prev_version}..{current_version}"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "Could not retrieve diff stats"


def classify_commit(commit_message):
    """Simple classification of commit types."""
    message_lower = commit_message.lower()
    
    if any(word in message_lower for word in ['fix', 'bug', 'patch', 'hotfix']):
        return 'bug_fix'
    elif any(word in message_lower for word in ['feat', 'add', 'new', 'implement']):
        return 'feature'
    elif any(word in message_lower for word in ['refactor', 'improve', 'optimize', 'enhance']):
        return 'improvement'
    elif any(word in message_lower for word in ['test', 'spec']):
        return 'test'
    elif any(word in message_lower for word in ['doc', 'readme', 'comment']):
        return 'documentation'
    elif any(word in message_lower for word in ['break', 'breaking']):
        return 'breaking'
    else:
        return 'other'


def generate_release_notes_with_gemini(version, prev_version, commits, diff_stats, api_key):
    """Generate release notes using Gemini AI."""
    
    # Prepare context for Gemini
    commits_by_type = {}
    for commit in commits:
        commit_type = classify_commit(commit['message'])
        if commit_type not in commits_by_type:
            commits_by_type[commit_type] = []
        commits_by_type[commit_type].append(commit)
    
    commit_summary = ""
    for commit_type, type_commits in commits_by_type.items():
        commit_summary += f"\n{commit_type.replace('_', ' ').title()}:\n"
        for commit in type_commits[:10]:  # Limit to prevent token overflow
            commit_summary += f"  - {commit['message']}\n"
    
    prompt = f"""
Generate professional release notes for aider-lint-fixer version {version} (upgrading from {prev_version}).

Project Context:
aider-lint-fixer is an AI-powered tool that automatically detects and fixes lint errors in codebases using aider.chat integration. It supports Python (Flake8, Pylint), JavaScript/TypeScript (ESLint), and Ansible (ansible-lint) with intelligent pattern matching and ML-driven classification.

Commit Summary:
{commit_summary}

Git Diff Stats:
{diff_stats}

Instructions:
1. Create release notes following this structure:
   - Brief overview paragraph
   - "🚀 What's New" section with key features/improvements  
   - "🔧 Improvements" section for enhancements
   - "🐛 Bug Fixes" section for fixes
   - "📊 Impact" section with stats
   - "🧪 Testing" section
   - "📦 Installation" section

2. Style Guidelines:
   - Use emojis appropriately (🚀 🔧 🐛 📊 🧪 📦)
   - Be concise but informative
   - Focus on user-facing changes
   - Group related changes together
   - Use bullet points for clarity

3. Technical Requirements:
   - Don't include internal/dev changes unless user-facing
   - Emphasize performance improvements and bug fixes
   - Mention any breaking changes prominently
   - Include upgrade instructions if needed

4. Format the output as proper markdown for a release notes file.

Generate professional, user-focused release notes now:
"""
    
    try:
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
        )
        
        return response.text
    
    except Exception as e:
        print(f"❌ Error generating release notes with Gemini: {e}")
        return None


def create_fallback_release_notes(version, prev_version, commits, diff_stats):
    """Create basic release notes without AI if Gemini fails."""
    
    commits_by_type = {}
    for commit in commits:
        commit_type = classify_commit(commit['message'])
        if commit_type not in commits_by_type:
            commits_by_type[commit_type] = []
        commits_by_type[commit_type].append(commit)
    
    release_notes = f"""# Release Notes v{version}

**Release Date**: {datetime.now().strftime("%Y-%m-%d")}
**Upgrading from**: v{prev_version}

## 📊 **Summary**

This release includes {len(commits)} commits with improvements across multiple areas of aider-lint-fixer.

"""
    
    if 'feature' in commits_by_type:
        release_notes += "## 🚀 **New Features**\n\n"
        for commit in commits_by_type['feature']:
            release_notes += f"- {commit['message']}\n"
        release_notes += "\n"
    
    if 'improvement' in commits_by_type:
        release_notes += "## 🔧 **Improvements**\n\n"
        for commit in commits_by_type['improvement']:
            release_notes += f"- {commit['message']}\n"
        release_notes += "\n"
    
    if 'bug_fix' in commits_by_type:
        release_notes += "## 🐛 **Bug Fixes**\n\n"
        for commit in commits_by_type['bug_fix']:
            release_notes += f"- {commit['message']}\n"
        release_notes += "\n"
    
    # Add other sections
    release_notes += f"""## 📊 **Impact**

- **Commits**: {len(commits)} changes
- **Files Changed**: See diff stats below

```
{diff_stats}
```

## 📦 **Installation**

```bash
pip install aider-lint-fixer=={version}
# or upgrade
pip install --upgrade aider-lint-fixer
```

## 🔗 **Links**

- **GitHub Release**: https://github.com/tosin2013/aider-lint-fixer/releases/tag/v{version}
- **Full Changelog**: https://github.com/tosin2013/aider-lint-fixer/compare/v{prev_version}...v{version}
"""
    
    return release_notes


def main():
    parser = argparse.ArgumentParser(description="Generate AI-powered release notes with smart version resolution")
    parser.add_argument("--version", help="New version (e.g., 2.1.0)")
    parser.add_argument("--prev-version", help="Previous version (e.g., 2.0.1)")
    parser.add_argument("--auto-resolve", action="store_true", help="Auto-detect versions using AI")
    parser.add_argument("--output", help="Output file (default: releases/RELEASE_NOTES_v{version}.md)")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI generation, use fallback only")
    parser.add_argument("--apply-version", action="store_true", help="Update version in __init__.py if resolved")
    
    args = parser.parse_args()
    
    # Smart version resolution
    if args.auto_resolve or not args.version:
        print("🤖 Using smart version resolution...")
        try:
            from .smart_version_resolver import VersionResolver
            import os
            
            api_key = os.getenv("GEMINI_API_KEY")
            resolver = VersionResolver(api_key)
            
            current_version = resolver.get_current_version()
            latest_tag = resolver.get_latest_git_tag() or "0.0.0"
            
            # Get commits since last release
            commits = resolver.get_commits_since_version(latest_tag)
            
            if commits:
                # Auto-suggest version based on commits
                suggested_version, bump_type, impact_scores = resolver.suggest_version_bump(current_version, commits)
                
                print(f"📊 Smart Version Analysis:")
                print(f"   Current: {current_version}")
                print(f"   Latest tag: {latest_tag}")
                print(f"   Suggested: {suggested_version} ({bump_type} bump)")
                print(f"   Based on: {len(commits)} commits")
                
                # Use resolved versions
                args.version = suggested_version
                args.prev_version = latest_tag
                
                # Update version in code if requested
                if args.apply_version:
                    resolver.update_version_in_file(suggested_version)
            else:
                print("ℹ️  No new commits found, using current version")
                args.version = current_version
                args.prev_version = latest_tag
                
        except ImportError:
            print("⚠️  Smart version resolver not available, using fallback")
        except Exception as e:
            print(f"⚠️  Smart resolution failed: {e}, using manual input")
    
    # Validate required arguments
    if not args.version:
        print("❌ --version is required (or use --auto-resolve)")
        return 1
    if not args.prev_version:
        print("❌ --prev-version is required (or use --auto-resolve)")
        return 1
    
    # Set output file
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = Path(f"releases/RELEASE_NOTES_v{args.version}.md")
    
    print(f"🔍 Generating release notes for v{args.version} (from v{args.prev_version})")
    
    # Get git data
    commits = get_git_commits(f"v{args.prev_version}", "HEAD")
    diff_stats = get_git_diff_stats(f"v{args.prev_version}", "HEAD")
    
    if not commits:
        print("❌ No commits found. Check version tags exist.")
        return 1
    
    print(f"📝 Found {len(commits)} commits to analyze")
    
    # Generate release notes
    release_notes = None
    
    if not args.no_ai:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            print("🤖 Generating AI-powered release notes with Gemini...")
            release_notes = generate_release_notes_with_gemini(
                args.version, args.prev_version, commits, diff_stats, api_key
            )
        else:
            print("⚠️  GEMINI_API_KEY not found, falling back to basic generation")
    
    if not release_notes:
        print("📝 Generating basic release notes...")
        release_notes = create_fallback_release_notes(
            args.version, args.prev_version, commits, diff_stats
        )
    
    # Ensure output directory exists
    output_file.parent.mkdir(exist_ok=True)
    
    # Write release notes
    output_file.write_text(release_notes)
    
    print(f"✅ Release notes generated: {output_file}")
    print(f"📋 Please review and edit before publishing")
    
    return 0


if __name__ == "__main__":
    exit(main())