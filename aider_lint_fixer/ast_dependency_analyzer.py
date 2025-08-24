#!/usr/bin/env python3
"""
AST-Based Dependency Analysis for Enhanced Code Logic Tracing

This module implements enhanced dependency analysis using Abstract Syntax Tree (AST) parsing
to support function-level and variable-level relationship tracking. This implements Phase 1
of the research's logic tracing enhancement strategy.

Key Features:
- Function-level dependency tracking
- Variable usage and scoping analysis
- Import/export relationship mapping
- Control flow dependency detection
- Integration with existing NetworkX dependency graph
- Language-specific AST parsing (Python, JavaScript/TypeScript)
"""

import ast
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class FunctionDependency:
    """Represents a function and its dependencies."""

    name: str
    file_path: str
    line_number: int
    calls: Set[str] = field(default_factory=set)  # Functions this function calls
    variables_used: Set[str] = field(default_factory=set)  # Variables used
    variables_defined: Set[str] = field(default_factory=set)  # Variables defined
    imports: Set[str] = field(default_factory=set)  # Modules imported


@dataclass
class VariableDependency:
    """Represents a variable and its usage patterns."""

    name: str
    file_path: str
    definition_line: Optional[int] = None
    usage_lines: List[int] = field(default_factory=list)
    scope: str = "global"  # global, function, class
    type_hint: Optional[str] = None


@dataclass
class ImportDependency:
    """Represents import relationships between files."""

    from_file: str
    to_module: str
    imported_names: Set[str] = field(default_factory=set)
    import_type: str = "import"  # import, from_import, relative_import


class PythonASTAnalyzer:
    """AST analyzer for Python files."""

    def __init__(self):
        self.functions: Dict[str, FunctionDependency] = {}
        self.variables: Dict[str, VariableDependency] = {}
        self.imports: List[ImportDependency] = []

    def analyze_file(self, file_path: str) -> Tuple[Dict, Dict, List]:
        """Analyze a Python file and extract dependencies."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=file_path)

            # Reset for this file
            self.functions = {}
            self.variables = {}
            self.imports = []

            # Analyze the AST
            self._analyze_node(tree, file_path)

            return self.functions, self.variables, self.imports

        except Exception as e:
            logger.warning(f"Failed to analyze Python file {file_path}: {e}")
            return {}, {}, []

    def _analyze_node(self, node: ast.AST, file_path: str, scope: str = "global"):
        """Recursively analyze AST nodes."""

        if isinstance(node, ast.FunctionDef):
            self._analyze_function(node, file_path, scope)

        elif isinstance(node, ast.ClassDef):
            self._analyze_class(node, file_path, scope)

        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            self._analyze_import(node, file_path)

        elif isinstance(node, ast.Assign):
            self._analyze_assignment(node, file_path, scope)

        elif isinstance(node, ast.Call):
            self._analyze_function_call(node, file_path, scope)

        # Recursively analyze child nodes
        for child in ast.iter_child_nodes(node):
            self._analyze_node(child, file_path, scope)

    def _analyze_function(self, node: ast.FunctionDef, file_path: str, scope: str):
        """Analyze function definition."""
        func_name = node.name
        func_key = f"{file_path}:{func_name}"

        func_dep = FunctionDependency(
            name=func_name, file_path=file_path, line_number=node.lineno
        )

        # Analyze function body
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and hasattr(child.func, "id"):
                func_dep.calls.add(child.func.id)
            elif isinstance(child, ast.Name):
                if isinstance(child.ctx, ast.Load):
                    func_dep.variables_used.add(child.id)
                elif isinstance(child.ctx, ast.Store):
                    func_dep.variables_defined.add(child.id)

        self.functions[func_key] = func_dep

    def _analyze_class(self, node: ast.ClassDef, file_path: str, scope: str):
        """Analyze class definition."""
        class_scope = f"{scope}.{node.name}" if scope != "global" else node.name

        # Analyze class methods
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                self._analyze_function(child, file_path, class_scope)

    def _analyze_import(self, node: Union[ast.Import, ast.ImportFrom], file_path: str):
        """Analyze import statements."""
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_dep = ImportDependency(
                    from_file=file_path,
                    to_module=alias.name,
                    imported_names={alias.asname or alias.name},
                    import_type="import",
                )
                self.imports.append(import_dep)

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imported_names = {alias.asname or alias.name for alias in node.names}

            import_dep = ImportDependency(
                from_file=file_path,
                to_module=module,
                imported_names=imported_names,
                import_type="from_import" if node.level == 0 else "relative_import",
            )
            self.imports.append(import_dep)

    def _analyze_assignment(self, node: ast.Assign, file_path: str, scope: str):
        """Analyze variable assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_key = f"{file_path}:{target.id}"

                if var_key not in self.variables:
                    self.variables[var_key] = VariableDependency(
                        name=target.id,
                        file_path=file_path,
                        definition_line=node.lineno,
                        scope=scope,
                    )
                else:
                    # Update definition line if this is a redefinition
                    self.variables[var_key].definition_line = node.lineno

    def _analyze_function_call(self, node: ast.Call, file_path: str, scope: str):
        """Analyze function calls."""
        # This is handled in _analyze_function for now
        pass


