#!/usr/bin/env python3
"""
Create a new release with automated version management.

Usage:
    python scripts/create_release.py --version 2.1.0 --type minor
"""
import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path


def get_current_version():
    """Get current version from __init__.py"""
    init_file = Path("aider_lint_fixer/__init__.py")
    content = init_file.read_text()
    match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)
    raise ValueError("Could not find version in __init__.py")


def update_version(new_version):
    """Update version in __init__.py"""
    init_file = Path("aider_lint_fixer/__init__.py")
    content = init_file.read_text()
    updated_content = re.sub(
        r'__version__ = ["\'][^"\']+["\']',
        f'__version__ = "{new_version}"',
        content
    )
    init_file.write_text(updated_content)
    print(f"✅ Updated version in __init__.py to {new_version}")


def create_release_notes(version, release_type):
    """Create release notes from template"""
    template_file = Path("releases/TEMPLATE.md")
    if not template_file.exists():
        print("❌ Template file not found at releases/TEMPLATE.md")
        return

    template_content = template_file.read_text()
    
    # Replace template variables
    release_content = template_content.replace("{VERSION}", version)
    release_content = release_content.replace("{RELEASE_DATE}", datetime.now().strftime("%Y-%m-%d"))
    release_content = release_content.replace("{RELEASE_TYPE}", release_type)
    
    # Try to determine previous version for changelog link
    current_version = get_current_version()
    release_content = release_content.replace("{PREV_VERSION}", current_version)
    
    # Write release notes
    release_file = Path(f"releases/RELEASE_NOTES_v{version}.md")
    release_file.write_text(release_content)
    
    print(f"✅ Created release notes: {release_file}")
    print(f"📝 Please edit {release_file} to add specific changes")


def main():
    parser = argparse.ArgumentParser(description="Create a new release")
    parser.add_argument("--version", required=True, help="New version (e.g., 2.1.0)")
    parser.add_argument("--type", choices=["major", "minor", "patch"], required=True, help="Release type")
    parser.add_argument("--update-version", action="store_true", help="Update version in __init__.py")
    parser.add_argument("--create-notes", action="store_true", help="Create release notes from template")
    
    args = parser.parse_args()
    
    try:
        current_version = get_current_version()
        print(f"Current version: {current_version}")
        print(f"New version: {args.version}")
        
        if args.update_version:
            update_version(args.version)
        
        if args.create_notes:
            create_release_notes(args.version, args.type)
            
        print(f"\n📋 Next steps:")
        print(f"1. Edit releases/RELEASE_NOTES_v{args.version}.md with actual changes")
        print(f"2. Update CHANGELOG.md")
        print(f"3. Commit changes: git add -A && git commit -m 'Prepare release v{args.version}'")
        print(f"4. Create tag: git tag v{args.version}")
        print(f"5. Push: git push && git push --tags")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())