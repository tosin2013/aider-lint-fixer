#!/usr/bin/env python3
"""
Aider Dependency Management Script

This script helps manage dependencies to avoid conflicts with aider-chat.
It can:
1. Check for conflicts with aider-chat dependencies
2. Generate a clean requirements.txt without conflicting sub-dependencies
3. Update aider-chat while preserving compatibility
"""

import subprocess
import sys
import re
from typing import Dict, List, Set, Tuple


def run_command(cmd: List[str]) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"


def get_package_dependencies(package: str) -> Dict[str, str]:
    """Get dependencies of a specific package."""
    code, stdout, stderr = run_command(["pip", "show", package])
    if code != 0:
        print(f"❌ Could not get info for {package}: {stderr}")
        return {}
    
    dependencies = {}
    for line in stdout.split('\n'):
        if line.startswith('Requires:'):
            deps_str = line.replace('Requires:', '').strip()
            if deps_str:
                for dep in deps_str.split(', '):
                    # Parse dependency with version constraints
                    match = re.match(r'([a-zA-Z0-9_-]+)([>=<!=]+.*)?', dep.strip())
                    if match:
                        dep_name = match.group(1)
                        version_constraint = match.group(2) or ""
                        dependencies[dep_name] = version_constraint
    
    return dependencies


def check_conflicts() -> bool:
    """Check for dependency conflicts."""
    print("🔍 Checking for dependency conflicts...")
    
    code, stdout, stderr = run_command(["pip", "check"])
    if code == 0:
        print("✅ No dependency conflicts found")
        return False
    else:
        print("⚠️ Dependency conflicts detected:")
        print(stdout)
        print(stderr)
        return True


def get_aider_dependencies() -> Dict[str, str]:
    """Get all dependencies required by aider-chat."""
    print("📦 Getting aider-chat dependencies...")
    return get_package_dependencies("aider-chat")


def analyze_requirements_file(file_path: str = "requirements.txt") -> Set[str]:
    """Analyze requirements.txt and return set of package names."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        packages = set()
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (before any version specifiers)
                match = re.match(r'([a-zA-Z0-9_-]+)', line)
                if match:
                    packages.add(match.group(1))
        
        return packages
    except FileNotFoundError:
        print(f"❌ {file_path} not found")
        return set()


def suggest_resolution():
    """Suggest resolution for dependency conflicts."""
    print("\n💡 Dependency Conflict Resolution Suggestions:")
    print("=" * 50)
    
    # Get aider-chat dependencies
    aider_deps = get_aider_dependencies()
    if not aider_deps:
        print("❌ Could not get aider-chat dependencies")
        return
    
    print(f"📋 Aider-chat manages these dependencies:")
    for dep, version in aider_deps.items():
        print(f"  • {dep}{version}")
    
    # Check requirements.txt
    req_packages = analyze_requirements_file()
    
    # Find overlapping dependencies
    overlaps = req_packages.intersection(set(aider_deps.keys()))
    
    if overlaps:
        print(f"\n⚠️ Found overlapping dependencies in requirements.txt:")
        for pkg in overlaps:
            print(f"  • {pkg}")
        
        print(f"\n🔧 Recommended actions:")
        print(f"1. Remove these packages from requirements.txt:")
        for pkg in overlaps:
            print(f"   - {pkg}")
        print(f"2. Let aider-chat manage these dependencies automatically")
        print(f"3. Update Dependabot to ignore these packages")
        
        # Generate clean requirements
        print(f"\n📝 Generating clean requirements.txt...")
        generate_clean_requirements(req_packages - overlaps)
    else:
        print("✅ No overlapping dependencies found in requirements.txt")


def generate_clean_requirements(keep_packages: Set[str]):
    """Generate a clean requirements.txt without conflicting dependencies."""
    try:
        with open("requirements.txt", 'r') as f:
            lines = f.readlines()
        
        clean_lines = []
        removed_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith('#'):
                match = re.match(r'([a-zA-Z0-9_-]+)', line_stripped)
                if match and match.group(1) in keep_packages:
                    clean_lines.append(line)
                else:
                    removed_lines.append(line)
            else:
                clean_lines.append(line)
        
        # Write clean requirements
        with open("requirements.txt.clean", 'w') as f:
            f.writelines(clean_lines)
        
        print(f"✅ Generated requirements.txt.clean")
        
        if removed_lines:
            print(f"📋 Removed conflicting dependencies:")
            for line in removed_lines:
                print(f"  - {line.strip()}")
            
            print(f"\n🔄 To apply changes:")
            print(f"  mv requirements.txt.clean requirements.txt")
    
    except Exception as e:
        print(f"❌ Error generating clean requirements: {e}")


def update_aider_safely():
    """Update aider-chat safely."""
    print("🔄 Updating aider-chat safely...")
    
    # First, check current version
    code, stdout, stderr = run_command(["pip", "show", "aider-chat"])
    if code == 0:
        for line in stdout.split('\n'):
            if line.startswith('Version:'):
                current_version = line.replace('Version:', '').strip()
                print(f"📦 Current aider-chat version: {current_version}")
                break
    
    # Update aider-chat
    print("🔄 Updating aider-chat...")
    code, stdout, stderr = run_command(["pip", "install", "--upgrade", "aider-chat"])
    
    if code == 0:
        print("✅ Aider-chat updated successfully")
        
        # Check for conflicts after update
        if check_conflicts():
            print("⚠️ Conflicts detected after update")
            suggest_resolution()
        else:
            print("✅ No conflicts after update")
    else:
        print(f"❌ Failed to update aider-chat: {stderr}")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python manage_aider_dependencies.py <command>")
        print("Commands:")
        print("  check       - Check for dependency conflicts")
        print("  analyze     - Analyze requirements.txt for conflicts")
        print("  clean       - Generate clean requirements.txt")
        print("  update      - Update aider-chat safely")
        print("  suggest     - Suggest conflict resolution")
        return
    
    command = sys.argv[1]
    
    if command == "check":
        check_conflicts()
    elif command == "analyze":
        suggest_resolution()
    elif command == "clean":
        req_packages = analyze_requirements_file()
        aider_deps = get_aider_dependencies()
        clean_packages = req_packages - set(aider_deps.keys())
        generate_clean_requirements(clean_packages)
    elif command == "update":
        update_aider_safely()
    elif command == "suggest":
        suggest_resolution()
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()
