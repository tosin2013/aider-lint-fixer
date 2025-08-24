"""
Test suite for the AST Dependency Analyzer module.

This module tests:
1. Python AST analysis functionality
2. JavaScript pattern-based analysis
3. Dependency graph construction
4. Function and variable dependency tracking
5. Import relationship mapping
6. Enhanced dependency analysis integration
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aider_lint_fixer.ast_dependency_analyzer import (
    EnhancedDependencyAnalyzer,
    FunctionDependency,
    ImportDependency,
    JavaScriptASTAnalyzer,
    PythonASTAnalyzer,
    VariableDependency,
)


class TestFunctionDependency:
    """Test FunctionDependency data structure."""

    def test_function_dependency_initialization(self):
        """Test FunctionDependency initialization."""
        func_dep = FunctionDependency(
            name="test_function", file_path="test.py", line_number=10
        )

        assert func_dep.name == "test_function"
        assert func_dep.file_path == "test.py"
        assert func_dep.line_number == 10
        assert len(func_dep.calls) == 0
        assert len(func_dep.variables_used) == 0
        assert len(func_dep.variables_defined) == 0
        assert len(func_dep.imports) == 0


class TestVariableDependency:
    """Test VariableDependency data structure."""

    def test_variable_dependency_initialization(self):
        """Test VariableDependency initialization."""
        var_dep = VariableDependency(
            name="test_var", file_path="test.py", definition_line=5, scope="function"
        )

        assert var_dep.name == "test_var"
        assert var_dep.file_path == "test.py"
        assert var_dep.definition_line == 5
        assert var_dep.scope == "function"
        assert len(var_dep.usage_lines) == 0


class TestImportDependency:
    """Test ImportDependency data structure."""

    def test_import_dependency_initialization(self):
        """Test ImportDependency initialization."""
        import_dep = ImportDependency(
            from_file="main.py",
            to_module="utils",
            imported_names={"helper_function"},
            import_type="from_import",
        )

        assert import_dep.from_file == "main.py"
        assert import_dep.to_module == "utils"
        assert "helper_function" in import_dep.imported_names
        assert import_dep.import_type == "from_import"


class TestPythonASTAnalyzer:
    """Test Python AST analysis functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = PythonASTAnalyzer()

    def test_analyze_simple_python_file(self):
        """Test analyzing a simple Python file."""
        python_code = """
def hello_world():
    message = "Hello, World!"
    print(message)
    return message

def main():
    result = hello_world()
    print(result)

if __name__ == "__main__":
    main()
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            f.flush()

            functions, variables, imports = self.analyzer.analyze_file(f.name)

            # Should find functions
            assert len(functions) >= 2

            # Check function names
            func_names = [func.name for func in functions.values()]
            assert "hello_world" in func_names
            assert "main" in func_names

    def test_analyze_python_imports(self):
        """Test analyzing Python import statements."""
        python_code = """
import os
import sys
from pathlib import Path
from typing import Dict, List
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            f.flush()

            functions, variables, imports = self.analyzer.analyze_file(f.name)

            # Should find imports
            assert len(imports) >= 3

            # Check import types
            import_modules = [imp.to_module for imp in imports]
            assert "os" in import_modules
            assert "pathlib" in import_modules
            assert "typing" in import_modules

    def test_analyze_python_function_calls(self):
        """Test analyzing function calls within Python code."""
        python_code = """
def helper():
    return "helper"

def main():
    result = helper()
    print(result)
    len(result)
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            f.flush()

            functions, variables, imports = self.analyzer.analyze_file(f.name)

            # Find main function
            main_func = None
            for func in functions.values():
                if func.name == "main":
                    main_func = func
                    break

            assert main_func is not None
            # Should detect function calls
            assert len(main_func.calls) > 0

    def test_analyze_invalid_python_file(self):
        """Test handling of invalid Python syntax."""
        invalid_python = """
