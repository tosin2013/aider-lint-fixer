#!/usr/bin/env python3
"""
Smart version validation and auto-fix using Gemini AI.

This script can:
1. Validate version consistency between tag and package
2. Auto-fix version mismatches intelligently
3. Detect and resolve version conflicts
4. Suggest appropriate version corrections

Usage:
    python scripts/smart_version_validator.py --validate-release-version --tag v2.1.0
    python scripts/smart_version_validator.py --tag v2.1.0 --auto-fix-if-needed
    python scripts/smart_version_validator.py --analyze-version-health
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


class SmartVersionValidator:
    """AI-powered version validation and auto-fixing."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None
        if api_key and genai:
            try:
                self.client = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"⚠️ Could not initialize Gemini client: {e}")
    
    def get_package_version(self) -> str:
        """Get current version from __init__.py"""
        init_file = Path("aider_lint_fixer/__init__.py")
        if not init_file.exists():
            raise FileNotFoundError("aider_lint_fixer/__init__.py not found")
        
        content = init_file.read_text()
        match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
        raise ValueError("Could not find version in __init__.py")
    
    def get_git_commits_since_last_tag(self) -> List[str]:
        """Get commits since last tag for analysis."""
        try:
            # Get last tag
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"], 
                capture_output=True, text=True, check=True
            )
            last_tag = result.stdout.strip()
            
            # Get commits since last tag
            result = subprocess.run(
                ["git", "log", f"{last_tag}..HEAD", "--oneline"], 
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.CalledProcessError:
            return []
    
    def ai_analyze_version_mismatch(self, package_version: str, tag_version: str) -> Dict:
        """Use AI to analyze version mismatch and suggest fixes."""
        if not self.client:
            return self._fallback_version_analysis(package_version, tag_version)
        
        commits = self.get_git_commits_since_last_tag()
        commit_summary = '\n'.join(commits[:10])  # Last 10 commits
        
        prompt = f"""
        Analyze this version mismatch and provide intelligent resolution:
        
        **Version Mismatch Details:**
        - Package version (in __init__.py): {package_version}
        - Release tag version: {tag_version}
        - Recent commits: {commit_summary}
        
        **Analysis needed:**
        1. Which version is likely correct?
        2. What type of changes do the commits suggest? (patch/minor/major)
        3. Should we update the package version or use a different tag?
        4. What's the recommended fix action?
        
        **Provide response as structured analysis:**
        - **Recommended Action**: [update_package|use_different_tag|manual_review]
        - **Correct Version**: [suggested version]
        - **Reasoning**: [brief explanation]
        - **Change Type**: [patch|minor|major|hotfix]
        - **Risk Level**: [low|medium|high]
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt
            )
            return self._parse_ai_response(response.text)
        except Exception as e:
            print(f"⚠️ AI analysis failed: {e}")
            return self._fallback_version_analysis(package_version, tag_version)
    
    def _parse_ai_response(self, response: str) -> Dict:
        """Parse AI response into structured data."""
        result = {
            'action': 'manual_review',
            'correct_version': None,
            'reasoning': 'AI analysis failed',
            'change_type': 'unknown',
            'risk_level': 'medium'
        }
        
        # Extract structured information from AI response
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if 'Recommended Action:' in line:
                action = re.search(r'\[(update_package|use_different_tag|manual_review)\]', line)
                if action:
                    result['action'] = action.group(1)
            elif 'Correct Version:' in line:
                version = re.search(r'(\d+\.\d+\.\d+)', line)
                if version:
                    result['correct_version'] = version.group(1)
            elif 'Change Type:' in line:
                change_type = re.search(r'\[(patch|minor|major|hotfix)\]', line)
                if change_type:
                    result['change_type'] = change_type.group(1)
            elif 'Risk Level:' in line:
                risk = re.search(r'\[(low|medium|high)\]', line)
                if risk:
                    result['risk_level'] = risk.group(1)
            elif 'Reasoning:' in line:
                result['reasoning'] = line.replace('**Reasoning:**', '').strip()
        
        return result
    
    def _fallback_version_analysis(self, package_version: str, tag_version: str) -> Dict:
        """Fallback analysis without AI."""
        # Simple heuristic: if tag is newer, probably correct
        package_parts = [int(x) for x in package_version.split('.')]
        tag_parts = [int(x) for x in tag_version.split('.')]
        
        if tag_parts > package_parts:
            return {
                'action': 'update_package',
                'correct_version': tag_version,
                'reasoning': 'Tag version is newer than package version',
                'change_type': 'patch',
                'risk_level': 'low'
            }
        else:
            return {
                'action': 'use_different_tag',
                'correct_version': package_version,
                'reasoning': 'Package version is newer than tag',
                'change_type': 'patch',
                'risk_level': 'low'
            }
    
    def update_package_version(self, new_version: str) -> bool:
        """Update version in __init__.py"""
        init_file = Path("aider_lint_fixer/__init__.py")
        content = init_file.read_text()
        
        # Replace version
        new_content = re.sub(
            r'__version__ = ["\'][^"\']+["\']',
            f'__version__ = "{new_version}"',
            content
        )
        
        if new_content != content:
            init_file.write_text(new_content)
            print(f"✅ Updated package version to {new_version}")
            return True
        return False
    
    def validate_release_version(self, tag_version: str, auto_fix: bool = False) -> bool:
        """Main validation function with optional auto-fix."""
        print(f"🔍 Validating release version: {tag_version}")
        
        # Remove 'v' prefix if present
        clean_tag = tag_version.lstrip('v')
        
        try:
            package_version = self.get_package_version()
            print(f"📦 Package version: {package_version}")
            print(f"🏷️ Tag version: {clean_tag}")
            
            if package_version == clean_tag:
                print("✅ Version consistency validated")
                return True
            
            print("⚠️ Version mismatch detected!")
            
            if auto_fix:
                print("🤖 Running AI analysis for auto-fix...")
                analysis = self.ai_analyze_version_mismatch(package_version, clean_tag)
                
                print(f"\n📊 AI Analysis Results:")
                print(f"   Action: {analysis['action']}")
                print(f"   Correct Version: {analysis.get('correct_version', 'unknown')}")
                print(f"   Change Type: {analysis['change_type']}")
                print(f"   Risk Level: {analysis['risk_level']}")
                print(f"   Reasoning: {analysis['reasoning']}")
                
                if analysis['action'] == 'update_package' and analysis['correct_version']:
                    if analysis['risk_level'] in ['low', 'medium']:
                        success = self.update_package_version(analysis['correct_version'])
                        if success:
                            print("🤖 Auto-fix completed successfully!")
                            return True
                    else:
                        print("🚨 High risk detected - manual review required")
                        return False
                elif analysis['action'] == 'use_different_tag':
                    print(f"💡 Recommendation: Use tag v{analysis['correct_version']} instead")
                    return False
                else:
                    print("🔍 Manual review required")
                    return False
            
            return False
            
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return False
    
    def analyze_version_health(self) -> Dict:
        """Analyze overall version health of the project."""
        print("🔍 Analyzing version health...")
        
        try:
            package_version = self.get_package_version()
            commits = self.get_git_commits_since_last_tag()
            
            # Check for common version issues
            issues = []
            recommendations = []
            
            if len(commits) > 20:
                issues.append("Many commits since last release")
                recommendations.append("Consider creating a release")
            
            # Check for breaking changes in commit messages
            breaking_changes = [c for c in commits if any(keyword in c.lower() 
                               for keyword in ['breaking', 'major', 'incompatible', 'remove'])]
            
            if breaking_changes:
                issues.append(f"Potential breaking changes detected: {len(breaking_changes)}")
                recommendations.append("Consider major version bump")
            
            health_score = max(0, 100 - len(issues) * 20)
            
            return {
                'package_version': package_version,
                'commits_since_tag': len(commits),
                'issues': issues,
                'recommendations': recommendations,
                'health_score': health_score,
                'breaking_changes': len(breaking_changes)
            }
            
        except Exception as e:
            return {'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description='Smart version validation and auto-fix')
    parser.add_argument('--validate-release-version', action='store_true',
                       help='Validate version consistency for release')
    parser.add_argument('--tag', required=False,
                       help='Tag version to validate against')
    parser.add_argument('--auto-fix-if-needed', action='store_true',
                       help='Auto-fix version mismatches if safe')
    parser.add_argument('--analyze-version-health', action='store_true',
                       help='Analyze overall version health')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("⚠️ GEMINI_API_KEY not set - using fallback analysis")
    
    validator = SmartVersionValidator(api_key)
    
    if args.validate_release_version:
        if not args.tag:
            print("❌ --tag is required for version validation")
            sys.exit(1)
        
        success = validator.validate_release_version(args.tag, args.auto_fix_if_needed)
        sys.exit(0 if success else 1)
    
    elif args.analyze_version_health:
        health = validator.analyze_version_health()
        if 'error' in health:
            print(f"❌ Health analysis failed: {health['error']}")
            sys.exit(1)
        
        print(f"\n📊 Version Health Report:")
        print(f"   Package Version: {health['package_version']}")
        print(f"   Commits Since Tag: {health['commits_since_tag']}")
        print(f"   Health Score: {health['health_score']}/100")
        print(f"   Breaking Changes: {health['breaking_changes']}")
        
        if health['issues']:
            print(f"\n⚠️ Issues:")
            for issue in health['issues']:
                print(f"   - {issue}")
        
        if health['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in health['recommendations']:
                print(f"   - {rec}")
        
        sys.exit(0)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()