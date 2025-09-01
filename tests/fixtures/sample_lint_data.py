"""
Sample lint data generators for testing aider-lint-fixer.

This module provides fixtures and data generators for creating realistic
lint error scenarios across different programming languages and linters.
"""

from typing import Dict, List, Any


class PythonLintData:
    """Sample lint errors and data for Python linters."""
    
    # Flake8 sample errors
    FLAKE8_ERRORS = [
        {
            "file_path": "example.py",
            "line": 1,
            "column": 80,
            "rule_id": "E501",
            "message": "line too long (85 > 79 characters)",
            "severity": "ERROR",
            "linter": "flake8"
        },
        {
            "file_path": "example.py", 
            "line": 5,
            "column": 1,
            "rule_id": "E302",
            "message": "expected 2 blank lines, found 1",
            "severity": "ERROR",
            "linter": "flake8"
        },
        {
            "file_path": "utils.py",
            "line": 12,
            "column": 15,
            "rule_id": "F841",
            "message": "local variable 'unused_var' is assigned to but never used",
            "severity": "WARNING",
            "linter": "flake8"
        }
    ]
    
    # Pylint sample errors
    PYLINT_ERRORS = [
        {
            "file_path": "module.py",
            "line": 8,
            "column": 0,
            "rule_id": "C0103",
            "message": "Invalid name 'x' (should match snake_case naming style)",
            "severity": "CONVENTION",
            "linter": "pylint"
        },
        {
            "file_path": "module.py",
            "line": 15,
            "column": 4,
            "rule_id": "W0613",
            "message": "Unused argument 'arg'",
            "severity": "WARNING", 
            "linter": "pylint"
        }
    ]
    
    # Sample problematic Python code
    PROBLEMATIC_CODE = """#!/usr/bin/env python3
# This file contains various Python lint violations for testing

import os
import sys
import json  # unused import

def very_long_function_name_that_exceeds_the_recommended_line_length_limit(parameter_one, parameter_two, parameter_three):
    x=1# missing spaces around operator
    y = 2
    unused_variable = 42
    
    if x==1:# missing spaces around operator
        print("x is 1")
    
    return parameter_one+parameter_two# missing spaces

class badClassName:# should be PascalCase
    def method_with_unused_arg(self, used_arg, unused_arg):
        return used_arg
    
    def method_missing_docstring(self):
        pass

# Missing newline at end of file"""

    # Sample well-formatted Python code
    CLEAN_CODE = """#!/usr/bin/env python3
\"\"\"
A well-formatted Python module that follows PEP 8 guidelines.
\"\"\"

import os
import sys
from typing import Optional


def calculate_sum(first_number: int, second_number: int) -> int:
    \"\"\"Calculate the sum of two integers.
    
    Args:
        first_number: The first integer to add
        second_number: The second integer to add
        
    Returns:
        The sum of the two integers
    \"\"\"
    return first_number + second_number


class Calculator:
    \"\"\"A simple calculator class.\"\"\"
    
    def __init__(self):
        \"\"\"Initialize the calculator.\"\"\"
        self.history = []
    
    def add(self, first: int, second: int) -> int:
        \"\"\"Add two numbers and return the result.\"\"\"
        result = first + second
        self.history.append(f"{first} + {second} = {result}")
        return result


if __name__ == "__main__":
    calc = Calculator()
    result = calc.add(5, 3)
    print(f"Result: {result}")
"""


class JavaScriptLintData:
    """Sample lint errors and data for JavaScript linters."""
    
    # ESLint sample errors
    ESLINT_ERRORS = [
        {
            "file_path": "app.js",
            "line": 3,
            "column": 25,
            "rule_id": "semi",
            "message": "Missing semicolon",
            "severity": "ERROR",
            "linter": "eslint"
        },
        {
            "file_path": "app.js",
            "line": 7,
            "column": 5,
            "rule_id": "no-unused-vars",
            "message": "'unusedVar' is defined but never used",
            "severity": "WARNING",
            "linter": "eslint"
        },
        {
            "file_path": "utils.js",
            "line": 12,
            "column": 1,
            "rule_id": "no-console",
            "message": "Unexpected console statement",
            "severity": "WARNING",
            "linter": "eslint"
        }
    ]
    
    # Sample problematic JavaScript code
    PROBLEMATIC_CODE = """// Problematic JavaScript code with lint violations

function badFunction(param1,param2){// missing spaces
    var unusedVar = 42
    let x=1// missing semicolon, spaces around operator
    
    if(x==1){// missing spaces
        console.log("x is 1")// missing semicolon
    }
    
    return param1+param2// missing spaces, semicolon
}

// Missing 'use strict'
// Inconsistent indentation
  function anotherFunction() {
      var a = 1;
        var b = 2;// inconsistent indentation
    return a + b;
  }
"""

    # Sample clean JavaScript code
    CLEAN_CODE = """'use strict';

/**
 * A well-formatted JavaScript module.
 */

function calculateSum(firstNumber, secondNumber) {
    if (typeof firstNumber !== 'number' || typeof secondNumber !== 'number') {
        throw new Error('Arguments must be numbers');
    }
    
    return firstNumber + secondNumber;
}

class Calculator {
    constructor() {
        this.history = [];
    }
    
    add(first, second) {
        const result = first + second;
        this.history.push(`${first} + ${second} = ${result}`);
        return result;
    }
    
    getHistory() {
        return [...this.history];
    }
}

module.exports = { calculateSum, Calculator };
"""


