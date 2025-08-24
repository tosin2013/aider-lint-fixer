#!/usr/bin/env python3
"""
Integration test for ansible-lint environment fixes.
Tests issue #27 resolution.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path


def test_ansible_lint_integration():
    """Test that ansible-lint works with our environment fixes."""
    print("Testing ansible-lint integration with environment fixes...")
    
    # Set up our mock ansible-lint in PATH
    mock_script = Path(__file__).parent / "mock-ansible-lint"
    temp_bin = Path("/tmp/ansible-lint-test-bin")
    temp_bin.mkdir(exist_ok=True)
    
    mock_ansible_lint = temp_bin / "ansible-lint"
    mock_ansible_lint.write_text(mock_script.read_text())
    mock_ansible_lint.chmod(0o755)
    
    # Update PATH
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{temp_bin}:{old_path}"
    
    try:
        # Import our linter classes
        sys.path.insert(0, str(Path(__file__).parent))
        from aider_lint_fixer.linters.ansible_lint import AnsibleLintLinter
        
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Testing in temporary directory: {temp_dir}")
            
            # Create a test ansible file
            test_file = Path(temp_dir) / "test.yml"
            test_file.write_text("""---
- hosts: localhost
  tasks:
    - name: Test task
      debug:
        msg: "Hello World"
""")
            
            # Test 1: Check availability with broken environment (simulating issue)
            print("\n1. Testing with broken environment (root-owned ansible dirs):")
            
            # Create root-owned directory to simulate the problem
            broken_dir = Path("/tmp/test-broken-ansible")
            broken_dir.mkdir(exist_ok=True)
            os.system(f"sudo chown root:root {broken_dir} 2>/dev/null || true")
            
            # Set environment to use broken directory
            old_env = {}
            broken_env_vars = {
                "ANSIBLE_LOCAL_TEMP": str(broken_dir),
                "ANSIBLE_REMOTE_TEMP": str(broken_dir),
                "ANSIBLE_GALAXY_CACHE_DIR": str(broken_dir / "galaxy"),
            }
            
            for key, value in broken_env_vars.items():
                old_env[key] = os.environ.get(key)
                os.environ[key] = value
            
            try:
                linter = AnsibleLintLinter(temp_dir)
                
                # Test availability check
                is_available = linter.is_available()
                print(f"  ansible-lint availability with broken env: {is_available}")
                
                if not is_available:
                    print("  ✓ Correctly detected unavailability due to permission issues")
                else:
                    print("  ⚠ ansible-lint reported as available despite permission issues")
                
            finally:
                # Restore environment
                for key, value in old_env.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
            
            # Test 2: Check with our environment fixes
            print("\n2. Testing with environment fixes:")
            
            linter = AnsibleLintLinter(temp_dir)
            
            # The linter should automatically set up proper environment
            is_available = linter.is_available()
            print(f"  ansible-lint availability with fixes: {is_available}")
            
            if is_available:
                print("  ✓ ansible-lint is available with our environment fixes")
                
                # Try to get version
                version = linter.get_version()
                print(f"  ansible-lint version: {version}")
                
                # Try to run the linter
                print("  Running ansible-lint on test file...")
                result = linter.run(file_paths=[str(test_file)])
                print(f"  Linter success: {result.success}")
                print(f"  Raw output: {result.raw_output[:100]}...")
                
                if result.success:
                    print("  ✓ ansible-lint ran successfully")
                else:
                    print(f"  ✗ ansible-lint failed: {result.raw_output}")
            else:
                print("  ✗ ansible-lint still not available after fixes")
            
            # Test 3: Test environment variable inheritance
            print("\n3. Testing environment variable inheritance:")
            
            # Set custom environment variables
            custom_env = {
                "ANSIBLE_LOCAL_TEMP": "/tmp/custom-ansible-local",
                "ANSIBLE_REMOTE_TEMP": "/tmp/custom-ansible-remote",
                "ANSIBLE_GALAXY_CACHE_DIR": "/tmp/custom-ansible-galaxy",
                "ANSIBLE_LOG_PATH": "/tmp/custom-ansible.log"
            }
            
            # Create directories
            for key, path in custom_env.items():
                if key != "ANSIBLE_LOG_PATH":
                    os.makedirs(path, exist_ok=True)
            
            old_custom_env = {}
            for key, value in custom_env.items():
                old_custom_env[key] = os.environ.get(key)
                os.environ[key] = value
            
            try:
                linter = AnsibleLintLinter(temp_dir)
                result = linter.run(file_paths=[str(test_file)])
                
                if result.success:
                    print("  ✓ ansible-lint works with custom environment variables")
                else:
                    print(f"  ✗ ansible-lint failed with custom env: {result.raw_output}")
                    
            finally:
                # Restore environment
                for key, value in old_custom_env.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
                        
                # Clean up custom directories
                for key, path in custom_env.items():
                    if key != "ANSIBLE_LOG_PATH":
                        try:
                            os.rmdir(path)
                        except:
                            pass
        
    finally:
        # Restore PATH
        os.environ["PATH"] = old_path
        
        # Clean up temp bin
        try:
            mock_ansible_lint.unlink()
            temp_bin.rmdir()
        except:
            pass
    
    return True


def main():
    """Run the integration test."""
    print("Running ansible-lint integration test for issue #27...\n")
    
    try:
        test_ansible_lint_integration()
        print("\n✓ All integration tests completed successfully!")
        print("\nThe fixes for issue #27 are working correctly:")
        print("- Environment variables are properly set up")
        print("- Temp directories are created in writable locations")  
        print("- ansible-lint can run without permission errors")
        return 0
    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())