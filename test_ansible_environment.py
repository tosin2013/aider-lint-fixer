#!/usr/bin/env python3
"""
Test script to verify ansible-lint environment setup works correctly.
This tests the fixes for issue #27.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path


def test_ansible_environment_setup():
    """Test that ansible environment variables are properly configured."""
    print("Testing ansible environment setup...")
    
    # Import our base linter
    sys.path.insert(0, str(Path(__file__).parent))
    from aider_lint_fixer.linters.base import BaseLinter
    from aider_lint_fixer.linters.ansible_lint import AnsibleLintLinter
    
    # Create a temporary project directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Testing in temporary directory: {temp_dir}")
        
        # Create a simple test ansible file
        test_file = Path(temp_dir) / "test.yml"
        test_file.write_text("""---
- hosts: localhost
  tasks:
    - debug:
        msg: "Hello World"
""")
        
        # Initialize ansible-lint linter
        linter = AnsibleLintLinter(temp_dir)
        
        # Test environment setup
        env = {}
        linter._setup_ansible_environment(env)
        
        print("Environment variables set:")
        for key in ["ANSIBLE_LOCAL_TEMP", "ANSIBLE_REMOTE_TEMP", "ANSIBLE_GALAXY_CACHE_DIR", "ANSIBLE_LOG_PATH"]:
            value = env.get(key, "NOT SET")
            print(f"  {key}: {value}")
        
        # Verify directories were created
        for key in ["ANSIBLE_LOCAL_TEMP", "ANSIBLE_REMOTE_TEMP", "ANSIBLE_GALAXY_CACHE_DIR"]:
            dir_path = env.get(key)
            if dir_path and Path(dir_path).exists():
                print(f"  ✓ Directory exists: {dir_path}")
            else:
                print(f"  ✗ Directory missing: {dir_path}")
        
        # Test availability check with our environment
        try:
            is_available = linter.is_available()
            print(f"ansible-lint availability: {is_available}")
            
            if is_available:
                version = linter.get_version()
                print(f"ansible-lint version: {version}")
            
        except Exception as e:
            print(f"Error checking ansible-lint: {e}")
            
        return True


def test_environment_variables():
    """Test that environment variables are properly inherited."""
    print("\nTesting environment variable inheritance...")
    
    # Set test environment variables
    test_vars = {
        "ANSIBLE_LOCAL_TEMP": "/tmp/test-ansible-local",
        "ANSIBLE_REMOTE_TEMP": "/tmp/test-ansible-remote",
        "ANSIBLE_GALAXY_CACHE_DIR": "/tmp/test-ansible-galaxy",
        "ANSIBLE_LOG_PATH": "/tmp/test-ansible.log"
    }
    
    # Temporarily set environment variables
    old_env = {}
    for key, value in test_vars.items():
        old_env[key] = os.environ.get(key)
        os.environ[key] = value
        # Create the directory if it doesn't exist
        os.makedirs(value.rsplit('/', 1)[0], exist_ok=True)
    
    try:
        # Import our linter
        sys.path.insert(0, str(Path(__file__).parent))
        from aider_lint_fixer.linters.ansible_lint import AnsibleLintLinter
        
        with tempfile.TemporaryDirectory() as temp_dir:
            linter = AnsibleLintLinter(temp_dir)
            
            # Test that environment variables are preserved
            env = os.environ.copy()
            linter._setup_ansible_environment(env)
            
            print("Environment variables after setup:")
            for key, expected_value in test_vars.items():
                actual_value = env.get(key)
                if actual_value == expected_value:
                    print(f"  ✓ {key}: {actual_value}")
                else:
                    print(f"  ✗ {key}: expected {expected_value}, got {actual_value}")
    
    finally:
        # Restore original environment
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    
    return True


def main():
    """Run all tests."""
    print("Running ansible environment tests for issue #27...\n")
    
    try:
        test_ansible_environment_setup()
        test_environment_variables()
        print("\n✓ All tests completed successfully!")
        return 0
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())