#!/usr/bin/env python3
"""
Smart CHANGELOG generation and validation using Gemini AI.

This script can:
1. Auto-generate CHANGELOG entries from commit history
2. Validate existing CHANGELOG completeness
3. Categorize changes intelligently (features, fixes, breaking changes)
4. Generate professional, user-friendly changelog entries

Usage:
    python scripts/smart_changelog_generator.py --version 2.1.0 --auto-generate-if-missing
    python scripts/smart_changelog_generator.py --validate-completeness --version 2.1.0
    python scripts/smart_changelog_generator.py --generate-entry --version 2.1.0 --prev-version 2.0.1
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from google import genai
except ImportError:
    genai = None


class SmartChangelogGenerator:
    """AI-powered CHANGELOG generation and validation."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None
        if api_key and genai:
            try:
                self.client = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"⚠️ Could not initialize Gemini client: {e}")
    
    def get_git_commits(self, prev_version: str, current_version: str = "HEAD") -> List[Dict]:
        """Get detailed commit information between versions."""
        try:
            cmd = ["git", "log", f"{prev_version}..{current_version}", 
                   "--pretty=format:%H|%s|%b|%an|%ad", "--date=short", "--no-merges"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('|', 4)
                    if len(parts) >= 4:
                        commits.append({
                            'hash': parts[0],
                            'subject': parts[1],
                            'body': parts[2] if len(parts) > 2 else '',
                            'author': parts[3] if len(parts) > 3 else '',
                            'date': parts[4] if len(parts) > 4 else ''
                        })
            
            return commits
        except subprocess.CalledProcessError as e:
            print(f"❌ Error getting git commits: {e}")
            return []
    
    def get_file_changes(self, prev_version: str, current_version: str = "HEAD") -> Dict:
        """Get file change statistics."""
        try:
            # Get changed files with stats
            cmd = ["git", "diff", "--stat", f"{prev_version}..{current_version}"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Get list of changed files
            cmd2 = ["git", "diff", "--name-only", f"{prev_version}..{current_version}"]
            result2 = subprocess.run(cmd2, capture_output=True, text=True, check=True)
            
            files = result2.stdout.strip().split('\n') if result2.stdout.strip() else []
            
            return {
                'stats': result.stdout,
                'files': files,
                'total_files': len(files)
            }
        except subprocess.CalledProcessError:
            return {'stats': '', 'files': [], 'total_files': 0}
    
    def ai_categorize_commits(self, commits: List[Dict], file_changes: Dict) -> Dict:
        """Use AI to categorize and analyze commits for changelog."""
        if not self.client:
            return self._fallback_categorize_commits(commits)
        
        # Prepare commit data for AI
        commit_summary = []
        for commit in commits[:20]:  # Limit to avoid token limits
            commit_summary.append(f"- {commit['subject']}")
            if commit['body'] and len(commit['body'].strip()) > 0:
                # Include first line of body if meaningful
                body_line = commit['body'].split('\n')[0].strip()
                if len(body_line) > 10:
                    commit_summary.append(f"  {body_line}")
        
        changed_files = file_changes.get('files', [])[:15]  # Sample of changed files
        
        prompt = f"""
        Analyze these commits and generate a professional changelog entry:
        
        **Commits:**
        {chr(10).join(commit_summary)}
        
        **Changed Files (sample):**
        {chr(10).join(changed_files)}
        
        **File Change Stats:**
        {file_changes.get('stats', 'No stats available')[:500]}
        
        **Instructions:**
        1. Categorize changes into: Features, Bug Fixes, Performance, Security, Breaking Changes, Documentation, Internal
        2. Write user-friendly descriptions (not raw commit messages)
        3. Focus on user impact, not technical details
        4. Identify any breaking changes
        5. Highlight important security fixes
        6. Use present tense ("Add", "Fix", "Improve")
        
        **Format as markdown:**
        ### 🎉 Features
        - Feature description
        
        ### 🐛 Bug Fixes  
        - Bug fix description
        
        ### ⚡ Performance
        - Performance improvement
        
        ### 🔒 Security
        - Security fix description
        
        ### 💥 Breaking Changes
        - Breaking change description
        
        ### 📚 Documentation
        - Documentation update
        
        ### 🔧 Internal
        - Internal improvement
        
        Only include sections that have changes. Focus on user value.
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt
            )
            return self._parse_changelog_response(response.text, commits)
        except Exception as e:
            print(f"⚠️ AI categorization failed: {e}")
            return self._fallback_categorize_commits(commits)
    
    def _parse_changelog_response(self, response: str, commits: List[Dict]) -> Dict:
        """Parse AI response into structured changelog data."""
        return {
            'content': response,
            'has_breaking_changes': 'Breaking Changes' in response,
            'has_security_fixes': 'Security' in response,
            'total_commits': len(commits),
            'ai_generated': True
        }
    
    def _fallback_categorize_commits(self, commits: List[Dict]) -> Dict:
        """Fallback categorization without AI."""
        features = []
        fixes = []
        docs = []
        breaking = []
        
        for commit in commits:
            subject = commit['subject'].lower()
            if any(keyword in subject for keyword in ['feat', 'add', 'implement', 'new']):
                features.append(commit['subject'])
            elif any(keyword in subject for keyword in ['fix', 'bug', 'resolve', 'patch']):
                fixes.append(commit['subject'])
            elif any(keyword in subject for keyword in ['doc', 'readme', 'guide']):
                docs.append(commit['subject'])
            elif any(keyword in subject for keyword in ['break', 'major', 'remove', 'deprecate']):
                breaking.append(commit['subject'])
        
        content = []
        if features:
            content.append("### 🎉 Features")
            for feat in features:
                content.append(f"- {feat}")
            content.append("")
        
        if fixes:
            content.append("### 🐛 Bug Fixes")
            for fix in fixes:
                content.append(f"- {fix}")
            content.append("")
        
        if docs:
            content.append("### 📚 Documentation")
            for doc in docs:
                content.append(f"- {doc}")
            content.append("")
        
        if breaking:
            content.append("### 💥 Breaking Changes")
            for brk in breaking:
                content.append(f"- {brk}")
            content.append("")
        
        return {
            'content': '\n'.join(content),
            'has_breaking_changes': len(breaking) > 0,
            'has_security_fixes': False,
            'total_commits': len(commits),
            'ai_generated': False
        }
    
    def check_existing_changelog(self, version: str) -> Dict:
        """Check if CHANGELOG.md exists and has entry for version."""
        changelog_path = Path("CHANGELOG.md")
        
        result = {
            'exists': changelog_path.exists(),
            'has_version_entry': False,
            'content': '',
            'needs_generation': False
        }
        
        if result['exists']:
            content = changelog_path.read_text()
            result['content'] = content
            
            # Check for version entry (various formats)
            version_patterns = [
                rf"## \[{version}\]",
                rf"## {version}",
                rf"# {version}",
                rf"## v{version}",
                rf"# v{version}"
            ]
            
            for pattern in version_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    result['has_version_entry'] = True
                    break
        
        result['needs_generation'] = not result['exists'] or not result['has_version_entry']
        return result
    
    def generate_changelog_entry(self, version: str, prev_version: str = None) -> str:
        """Generate complete changelog entry for a version."""
        print(f"🔍 Generating changelog entry for version {version}...")
        
        # Auto-detect previous version if not provided
        if not prev_version:
            try:
                result = subprocess.run(
                    ["git", "describe", "--tags", "--abbrev=0"], 
                    capture_output=True, text=True, check=True
                )
                prev_version = result.stdout.strip()
            except subprocess.CalledProcessError:
                prev_version = "HEAD~10"  # Fallback
        
        # Get commits and changes
        commits = self.get_git_commits(prev_version, "HEAD")
        file_changes = self.get_file_changes(prev_version, "HEAD")
        
        if not commits:
            return f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n\nNo changes detected."
        
        # Categorize with AI
        analysis = self.ai_categorize_commits(commits, file_changes)
        
        # Build changelog entry
        entry_lines = [
            f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}",
            ""
        ]
        
        # Add summary if AI generated
        if analysis['ai_generated']:
            entry_lines.extend([
                f"🔄 **{analysis['total_commits']} changes** across {file_changes['total_files']} files",
                ""
            ])
            
            if analysis['has_breaking_changes']:
                entry_lines.extend([
                    "⚠️ **BREAKING CHANGES**: This release contains breaking changes. Please review the changelog carefully.",
                    ""
                ])
        
        # Add categorized content
        entry_lines.append(analysis['content'])
        
        # Add footer
        entry_lines.extend([
            "",
            "---",
            f"**Full Changelog**: [{prev_version}...{version}](../../compare/{prev_version}...{version})",
            ""
        ])
        
        return '\n'.join(entry_lines)
    
    def update_changelog_file(self, version: str, entry_content: str) -> bool:
        """Update or create CHANGELOG.md with new entry."""
        changelog_path = Path("CHANGELOG.md")
        
        if changelog_path.exists():
            existing_content = changelog_path.read_text()
            
            # Insert new entry after header
            lines = existing_content.split('\n')
            
            # Find insertion point (after title and any intro)
            insertion_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('## ') and '[' in line:  # First version entry
                    insertion_idx = i
                    break
                elif i > 5:  # Max 5 lines for header
                    insertion_idx = i
                    break
            
            # Insert new entry
            new_lines = (lines[:insertion_idx] + 
                        [''] + entry_content.split('\n') + 
                        [''] + lines[insertion_idx:])
            
            new_content = '\n'.join(new_lines)
        else:
            # Create new changelog
            header = [
                "# Changelog",
                "",
                "All notable changes to this project will be documented in this file.",
                "",
                "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),",
                "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
                "",
                ""
            ]
            
            new_content = '\n'.join(header + entry_content.split('\n'))
        
        try:
            changelog_path.write_text(new_content)
            print(f"✅ Updated CHANGELOG.md with entry for {version}")
            return True
        except Exception as e:
            print(f"❌ Failed to update CHANGELOG.md: {e}")
            return False
    
    def validate_completeness(self, version: str) -> Dict:
        """Validate changelog completeness for a version."""
        print(f"🔍 Validating changelog completeness for {version}...")
        
        changelog_check = self.check_existing_changelog(version)
        
        if not changelog_check['exists']:
            return {
                'valid': False,
                'issues': ['CHANGELOG.md file does not exist'],
                'recommendations': ['Create CHANGELOG.md file with version entry']
            }
        
        if not changelog_check['has_version_entry']:
            return {
                'valid': False,
                'issues': [f'No entry found for version {version}'],
                'recommendations': [f'Add changelog entry for version {version}']
            }
        
        # Additional validation could check entry completeness
        return {
            'valid': True,
            'issues': [],
            'recommendations': []
        }


def main():
    parser = argparse.ArgumentParser(description='Smart CHANGELOG generation and validation')
    parser.add_argument('--version', required=True,
                       help='Version to generate changelog for')
    parser.add_argument('--prev-version',
                       help='Previous version (auto-detected if not provided)')
    parser.add_argument('--auto-generate-if-missing', action='store_true',
                       help='Auto-generate changelog entry if missing')
    parser.add_argument('--validate-completeness', action='store_true',
                       help='Validate changelog completeness')
    parser.add_argument('--generate-entry', action='store_true',
                       help='Generate changelog entry')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("⚠️ GEMINI_API_KEY not set - using fallback analysis")
    
    generator = SmartChangelogGenerator(api_key)
    
    if args.validate_completeness:
        result = generator.validate_completeness(args.version)
        
        if result['valid']:
            print("✅ Changelog validation passed")
            sys.exit(0)
        else:
            print("❌ Changelog validation failed")
            for issue in result['issues']:
                print(f"   Issue: {issue}")
            for rec in result['recommendations']:
                print(f"   Recommendation: {rec}")
            
            if args.auto_generate_if_missing:
                print("\n🤖 Auto-generating missing changelog entry...")
                entry = generator.generate_changelog_entry(args.version, args.prev_version)
                success = generator.update_changelog_file(args.version, entry)
                sys.exit(0 if success else 1)
            
            sys.exit(1)
    
    elif args.generate_entry:
        entry = generator.generate_changelog_entry(args.version, args.prev_version)
        print("\n📝 Generated changelog entry:")
        print("=" * 50)
        print(entry)
        print("=" * 50)
        
        # Update file
        success = generator.update_changelog_file(args.version, entry)
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()