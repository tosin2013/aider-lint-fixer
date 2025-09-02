#!/usr/bin/env python3
"""
Smart version resolution and auto-bumping using Gemini AI.

This script can:
1. Auto-detect the correct version bump based on commit analysis
2. Resolve version conflicts intelligently  
3. Suggest appropriate version numbers
4. Auto-fix version mismatches

Usage:
    python scripts/smart_version_resolver.py --analyze-commits
    python scripts/smart_version_resolver.py --resolve-conflict --current 2.0.1 --requested 2.1.5
    python scripts/smart_version_resolver.py --auto-bump --from-version 2.0.1
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from google import genai
except ImportError:
    genai = None


class VersionResolver:
    """Smart version resolution using AI and semantic analysis."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None
        if api_key and genai:
            try:
                self.client = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"⚠️  Could not initialize Gemini client: {e}")
    
    def get_current_version(self) -> str:
        """Get current version from __init__.py"""
        init_file = Path("aider_lint_fixer/__init__.py")
        if not init_file.exists():
            raise FileNotFoundError("aider_lint_fixer/__init__.py not found")
        
        content = init_file.read_text()
        match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
        raise ValueError("Could not find version in __init__.py")
    
    def get_latest_git_tag(self) -> Optional[str]:
        """Get the latest git tag."""
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"], 
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip().lstrip('v')
        except subprocess.CalledProcessError:
            return None
    
    def get_commits_since_version(self, version: str) -> List[Dict]:
        """Get commits since a specific version."""
        try:
            # Try with 'v' prefix first, then without
            for tag_format in [f"v{version}", version]:
                try:
                    result = subprocess.run(
                        ["git", "log", f"{tag_format}..HEAD", "--oneline", "--no-merges"],
                        capture_output=True, text=True, check=True
                    )
                    break
                except subprocess.CalledProcessError:
                    continue
            else:
                # If no tag found, get all commits
                result = subprocess.run(
                    ["git", "log", "--oneline", "--no-merges", "-20"],  # Last 20 commits
                    capture_output=True, text=True, check=True
                )
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        commits.append({
                            'hash': parts[0],
                            'message': parts[1]
                        })
            
            return commits
        except subprocess.CalledProcessError:
            return []
    
    def analyze_commit_impact(self, commits: List[Dict]) -> Dict[str, int]:
        """Analyze commits to determine impact level."""
        impact_score = {
            'major': 0,
            'minor': 0, 
            'patch': 0
        }
        
        for commit in commits:
            message = commit['message'].lower()
            
            # Major changes (breaking changes, major features)
            if any(keyword in message for keyword in [
                'breaking', 'break', 'major', 'remove', 'delete', 'deprecated',
                'incompatible', 'migrate', 'rewrite', 'refactor major'
            ]):
                impact_score['major'] += 3
            
            # Minor changes (new features, enhancements)
            elif any(keyword in message for keyword in [
                'feat', 'feature', 'add', 'new', 'implement', 'enhance',
                'improve', 'extend', 'support', 'introduce'
            ]):
                impact_score['minor'] += 2
            
            # Patch changes (fixes, small improvements)
            elif any(keyword in message for keyword in [
                'fix', 'bug', 'patch', 'hotfix', 'correct', 'resolve',
                'update', 'adjust', 'tweak', 'clean', 'optimize'
            ]):
                impact_score['patch'] += 1
            
            # Documentation, tests (usually patch)
            elif any(keyword in message for keyword in [
                'doc', 'test', 'spec', 'readme', 'comment', 'typo'
            ]):
                impact_score['patch'] += 0.5
        
        return impact_score
    
    def suggest_version_bump(self, current_version: str, commits: List[Dict]) -> Tuple[str, str, Dict]:
        """Suggest appropriate version bump based on commits."""
        impact_scores = self.analyze_commit_impact(commits)
        
        # Parse current version
        try:
            major, minor, patch = map(int, current_version.split('.'))
        except ValueError:
            raise ValueError(f"Invalid version format: {current_version}")
        
        # Determine bump type
        if impact_scores['major'] >= 1:
            bump_type = 'major'
            new_version = f"{major + 1}.0.0"
        elif impact_scores['minor'] >= 2 or len(commits) >= 10:  # Many commits suggest minor
            bump_type = 'minor' 
            new_version = f"{major}.{minor + 1}.0"
        elif impact_scores['patch'] >= 1 or len(commits) >= 1:
            bump_type = 'patch'
            new_version = f"{major}.{minor}.{patch + 1}"
        else:
            bump_type = 'patch'  # Default to patch
            new_version = f"{major}.{minor}.{patch + 1}"
        
        return new_version, bump_type, impact_scores
    
    def ai_analyze_version_conflict(self, current_version: str, requested_version: str, 
                                  commits: List[Dict]) -> Optional[Dict]:
        """Use AI to analyze version conflicts and suggest resolution."""
        if not self.client:
            return None
        
        # Prepare commit summary
        commit_summary = "\n".join([
            f"- {commit['message']}" for commit in commits[:15]  # Limit for token efficiency
        ])
        
        prompt = f"""
Analyze this version conflict and recommend the best resolution:

Current version: {current_version}
Requested version: {requested_version}
Recent commits since {current_version}:
{commit_summary}

Project context: aider-lint-fixer is an AI-powered lint fixing tool. This is a semantic versioning (semver) project.

Rules:
- MAJOR: Breaking changes, removed features, major architecture changes
- MINOR: New features, significant enhancements, new capabilities  
- PATCH: Bug fixes, small improvements, documentation updates

Analyze the commits and determine:
1. What type of changes were actually made?
2. Is the requested version appropriate?
3. What version should we actually use?
4. Why is this the right choice?

Respond in this exact JSON format:
{{
    "analysis": "Brief analysis of the changes",
    "change_type": "major|minor|patch",
    "recommended_version": "X.Y.Z",
    "reasoning": "Why this version is correct",
    "conflict_resolution": "accept_requested|use_recommended|bump_current",
    "confidence": 0.85
}}
"""
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
            )
            
            # Extract JSON from response
            import json
            response_text = response.text.strip()
            
            # Try to find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                return json.loads(json_text)
            
        except Exception as e:
            print(f"⚠️  AI analysis failed: {e}")
        
        return None
    
    def resolve_version_conflict(self, current_version: str, requested_version: str) -> Dict:
        """Resolve version conflict using AI and fallback logic."""
        commits = self.get_commits_since_version(current_version)
        
        # Try AI analysis first
        ai_result = self.ai_analyze_version_conflict(current_version, requested_version, commits)
        
        if ai_result:
            return {
                'resolved_version': ai_result['recommended_version'],
                'reasoning': ai_result['reasoning'],
                'method': 'ai_analysis',
                'confidence': ai_result.get('confidence', 0.8),
                'change_type': ai_result.get('change_type', 'unknown'),
                'ai_analysis': ai_result
            }
        
        # Fallback to rule-based analysis
        suggested_version, bump_type, impact_scores = self.suggest_version_bump(current_version, commits)
        
        # Compare requested vs suggested
        def version_tuple(v):
            return tuple(map(int, v.split('.')))
        
        current_tuple = version_tuple(current_version)
        requested_tuple = version_tuple(requested_version)
        suggested_tuple = version_tuple(suggested_version)
        
        # Determine best version
        if requested_tuple == suggested_tuple:
            # Perfect match
            resolved_version = requested_version
            reasoning = f"Requested version matches analysis: {bump_type} bump appropriate"
        elif requested_tuple > suggested_tuple:
            # Requested is higher - might be future planning
            if requested_tuple[0] > current_tuple[0]:  # Major bump
                resolved_version = requested_version if impact_scores['major'] > 0 else suggested_version
                reasoning = f"Major version requested but commits suggest {bump_type} bump"
            else:
                resolved_version = requested_version
                reasoning = f"Accepting higher requested version for future planning"
        else:
            # Suggested is higher - use suggested
            resolved_version = suggested_version
            reasoning = f"Commits suggest {bump_type} bump, using {suggested_version}"
        
        return {
            'resolved_version': resolved_version,
            'reasoning': reasoning,
            'method': 'rule_based_analysis',
            'confidence': 0.7,
            'change_type': bump_type,
            'impact_scores': impact_scores,
            'commit_count': len(commits)
        }
    
    def update_version_in_file(self, new_version: str) -> bool:
        """Update version in __init__.py"""
        init_file = Path("aider_lint_fixer/__init__.py")
        
        try:
            content = init_file.read_text()
            updated_content = re.sub(
                r'__version__ = ["\'][^"\']+["\']',
                f'__version__ = "{new_version}"',
                content
            )
            
            if content != updated_content:
                init_file.write_text(updated_content)
                print(f"✅ Updated version in {init_file} to {new_version}")
                return True
            else:
                print(f"ℹ️  Version already set to {new_version}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to update version: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Smart version resolution and auto-bumping")
    parser.add_argument("--analyze-commits", action="store_true", 
                       help="Analyze recent commits and suggest version bump")
    parser.add_argument("--resolve-conflict", action="store_true",
                       help="Resolve version conflict between current and requested")
    parser.add_argument("--auto-bump", action="store_true",
                       help="Automatically bump version based on commits")
    parser.add_argument("--current", help="Current version")
    parser.add_argument("--requested", help="Requested version") 
    parser.add_argument("--from-version", help="Version to bump from")
    parser.add_argument("--apply", action="store_true", help="Apply the resolved version")
    parser.add_argument("--api-key", help="Gemini API key (or use GEMINI_API_KEY env var)")
    
    args = parser.parse_args()
    
    # Get API key
    import os
    api_key = args.api_key or os.getenv("GEMINI_API_KEY")
    
    resolver = VersionResolver(api_key)
    
    try:
        if args.analyze_commits:
            current = args.current or resolver.get_current_version()
            commits = resolver.get_commits_since_version(current)
            
            print(f"📊 Analyzing {len(commits)} commits since v{current}")
            
            suggested_version, bump_type, impact_scores = resolver.suggest_version_bump(current, commits)
            
            print(f"\n🔍 Analysis Results:")
            print(f"   Current version: {current}")
            print(f"   Suggested version: {suggested_version}")
            print(f"   Bump type: {bump_type}")
            print(f"   Impact scores: {impact_scores}")
            
            if args.apply:
                resolver.update_version_in_file(suggested_version)
        
        elif args.resolve_conflict:
            if not args.current or not args.requested:
                print("❌ --current and --requested are required for conflict resolution")
                return 1
            
            print(f"🔧 Resolving conflict: current={args.current}, requested={args.requested}")
            
            result = resolver.resolve_version_conflict(args.current, args.requested)
            
            print(f"\n✅ Resolution Results:")
            print(f"   Resolved version: {result['resolved_version']}")
            print(f"   Method: {result['method']}")
            print(f"   Confidence: {result['confidence']:.1%}")
            print(f"   Reasoning: {result['reasoning']}")
            
            if args.apply:
                resolver.update_version_in_file(result['resolved_version'])
        
        elif args.auto_bump:
            from_version = args.from_version or resolver.get_current_version()
            commits = resolver.get_commits_since_version(from_version)
            
            if not commits:
                print(f"ℹ️  No commits found since {from_version}, no bump needed")
                return 0
            
            suggested_version, bump_type, impact_scores = resolver.suggest_version_bump(from_version, commits)
            
            print(f"🚀 Auto-bump Results:")
            print(f"   From: {from_version}")
            print(f"   To: {suggested_version}")
            print(f"   Type: {bump_type}")
            print(f"   Based on: {len(commits)} commits")
            
            if args.apply:
                resolver.update_version_in_file(suggested_version)
                print(f"✅ Version auto-bumped to {suggested_version}")
            else:
                print("ℹ️  Use --apply to update version in __init__.py")
        
        else:
            # Just show current state
            current = resolver.get_current_version()
            latest_tag = resolver.get_latest_git_tag()
            
            print(f"📋 Version Status:")
            print(f"   Current (__init__.py): {current}")
            print(f"   Latest git tag: {latest_tag or 'None'}")
            
            if latest_tag and latest_tag != current:
                print(f"   ⚠️  Version mismatch detected!")
                commits = resolver.get_commits_since_version(latest_tag)
                if commits:
                    suggested, bump_type, _ = resolver.suggest_version_bump(current, commits)
                    print(f"   💡 Suggested: {suggested} ({bump_type} bump)")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())