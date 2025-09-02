#!/usr/bin/env python3
"""
AI-powered release readiness assessment.

This script can:
1. Analyze commit patterns for stability indicators
2. Assess breaking changes and compatibility
3. Evaluate code quality and test coverage changes
4. Recommend release type and timing
5. Detect potential risks and blockers

Usage:
    python scripts/release_readiness_analyzer.py --analyze-commits --check-breaking-changes
    python scripts/release_readiness_analyzer.py --assess-stability --recommend-release-type
    python scripts/release_readiness_analyzer.py --full-assessment
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

try:
    from google import genai
except ImportError:
    genai = None


class ReleaseReadinessAnalyzer:
    """AI-powered release readiness assessment."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None
        if api_key and genai:
            try:
                self.client = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"⚠️ Could not initialize Gemini client: {e}")
    
    def get_commit_history(self, days: int = 30) -> List[Dict]:
        """Get recent commit history for analysis."""
        try:
            since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            cmd = [
                "git", "log", f"--since={since_date}",
                "--pretty=format:%H|%s|%b|%an|%ad|%cn",
                "--date=short", "--no-merges"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('|', 5)
                    if len(parts) >= 5:
                        commits.append({
                            'hash': parts[0],
                            'subject': parts[1],
                            'body': parts[2],
                            'author': parts[3],
                            'date': parts[4],
                            'committer': parts[5] if len(parts) > 5 else parts[3]
                        })
            
            return commits
        except subprocess.CalledProcessError as e:
            print(f"❌ Error getting commit history: {e}")
            return []
    
    def analyze_test_coverage(self) -> Dict:
        """Analyze test coverage and quality indicators."""
        test_files = list(Path('.').rglob('test_*.py')) + list(Path('.').rglob('*_test.py'))
        test_dirs = [p for p in Path('.').iterdir() if p.is_dir() and 'test' in p.name.lower()]
        
        # Look for coverage reports
        coverage_files = list(Path('.').rglob('coverage.xml')) + list(Path('.').rglob('.coverage'))
        
        # Count test files vs source files
        source_files = list(Path('.').rglob('*.py'))
        source_files = [f for f in source_files if not any(part.startswith('.') for part in f.parts)]
        source_files = [f for f in source_files if 'test' not in str(f)]
        
        return {
            'test_files_count': len(test_files),
            'test_directories': len(test_dirs),
            'source_files_count': len(source_files),
            'test_ratio': len(test_files) / max(len(source_files), 1),
            'has_coverage_reports': len(coverage_files) > 0,
            'coverage_files': [str(f) for f in coverage_files]
        }
    
    def check_ci_status(self) -> Dict:
        """Check CI configuration and workflow health."""
        workflows_dir = Path('.github/workflows')
        workflows = list(workflows_dir.glob('*.yml')) if workflows_dir.exists() else []
        
        # Look for common CI indicators
        has_tests = any('test' in f.name.lower() for f in workflows)
        has_build = any('build' in f.name.lower() or 'ci' in f.name.lower() for f in workflows)
        has_release = any('release' in f.name.lower() for f in workflows)
        
        return {
            'has_github_actions': workflows_dir.exists(),
            'workflow_count': len(workflows),
            'has_test_workflow': has_tests,
            'has_build_workflow': has_build,
            'has_release_workflow': has_release,
            'workflows': [f.name for f in workflows]
        }
    
    def detect_breaking_changes(self, commits: List[Dict]) -> Dict:
        """Detect potential breaking changes in commits."""
        breaking_indicators = [
            'breaking', 'major', 'incompatible', 'remove', 'delete', 'deprecate',
            'drop support', 'no longer', 'breaking change', 'api change'
        ]
        
        api_change_indicators = [
            'change signature', 'rename', 'refactor api', 'modify interface',
            'update api', 'change method', 'remove method', 'remove function'
        ]
        
        breaking_commits = []
        api_changes = []
        
        for commit in commits:
            text = (commit['subject'] + ' ' + commit['body']).lower()
            
            for indicator in breaking_indicators:
                if indicator in text:
                    breaking_commits.append({
                        'commit': commit,
                        'reason': indicator,
                        'type': 'breaking'
                    })
                    break
            
            for indicator in api_change_indicators:
                if indicator in text:
                    api_changes.append({
                        'commit': commit,
                        'reason': indicator,
                        'type': 'api_change'
                    })
                    break
        
        return {
            'breaking_changes_count': len(breaking_commits),
            'api_changes_count': len(api_changes),
            'breaking_commits': breaking_commits,
            'api_changes': api_changes,
            'risk_level': 'high' if breaking_commits else 'medium' if api_changes else 'low'
        }
    
    def analyze_commit_patterns(self, commits: List[Dict]) -> Dict:
        """Analyze commit patterns for stability indicators."""
        if not commits:
            return {'error': 'No commits to analyze'}
        
        # Categorize commits
        categories = {
            'features': [],
            'fixes': [],
            'docs': [],
            'tests': [],
            'refactor': [],
            'chore': [],
            'security': [],
            'performance': []
        }
        
        # Keywords for categorization
        keywords = {
            'features': ['feat', 'add', 'implement', 'new', 'introduce'],
            'fixes': ['fix', 'bug', 'resolve', 'patch', 'correct'],
            'docs': ['doc', 'readme', 'documentation', 'guide', 'comment'],
            'tests': ['test', 'spec', 'coverage', 'unit', 'integration'],
            'refactor': ['refactor', 'restructure', 'reorganize', 'cleanup'],
            'chore': ['chore', 'deps', 'dependency', 'update', 'upgrade', 'bump'],
            'security': ['security', 'vulnerability', 'cve', 'secure', 'auth'],
            'performance': ['perf', 'performance', 'optimize', 'speed', 'fast']
        }
        
        for commit in commits:
            subject = commit['subject'].lower()
            categorized = False
            
            for category, words in keywords.items():
                if any(word in subject for word in words):
                    categories[category].append(commit)
                    categorized = True
                    break
            
            if not categorized:
                categories['chore'].append(commit)
        
        # Calculate metrics
        total_commits = len(commits)
        fix_ratio = len(categories['fixes']) / total_commits
        feature_ratio = len(categories['features']) / total_commits
        test_ratio = len(categories['tests']) / total_commits
        
        # Assess stability
        stability_score = 100
        if fix_ratio > 0.3:  # Too many fixes
            stability_score -= 20
        if feature_ratio > 0.5:  # Too many new features
            stability_score -= 10
        if test_ratio < 0.1:  # Too few test updates
            stability_score -= 15
        
        stability_score = max(0, stability_score)
        
        return {
            'total_commits': total_commits,
            'categories': {k: len(v) for k, v in categories.items()},
            'ratios': {
                'fixes': fix_ratio,
                'features': feature_ratio,
                'tests': test_ratio
            },
            'stability_score': stability_score,
            'assessment': self._assess_stability_level(stability_score)
        }
    
    def _assess_stability_level(self, score: int) -> str:
        """Convert stability score to assessment level."""
        if score >= 80:
            return 'stable'
        elif score >= 60:
            return 'mostly_stable'
        elif score >= 40:
            return 'unstable'
        else:
            return 'highly_unstable'
    
    def ai_assess_release_readiness(self, 
                                   commit_analysis: Dict,
                                   breaking_changes: Dict,
                                   test_coverage: Dict,
                                   ci_status: Dict) -> Dict:
        """Use AI to assess overall release readiness."""
        if not self.client:
            return self._fallback_readiness_assessment(
                commit_analysis, breaking_changes, test_coverage, ci_status
            )
        
        prompt = f"""
        Analyze this project's readiness for release based on the following data:
        
        **Commit Analysis:**
        - Total commits: {commit_analysis.get('total_commits', 0)}
        - Stability score: {commit_analysis.get('stability_score', 0)}/100
        - Fix ratio: {commit_analysis.get('ratios', {}).get('fixes', 0):.2f}
        - Feature ratio: {commit_analysis.get('ratios', {}).get('features', 0):.2f}
        - Test ratio: {commit_analysis.get('ratios', {}).get('tests', 0):.2f}
        
        **Breaking Changes:**
        - Breaking changes: {breaking_changes.get('breaking_changes_count', 0)}
        - API changes: {breaking_changes.get('api_changes_count', 0)}
        - Risk level: {breaking_changes.get('risk_level', 'unknown')}
        
        **Test Coverage:**
        - Test files: {test_coverage.get('test_files_count', 0)}
        - Source files: {test_coverage.get('source_files_count', 0)}
        - Test ratio: {test_coverage.get('test_ratio', 0):.2f}
        - Has coverage reports: {test_coverage.get('has_coverage_reports', False)}
        
        **CI Status:**
        - Has GitHub Actions: {ci_status.get('has_github_actions', False)}
        - Test workflow: {ci_status.get('has_test_workflow', False)}
        - Build workflow: {ci_status.get('has_build_workflow', False)}
        - Release workflow: {ci_status.get('has_release_workflow', False)}
        
        **Provide assessment:**
        1. **Release Readiness**: [ready|needs_work|not_ready]
        2. **Recommended Release Type**: [patch|minor|major|hotfix]
        3. **Risk Assessment**: [low|medium|high]
        4. **Blockers**: List any critical issues that should be fixed before release
        5. **Recommendations**: Specific actions to improve readiness
        6. **Timeline**: Suggested timeline (immediate/1-2 days/1 week/longer)
        
        Focus on practical recommendations for a production release.
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt
            )
            return self._parse_readiness_response(response.text)
        except Exception as e:
            print(f"⚠️ AI assessment failed: {e}")
            return self._fallback_readiness_assessment(
                commit_analysis, breaking_changes, test_coverage, ci_status
            )
    
    def _parse_readiness_response(self, response: str) -> Dict:
        """Parse AI readiness assessment response."""
        result = {
            'readiness': 'needs_work',
            'release_type': 'patch',
            'risk_level': 'medium',
            'blockers': [],
            'recommendations': [],
            'timeline': '1 week',
            'ai_generated': True,
            'raw_response': response
        }
        
        # Extract structured information
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if 'Release Readiness:' in line:
                match = re.search(r'\[(ready|needs_work|not_ready)\]', line)
                if match:
                    result['readiness'] = match.group(1)
            
            elif 'Recommended Release Type:' in line:
                match = re.search(r'\[(patch|minor|major|hotfix)\]', line)
                if match:
                    result['release_type'] = match.group(1)
            
            elif 'Risk Assessment:' in line:
                match = re.search(r'\[(low|medium|high)\]', line)
                if match:
                    result['risk_level'] = match.group(1)
            
            elif 'Blockers:' in line:
                current_section = 'blockers'
            
            elif 'Recommendations:' in line:
                current_section = 'recommendations'
            
            elif 'Timeline:' in line:
                current_section = None
                timeline_match = re.search(r'(immediate|1-2 days|1 week|longer)', line, re.IGNORECASE)
                if timeline_match:
                    result['timeline'] = timeline_match.group(1)
            
            elif current_section and line.startswith('-'):
                item = line.lstrip('- ').strip()
                if item:
                    result[current_section].append(item)
        
        return result
    
    def _fallback_readiness_assessment(self, 
                                     commit_analysis: Dict,
                                     breaking_changes: Dict,
                                     test_coverage: Dict,
                                     ci_status: Dict) -> Dict:
        """Fallback assessment without AI."""
        stability_score = commit_analysis.get('stability_score', 50)
        breaking_count = breaking_changes.get('breaking_changes_count', 0)
        test_ratio = test_coverage.get('test_ratio', 0)
        
        # Simple heuristic assessment
        if breaking_count > 0:
            readiness = 'needs_work'
            release_type = 'major'
            risk_level = 'high'
        elif stability_score < 60:
            readiness = 'needs_work'
            release_type = 'patch'
            risk_level = 'medium'
        elif test_ratio < 0.2:
            readiness = 'needs_work'
            release_type = 'patch'
            risk_level = 'medium'
        else:
            readiness = 'ready'
            release_type = 'minor' if commit_analysis.get('ratios', {}).get('features', 0) > 0.2 else 'patch'
            risk_level = 'low'
        
        blockers = []
        recommendations = []
        
        if breaking_count > 0:
            blockers.append("Breaking changes detected - review compatibility")
        
        if test_ratio < 0.2:
            recommendations.append("Improve test coverage")
        
        if not ci_status.get('has_test_workflow'):
            recommendations.append("Add automated testing workflow")
        
        return {
            'readiness': readiness,
            'release_type': release_type,
            'risk_level': risk_level,
            'blockers': blockers,
            'recommendations': recommendations,
            'timeline': '1 week' if blockers else 'immediate',
            'ai_generated': False
        }
    
    def full_assessment(self) -> Dict:
        """Perform complete release readiness assessment."""
        print("🔍 Performing full release readiness assessment...")
        
        # Gather all data
        commits = self.get_commit_history()
        commit_analysis = self.analyze_commit_patterns(commits)
        breaking_changes = self.detect_breaking_changes(commits)
        test_coverage = self.analyze_test_coverage()
        ci_status = self.check_ci_status()
        
        # AI assessment
        readiness = self.ai_assess_release_readiness(
            commit_analysis, breaking_changes, test_coverage, ci_status
        )
        
        return {
            'timestamp': datetime.now().isoformat(),
            'commit_analysis': commit_analysis,
            'breaking_changes': breaking_changes,
            'test_coverage': test_coverage,
            'ci_status': ci_status,
            'readiness_assessment': readiness,
            'summary': self._generate_summary(readiness)
        }
    
    def _generate_summary(self, readiness: Dict) -> str:
        """Generate human-readable summary."""
        status_icons = {
            'ready': '✅',
            'needs_work': '⚠️',
            'not_ready': '❌'
        }
        
        icon = status_icons.get(readiness['readiness'], '⚠️')
        
        summary = [
            f"{icon} **Release Status**: {readiness['readiness'].replace('_', ' ').title()}",
            f"🎯 **Recommended Type**: {readiness['release_type'].title()} release",
            f"⚡ **Risk Level**: {readiness['risk_level'].title()}",
            f"⏰ **Timeline**: {readiness['timeline']}"
        ]
        
        if readiness['blockers']:
            summary.append(f"🚫 **Blockers**: {len(readiness['blockers'])}")
        
        if readiness['recommendations']:
            summary.append(f"💡 **Recommendations**: {len(readiness['recommendations'])}")
        
        return '\n'.join(summary)


def main():
    parser = argparse.ArgumentParser(description='AI-powered release readiness assessment')
    parser.add_argument('--analyze-commits', action='store_true',
                       help='Analyze commit patterns')
    parser.add_argument('--check-breaking-changes', action='store_true',
                       help='Check for breaking changes')
    parser.add_argument('--assess-stability', action='store_true',
                       help='Assess code stability')
    parser.add_argument('--recommend-release-type', action='store_true',
                       help='Recommend release type')
    parser.add_argument('--full-assessment', action='store_true',
                       help='Perform complete assessment')
    parser.add_argument('--days', type=int, default=30,
                       help='Days of history to analyze (default: 30)')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("⚠️ GEMINI_API_KEY not set - using fallback analysis")
    
    analyzer = ReleaseReadinessAnalyzer(api_key)
    
    if args.full_assessment:
        assessment = analyzer.full_assessment()
        
        print("\n📊 Release Readiness Assessment")
        print("=" * 50)
        print(assessment['summary'])
        
        readiness = assessment['readiness_assessment']
        
        if readiness['blockers']:
            print(f"\n🚫 Blockers ({len(readiness['blockers'])}):")
            for blocker in readiness['blockers']:
                print(f"   - {blocker}")
        
        if readiness['recommendations']:
            print(f"\n💡 Recommendations ({len(readiness['recommendations'])}):")
            for rec in readiness['recommendations']:
                print(f"   - {rec}")
        
        print(f"\n📈 Detailed Metrics:")
        print(f"   Commits analyzed: {assessment['commit_analysis'].get('total_commits', 0)}")
        print(f"   Stability score: {assessment['commit_analysis'].get('stability_score', 0)}/100")
        print(f"   Breaking changes: {assessment['breaking_changes'].get('breaking_changes_count', 0)}")
        print(f"   Test coverage ratio: {assessment['test_coverage'].get('test_ratio', 0):.2f}")
        
        # Exit with appropriate code
        if readiness['readiness'] == 'ready':
            sys.exit(0)
        elif readiness['readiness'] == 'needs_work':
            sys.exit(1)
        else:
            sys.exit(2)
    
    else:
        # Individual analysis components
        commits = analyzer.get_commit_history(args.days)
        
        if args.analyze_commits:
            analysis = analyzer.analyze_commit_patterns(commits)
            print(f"📊 Commit Analysis (last {args.days} days):")
            print(f"   Total commits: {analysis['total_commits']}")
            print(f"   Stability score: {analysis['stability_score']}/100")
            print(f"   Assessment: {analysis['assessment']}")
        
        if args.check_breaking_changes:
            breaking = analyzer.detect_breaking_changes(commits)
            print(f"💥 Breaking Changes:")
            print(f"   Breaking changes: {breaking['breaking_changes_count']}")
            print(f"   API changes: {breaking['api_changes_count']}")
            print(f"   Risk level: {breaking['risk_level']}")
        
        if args.assess_stability:
            test_coverage = analyzer.analyze_test_coverage()
            ci_status = analyzer.check_ci_status()
            print(f"🔒 Stability Assessment:")
            print(f"   Test ratio: {test_coverage['test_ratio']:.2f}")
            print(f"   CI configured: {ci_status['has_github_actions']}")
        
        if args.recommend_release_type:
            # This would need the full assessment
            print("Use --full-assessment for release type recommendation")


if __name__ == '__main__':
    main()