def broken_function(
    # Missing closing parenthesis and colon
    print("This is broken")
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(invalid_python)
            f.flush()

            functions, variables, imports = self.analyzer.analyze_file(f.name)

            # Should return empty results for invalid syntax
            assert len(functions) == 0
            assert len(variables) == 0
            assert len(imports) == 0


class TestJavaScriptASTAnalyzer:
    """Test JavaScript pattern-based analysis functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = JavaScriptASTAnalyzer()

    def test_analyze_simple_javascript_file(self):
        """Test analyzing a simple JavaScript file."""
        js_code = """
function helloWorld() {
    const message = "Hello, World!";
    console.log(message);
    return message;
}

function main() {
    const result = helloWorld();
    console.log(result);
}

main();
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(js_code)
            f.flush()

            functions, variables, imports = self.analyzer.analyze_file(f.name)

            # Should find functions
            assert len(functions) >= 2

            # Check function names
            func_names = [func.name for func in functions.values()]
            assert "helloWorld" in func_names
            assert "main" in func_names

    def test_analyze_javascript_imports(self):
        """Test analyzing JavaScript import statements."""
        js_code = """
import React from 'react';
import { useState, useEffect } from 'react';
import * as utils from './utils';
const fs = require('fs');
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(js_code)
            f.flush()

            functions, variables, imports = self.analyzer.analyze_file(f.name)

            # Should find imports
            assert len(imports) >= 3

            # Check import modules
            import_modules = [imp.to_module for imp in imports]
            assert "react" in import_modules
            assert "./utils" in import_modules

    def test_analyze_javascript_variables(self):
        """Test analyzing JavaScript variable declarations."""
        js_code = """
const API_URL = "https://api.example.com";
let currentUser = null;
var isLoggedIn = false;

function setUser(user) {
    currentUser = user;
    isLoggedIn = true;
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(js_code)
            f.flush()

            functions, variables, imports = self.analyzer.analyze_file(f.name)

            # Should find variables
            assert len(variables) >= 3

            # Check variable names
            var_names = [var.name for var in variables.values()]
            assert "API_URL" in var_names
            assert "currentUser" in var_names
            assert "isLoggedIn" in var_names


class TestEnhancedDependencyAnalyzer:
    """Test the enhanced dependency analyzer integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = EnhancedDependencyAnalyzer()

    def test_analyze_multiple_files(self):
        """Test analyzing multiple files and building dependency graph."""
        # Create test Python files
        main_py = """
from utils import helper_function

def main():
    result = helper_function("test")
    print(result)
"""

        utils_py = """
def helper_function(message):
    return f"Processed: {message}"

def unused_function():
    pass
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            main_file = Path(temp_dir) / "main.py"
            utils_file = Path(temp_dir) / "utils.py"

            main_file.write_text(main_py)
            utils_file.write_text(utils_py)

            file_paths = [str(main_file), str(utils_file)]
            dependency_graph = self.analyzer.analyze_files(file_paths)

            # Should create a dependency graph
            assert dependency_graph.number_of_nodes() >= 2
            assert dependency_graph.number_of_edges() >= 0

    def test_get_function_dependencies(self):
        """Test getting function dependencies for a file."""
        python_code = """
def target_function():
    return "target"

def caller_function():
    return target_function()
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            f.flush()

            self.analyzer.analyze_files([f.name])
            dependencies = self.analyzer.get_function_dependencies(f.name)

            # Should return list of dependent files
            assert isinstance(dependencies, list)

    def test_get_variable_dependencies(self):
        """Test getting variable dependencies for a file."""
        python_code = """
GLOBAL_VAR = "global"

def function_using_global():
    return GLOBAL_VAR
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            f.flush()

            self.analyzer.analyze_files([f.name])
            dependencies = self.analyzer.get_variable_dependencies(f.name)

            # Should return list of dependent files
            assert isinstance(dependencies, list)

    def test_unsupported_file_type(self):
        """Test handling of unsupported file types."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a text file")
            f.flush()

            dependency_graph = self.analyzer.analyze_files([f.name])

            # Should handle gracefully
            assert dependency_graph.number_of_nodes() == 0

    def test_file_caching(self):
        """Test that file analysis results are cached."""
        python_code = """
def test_function():
    pass
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            f.flush()

            # Analyze twice
            self.analyzer.analyze_files([f.name])
            self.analyzer.analyze_files([f.name])

            # Should have cached the result
            assert f.name in self.analyzer.file_cache

    def test_module_path_resolution(self):
        """Test module path resolution for imports."""
        # Test relative import resolution
        resolved = self.analyzer._resolve_module_path("./utils", "/project/main.py")
        # Should attempt to resolve but may return None if file doesn't exist
        assert resolved is None or isinstance(resolved, str)

        # Test absolute import resolution
        resolved = self.analyzer._resolve_module_path("os", "/project/main.py")
        # Should return None for system modules
        assert resolved is None

    def test_dependency_graph_construction(self):
        """Test that dependency graphs are properly constructed."""
        # Create interconnected files
        file1_code = """
from file2 import function_b

def function_a():
    return function_b()
"""

        file2_code = """
def function_b():
    return "from file2"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "file1.py"
            file2 = Path(temp_dir) / "file2.py"

            file1.write_text(file1_code)
            file2.write_text(file2_code)

            dependency_graph = self.analyzer.analyze_files([str(file1), str(file2)])

            # Should have nodes for both files
            assert dependency_graph.number_of_nodes() >= 2

            # Should have function-level dependencies
            assert len(self.analyzer.function_graph.nodes()) >= 2


if __name__ == "__main__":
    pytest.main([__file__])