class AnsibleLintData:
    """Sample lint errors and data for Ansible linters."""
    
    # Ansible-lint sample errors
    ANSIBLE_LINT_ERRORS = [
        {
            "file_path": "playbook.yml",
            "line": 8,
            "column": 1,
            "rule_id": "yaml[line-length]",
            "message": "line too long (120 > 80 characters)",
            "severity": "MEDIUM",
            "linter": "ansible-lint"
        },
        {
            "file_path": "playbook.yml",
            "line": 12,
            "column": 5,
            "rule_id": "name[missing]",
            "message": "All tasks should be named",
            "severity": "MEDIUM",
            "linter": "ansible-lint"
        },
        {
            "file_path": "tasks/main.yml",
            "line": 3,
            "column": 1,
            "rule_id": "risky-shell-pipe",
            "message": "Shells that use pipes should set the pipefail option",
            "severity": "MEDIUM",
            "linter": "ansible-lint"
        }
    ]
    
    # Sample problematic Ansible playbook
    PROBLEMATIC_PLAYBOOK = """---
- hosts: all
  tasks:
    - shell: cat /etc/passwd | grep root  # risky-shell-pipe
    
    - debug:  # name[missing]
        msg: "Hello World"
    
    - name: "This is a very long task name that exceeds the recommended line length limit and should be shortened"  # yaml[line-length]
      debug:
        msg: "Too long name"
    
    - name: Use sudo without become
      shell: sudo systemctl restart nginx  # command-instead-of-shell, risky-shell-pipe
"""

    # Sample clean Ansible playbook
    CLEAN_PLAYBOOK = """---
- name: Configure web servers
  hosts: webservers
  become: true
  gather_facts: true
  
  vars:
    nginx_port: 80
    
  tasks:
    - name: Install nginx package
      package:
        name: nginx
        state: present
        
    - name: Start and enable nginx service
      systemd:
        name: nginx
        state: started
        enabled: true
        
    - name: Configure nginx with custom port
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/nginx.conf
        backup: true
      notify: restart nginx
      
  handlers:
    - name: restart nginx
      systemd:
        name: nginx
        state: restarted
"""


class ConfigurationTemplates:
    """Configuration file templates for different linters."""
    
    FLAKE8_CONFIG = """[flake8]
max-line-length = 88
extend-ignore = E203, W503, E501
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    .venv,
    venv
per-file-ignores =
    __init__.py:F401
    test_*.py:F401,F811
"""

    PYLINT_CONFIG = """[MAIN]
load-plugins=pylint.extensions.docparams

[MESSAGES CONTROL]
disable=missing-module-docstring,
        missing-class-docstring,
        missing-function-docstring,
        too-few-public-methods

[FORMAT]
max-line-length=88
"""

    ESLINT_CONFIG = """{
  "env": {
    "node": true,
    "es2021": true
  },
  "extends": ["eslint:recommended"],
  "parserOptions": {
    "ecmaVersion": 12,
    "sourceType": "module"
  },
  "rules": {
    "semi": ["error", "always"],
    "quotes": ["error", "single"],
    "no-console": "warn",
    "no-unused-vars": "error",
    "indent": ["error", 2]
  }
}
"""

    ANSIBLE_LINT_CONFIG = """---
exclude_paths:
  - .cache/
  - .github/
  - molecule/
  - .pytest_cache/
  - venv/

use_default_rules: true

skip_list:
  - yaml[comments]
  - yaml[line-length]

warn_list:
  - experimental
"""

    PRETTIER_CONFIG = """{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 80
}
"""


def get_sample_errors_by_linter(linter_name: str) -> List[Dict[str, Any]]:
    """Get sample errors for a specific linter."""
    error_map = {
        "flake8": PythonLintData.FLAKE8_ERRORS,
        "pylint": PythonLintData.PYLINT_ERRORS,
        "eslint": JavaScriptLintData.ESLINT_ERRORS,
        "ansible-lint": AnsibleLintData.ANSIBLE_LINT_ERRORS
    }
    return error_map.get(linter_name, [])


def get_sample_code_by_language(language: str, clean: bool = False) -> str:
    """Get sample code for a specific language."""
    code_map = {
        "python": {
            "clean": PythonLintData.CLEAN_CODE,
            "problematic": PythonLintData.PROBLEMATIC_CODE
        },
        "javascript": {
            "clean": JavaScriptLintData.CLEAN_CODE,
            "problematic": JavaScriptLintData.PROBLEMATIC_CODE
        },
        "ansible": {
            "clean": AnsibleLintData.CLEAN_PLAYBOOK,
            "problematic": AnsibleLintData.PROBLEMATIC_PLAYBOOK
        }
    }
    
    code_type = "clean" if clean else "problematic"
    return code_map.get(language, {}).get(code_type, "")


def get_config_template(linter_name: str) -> str:
    """Get configuration template for a specific linter."""
    config_map = {
        "flake8": ConfigurationTemplates.FLAKE8_CONFIG,
        "pylint": ConfigurationTemplates.PYLINT_CONFIG,
        "eslint": ConfigurationTemplates.ESLINT_CONFIG,
        "ansible-lint": ConfigurationTemplates.ANSIBLE_LINT_CONFIG,
        "prettier": ConfigurationTemplates.PRETTIER_CONFIG
    }
    return config_map.get(linter_name, "")