class JavaScriptASTAnalyzer:
    """AST analyzer for JavaScript/TypeScript files using regex patterns."""

    def __init__(self):
        self.functions: Dict[str, FunctionDependency] = {}
        self.variables: Dict[str, VariableDependency] = {}
        self.imports: List[ImportDependency] = []

    def analyze_file(self, file_path: str) -> Tuple[Dict, Dict, List]:
        """Analyze a JavaScript/TypeScript file using regex patterns."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Reset for this file
            self.functions = {}
            self.variables = {}
            self.imports = []

            # Analyze using regex patterns
            self._analyze_functions(content, file_path)
            self._analyze_variables(content, file_path)
            self._analyze_imports(content, file_path)

            return self.functions, self.variables, self.imports

        except Exception as e:
            logger.warning(f"Failed to analyze JavaScript file {file_path}: {e}")
            return {}, {}, []

    def _analyze_functions(self, content: str, file_path: str):
        """Analyze function definitions using regex."""
        # Function declaration patterns
        patterns = [
            r"function\s+(\w+)\s*\(",  # function name()
            r"(\w+)\s*:\s*function\s*\(",  # name: function()
            r"(\w+)\s*=\s*function\s*\(",  # name = function()
            r"(\w+)\s*=>\s*",  # arrow functions
            r"(\w+)\s*\([^)]*\)\s*{",  # method definitions
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                func_name = match.group(1)
                line_number = content[: match.start()].count("\n") + 1

                func_key = f"{file_path}:{func_name}"
                self.functions[func_key] = FunctionDependency(
                    name=func_name, file_path=file_path, line_number=line_number
                )

    def _analyze_variables(self, content: str, file_path: str):
        """Analyze variable declarations using regex."""
        # Variable declaration patterns
        patterns = [
            r"(?:var|let|const)\s+(\w+)",  # var/let/const declarations
            r"(\w+)\s*=",  # assignments
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                var_name = match.group(1)
                line_number = content[: match.start()].count("\n") + 1

                var_key = f"{file_path}:{var_name}"
                if var_key not in self.variables:
                    self.variables[var_key] = VariableDependency(
                        name=var_name, file_path=file_path, definition_line=line_number
                    )

    def _analyze_imports(self, content: str, file_path: str):
        """Analyze import statements using regex."""
        # Import patterns
        import_patterns = [
            r'import\s+(.+?)\s+from\s+[\'"](.+?)[\'"]',  # import ... from '...'
            r'import\s+[\'"](.+?)[\'"]',  # import '...'
            r'require\s*\(\s*[\'"](.+?)[\'"]\s*\)',  # require('...')
        ]

        for pattern in import_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                if len(match.groups()) == 2:
                    imported_names = {
                        name.strip() for name in match.group(1).split(",")
                    }
                    module = match.group(2)
                else:
                    imported_names = set()
                    module = match.group(1)

                import_dep = ImportDependency(
                    from_file=file_path,
                    to_module=module,
                    imported_names=imported_names,
                    import_type="import",
                )
                self.imports.append(import_dep)


class EnhancedDependencyAnalyzer:
    """Enhanced dependency analyzer that integrates AST analysis with NetworkX graphs."""

    def __init__(self):
        self.dependency_graph = nx.DiGraph()
        self.function_graph = nx.DiGraph()
        self.variable_graph = nx.DiGraph()

        self.python_analyzer = PythonASTAnalyzer()
        self.js_analyzer = JavaScriptASTAnalyzer()

        # Cache for analyzed files
        self.file_cache: Dict[str, Tuple[Dict, Dict, List]] = {}

    def analyze_files(self, file_paths: List[str]) -> nx.DiGraph:
        """Analyze multiple files and build comprehensive dependency graph."""
        self.dependency_graph.clear()
        self.function_graph.clear()
        self.variable_graph.clear()

        all_functions = {}
        all_variables = {}
        all_imports = []

        for file_path in file_paths:
            functions, variables, imports = self._analyze_single_file(file_path)

            all_functions.update(functions)
            all_variables.update(variables)
            all_imports.extend(imports)

        # Build graphs
        self._build_file_dependency_graph(all_imports)
        self._build_function_dependency_graph(all_functions)
        self._build_variable_dependency_graph(all_variables)

        return self.dependency_graph

    def _analyze_single_file(self, file_path: str) -> Tuple[Dict, Dict, List]:
        """Analyze a single file based on its extension."""
        if file_path in self.file_cache:
            return self.file_cache[file_path]

        file_ext = Path(file_path).suffix.lower()

        if file_ext == ".py":
            result = self.python_analyzer.analyze_file(file_path)
        elif file_ext in [".js", ".ts", ".jsx", ".tsx"]:
            result = self.js_analyzer.analyze_file(file_path)
        else:
            logger.debug(f"Unsupported file type for AST analysis: {file_path}")
            result = ({}, {}, [])

        self.file_cache[file_path] = result
        return result

    def _build_file_dependency_graph(self, imports: List[ImportDependency]):
        """Build file-level dependency graph from imports."""
        for import_dep in imports:
            self.dependency_graph.add_node(import_dep.from_file, type="file")

            # Try to resolve module to file path
            resolved_path = self._resolve_module_path(
                import_dep.to_module, import_dep.from_file
            )
            if resolved_path:
                self.dependency_graph.add_node(resolved_path, type="file")
                self.dependency_graph.add_edge(
                    import_dep.from_file,
                    resolved_path,
                    type="import",
                    imported_names=import_dep.imported_names,
                )

    def _build_function_dependency_graph(
        self, functions: Dict[str, FunctionDependency]
    ):
        """Build function-level dependency graph."""
        for func_key, func_dep in functions.items():
            self.function_graph.add_node(func_key, **func_dep.__dict__)

            # Add edges for function calls
            for called_func in func_dep.calls:
                # Try to find the called function in our analyzed functions
                for other_key, other_func in functions.items():
                    if other_func.name == called_func:
                        self.function_graph.add_edge(func_key, other_key, type="calls")

    def _build_variable_dependency_graph(
        self, variables: Dict[str, VariableDependency]
    ):
        """Build variable-level dependency graph."""
        for var_key, var_dep in variables.items():
            self.variable_graph.add_node(var_key, **var_dep.__dict__)

    def _resolve_module_path(self, module: str, from_file: str) -> Optional[str]:
        """Attempt to resolve module import to actual file path."""
        # This is a simplified resolution - in practice would need more sophisticated logic
        from_dir = Path(from_file).parent

        # Handle relative imports
        if module.startswith("."):
            # Relative import
            relative_path = from_dir / module.lstrip(".")
            for ext in [".py", ".js", ".ts"]:
                candidate = relative_path.with_suffix(ext)
                if candidate.exists():
                    return str(candidate)

        # Handle absolute imports (simplified)
        for ext in [".py", ".js", ".ts"]:
            candidate = from_dir / f"{module}{ext}"
            if candidate.exists():
                return str(candidate)

        return None

    def get_function_dependencies(self, file_path: str) -> List[str]:
        """Get functions that depend on functions in the given file."""
        dependencies = []

        for node in self.function_graph.nodes():
            if node.startswith(file_path + ":"):
                # Find all functions that call this function
                for pred in self.function_graph.predecessors(node):
                    pred_file = pred.split(":")[0]
                    if pred_file != file_path:
                        dependencies.append(pred_file)

        return list(set(dependencies))

    def get_variable_dependencies(self, file_path: str) -> List[str]:
        """Get files that might be affected by variable changes in the given file."""
        # This is a simplified implementation
        # In practice, would need more sophisticated analysis
        dependencies = []

        # For now, return files that import from this file
        for edge in self.dependency_graph.edges(data=True):
            if edge[1] == file_path and edge[2].get("type") == "import":
                dependencies.append(edge[0])

        return dependencies
