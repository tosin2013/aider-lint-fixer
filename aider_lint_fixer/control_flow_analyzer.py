#!/usr/bin/env python3
"""
Control Flow Analysis Integration

This module implements control flow analysis capabilities to analyze conditional statements,
loop structures, and exception handling patterns, implementing Phase 2 of the logic tracing
enhancement strategy.

Based on research findings that Phase 2 would add control flow analysis capabilities to the
error analyzer module to analyze conditional statements, loop structures, and exception
handling patterns to understand the logical structure of code around lint errors.

Key Features:
- Control flow graph construction
- Conditional statement analysis
- Loop structure detection
- Exception handling pattern analysis
- Variable scoping within control structures
- Dead code detection
- Unreachable code identification
"""

import ast
import logging
import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)


class ControlFlowNodeType(Enum):
    """Types of control flow nodes."""

    ENTRY = "entry"
    EXIT = "exit"
    STATEMENT = "statement"
    CONDITION = "condition"
    LOOP_HEADER = "loop_header"
    LOOP_BODY = "loop_body"
    EXCEPTION_HANDLER = "exception_handler"
    FUNCTION_CALL = "function_call"
    RETURN = "return"
    BREAK = "break"
    CONTINUE = "continue"


@dataclass
class ControlFlowNode:
    """Represents a node in the control flow graph."""

    node_id: str
    node_type: ControlFlowNodeType
    line_number: int
    code_snippet: str
    predecessors: Set[str] = field(default_factory=set)
    successors: Set[str] = field(default_factory=set)
    variables_read: Set[str] = field(default_factory=set)
    variables_written: Set[str] = field(default_factory=set)
    conditions: List[str] = field(default_factory=list)
    is_reachable: bool = True


@dataclass
class ControlStructure:
    """Represents a control structure (if, loop, try-catch)."""

    structure_type: str  # if, for, while, try, with
    start_line: int
    end_line: int
    condition: Optional[str] = None
    variables_in_condition: Set[str] = field(default_factory=set)
    nested_structures: List["ControlStructure"] = field(default_factory=list)
    complexity_score: float = 0.0


@dataclass
class ControlFlowAnalysis:
    """Results of control flow analysis."""

    file_path: str
    control_flow_graph: Dict[str, ControlFlowNode] = field(default_factory=dict)
    control_structures: List[ControlStructure] = field(default_factory=list)
    unreachable_code: List[int] = field(default_factory=list)
    dead_variables: Set[str] = field(default_factory=set)
    complexity_metrics: Dict[str, float] = field(default_factory=dict)
    scoping_issues: List[Dict] = field(default_factory=list)


class ControlFlowAnalyzer:
    """Analyzes control flow patterns in code."""

    def __init__(self):
        self.current_analysis = None
        self.node_counter = 0

    def analyze_file(self, file_path: str, error_lines: Set[int] = None) -> ControlFlowAnalysis:
        """Analyze control flow for a file, focusing on areas with errors."""

        self.current_analysis = ControlFlowAnalysis(file_path=file_path)
        self.node_counter = 0

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Determine file type and analyze accordingly
            file_ext = Path(file_path).suffix.lower()

            if file_ext == ".py":
                self._analyze_python_control_flow(content, error_lines)
            elif file_ext in [".js", ".ts", ".jsx", ".tsx"]:
                self._analyze_javascript_control_flow(content, error_lines)
            else:
                logger.debug(f"Control flow analysis not supported for {file_ext}")
                return self.current_analysis

            # Perform additional analysis
            self._detect_unreachable_code()
            self._analyze_variable_scoping()
            self._calculate_complexity_metrics()

        except Exception as e:
            logger.warning(f"Control flow analysis failed for {file_path}: {e}")

        return self.current_analysis

    def _analyze_python_control_flow(self, content: str, error_lines: Set[int] = None):
        """Analyze Python control flow using AST."""

        try:
            tree = ast.parse(content)
            self._build_python_cfg(tree)
            self._extract_python_control_structures(tree)
        except SyntaxError as e:
            logger.warning(f"Python syntax error, skipping control flow analysis: {e}")

    def _analyze_javascript_control_flow(self, content: str, error_lines: Set[int] = None):
        """Analyze JavaScript control flow using regex patterns."""

        lines = content.split("\n")

        # Build basic control flow graph using pattern matching
        self._build_javascript_cfg_from_patterns(lines)
        self._extract_javascript_control_structures(lines)

    def _build_python_cfg(self, tree: ast.AST):
        """Build control flow graph for Python code."""

        # Create entry node
        entry_node = self._create_node(ControlFlowNodeType.ENTRY, 1, "# Entry point")

        current_nodes = [entry_node.node_id]

        # Process AST nodes
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For)):
                current_nodes = self._process_python_control_node(node, current_nodes)
            elif isinstance(node, ast.Try):
                current_nodes = self._process_python_try_node(node, current_nodes)
            elif isinstance(node, (ast.Return, ast.Break, ast.Continue)):
                current_nodes = self._process_python_jump_node(node, current_nodes)
            elif isinstance(node, ast.FunctionDef):
                self._process_python_function_node(node)

    def _process_python_control_node(
        self, node: Union[ast.If, ast.While, ast.For], current_nodes: List[str]
    ) -> List[str]:
        """Process Python control flow nodes (if, while, for)."""

        # Create condition node - handle different node types
        if isinstance(node, ast.For):
            # For loops have 'iter' instead of 'test'
            condition_code = ast.unparse(node.iter) if hasattr(ast, "unparse") else str(node.iter)
        else:
            # If and While have 'test'
            condition_code = ast.unparse(node.test) if hasattr(ast, "unparse") else str(node.test)

        condition_node = self._create_node(
            ControlFlowNodeType.CONDITION, node.lineno, condition_code
        )

        # Connect current nodes to condition
        for current_id in current_nodes:
            self._add_edge(current_id, condition_node.node_id)

        # Process body
        body_nodes = []
        if isinstance(node, ast.If):
            body_nodes = self._process_python_block(node.body, [condition_node.node_id])

            # Process else block if present
            if node.orelse:
                else_nodes = self._process_python_block(node.orelse, [condition_node.node_id])
                body_nodes.extend(else_nodes)

        elif isinstance(node, (ast.While, ast.For)):
            # Create loop header
            loop_header = self._create_node(
                ControlFlowNodeType.LOOP_HEADER, node.lineno, f"Loop: {condition_code}"
            )
            self._add_edge(condition_node.node_id, loop_header.node_id)

            # Process loop body
            body_nodes = self._process_python_block(node.body, [loop_header.node_id])

            # Add back edge for loop
            for body_node in body_nodes:
                self._add_edge(body_node, condition_node.node_id)

        return body_nodes if body_nodes else [condition_node.node_id]

    def _process_python_try_node(self, node: ast.Try, current_nodes: List[str]) -> List[str]:
        """Process Python try-except blocks."""

        # Process try block
        try_nodes = self._process_python_block(node.body, current_nodes)

        # Process exception handlers
        handler_nodes = []
        for handler in node.handlers:
            handler_node = self._create_node(
                ControlFlowNodeType.EXCEPTION_HANDLER,
                handler.lineno,
                f"except {handler.type.id if handler.type else 'Exception'}",
            )

            # Connect from try block (potential exception points)
            for try_node in try_nodes:
                self._add_edge(try_node, handler_node.node_id)

            # Process handler body
            handler_body = self._process_python_block(handler.body, [handler_node.node_id])
            handler_nodes.extend(handler_body)

        # Process finally block
        finally_nodes = []
        if node.finalbody:
            finally_nodes = self._process_python_block(node.finalbody, try_nodes + handler_nodes)

        return finally_nodes if finally_nodes else (try_nodes + handler_nodes)

    def _process_python_jump_node(
        self, node: Union[ast.Return, ast.Break, ast.Continue], current_nodes: List[str]
    ) -> List[str]:
        """Process Python jump statements."""

        if isinstance(node, ast.Return):
            node_type = ControlFlowNodeType.RETURN
            code = f"return {ast.unparse(node.value) if node.value else ''}"
        elif isinstance(node, ast.Break):
            node_type = ControlFlowNodeType.BREAK
            code = "break"
        else:  # Continue
            node_type = ControlFlowNodeType.CONTINUE
            code = "continue"

        jump_node = self._create_node(node_type, node.lineno, code)

        for current_id in current_nodes:
            self._add_edge(current_id, jump_node.node_id)

        return [jump_node.node_id]

    def _process_python_function_node(self, node: ast.FunctionDef):
        """Process Python function definitions."""

        func_node = self._create_node(
            ControlFlowNodeType.FUNCTION_CALL, node.lineno, f"def {node.name}(...)"
        )

        # Analyze function arguments for variable definitions
        for arg in node.args.args:
            func_node.variables_written.add(arg.arg)

    def _process_python_block(
        self, statements: List[ast.stmt], entry_nodes: List[str]
    ) -> List[str]:
        """Process a block of Python statements."""

        current_nodes = entry_nodes

        for stmt in statements:
            stmt_node = self._create_node(
                ControlFlowNodeType.STATEMENT,
                stmt.lineno,
                ast.unparse(stmt) if hasattr(ast, "unparse") else str(stmt)[:50],
            )

            for current_id in current_nodes:
                self._add_edge(current_id, stmt_node.node_id)

            current_nodes = [stmt_node.node_id]

        return current_nodes

    def _build_javascript_cfg_from_patterns(self, lines: List[str]):
        """Build control flow graph for JavaScript using pattern matching."""

        entry_node = self._create_node(ControlFlowNodeType.ENTRY, 1, "// Entry point")

        current_nodes = [entry_node.node_id]

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("//"):
                continue

            # Detect control structures
            if re.match(r"\s*if\s*\(", line):
                condition_node = self._create_node(ControlFlowNodeType.CONDITION, i, line)
                for current_id in current_nodes:
                    self._add_edge(current_id, condition_node.node_id)
                current_nodes = [condition_node.node_id]

            elif re.match(r"\s*(for|while)\s*\(", line):
                loop_node = self._create_node(ControlFlowNodeType.LOOP_HEADER, i, line)
                for current_id in current_nodes:
                    self._add_edge(current_id, loop_node.node_id)
                current_nodes = [loop_node.node_id]

            elif re.match(r"\s*try\s*{", line):
                try_node = self._create_node(ControlFlowNodeType.STATEMENT, i, line)
                for current_id in current_nodes:
                    self._add_edge(current_id, try_node.node_id)
                current_nodes = [try_node.node_id]

            elif re.match(r"\s*catch\s*\(", line):
                catch_node = self._create_node(ControlFlowNodeType.EXCEPTION_HANDLER, i, line)
                # Connect to previous nodes (exception can occur anywhere)
                for current_id in current_nodes:
                    self._add_edge(current_id, catch_node.node_id)
                current_nodes = [catch_node.node_id]

            elif re.match(r"\s*return\b", line):
                return_node = self._create_node(ControlFlowNodeType.RETURN, i, line)
                for current_id in current_nodes:
                    self._add_edge(current_id, return_node.node_id)
                current_nodes = [return_node.node_id]

            else:
                # Regular statement
                stmt_node = self._create_node(ControlFlowNodeType.STATEMENT, i, line)
                for current_id in current_nodes:
                    self._add_edge(current_id, stmt_node.node_id)
                current_nodes = [stmt_node.node_id]

    def _extract_python_control_structures(self, tree: ast.AST):
        """Extract control structures from Python AST."""

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                structure = ControlStructure(
                    structure_type="if",
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    condition=(
                        ast.unparse(node.test) if hasattr(ast, "unparse") else str(node.test)
                    ),
                )
                self._analyze_control_structure_complexity(structure, node)
                self.current_analysis.control_structures.append(structure)

            elif isinstance(node, (ast.For, ast.While)):
                structure = ControlStructure(
                    structure_type="for" if isinstance(node, ast.For) else "while",
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    condition=(
                        ast.unparse(node.test if hasattr(node, "test") else node.iter)
                        if hasattr(ast, "unparse")
                        else str(node)
                    ),
                )
                self._analyze_control_structure_complexity(structure, node)
                self.current_analysis.control_structures.append(structure)

            elif isinstance(node, ast.Try):
                structure = ControlStructure(
                    structure_type="try",
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                )
                self._analyze_control_structure_complexity(structure, node)
                self.current_analysis.control_structures.append(structure)

    def _extract_javascript_control_structures(self, lines: List[str]):
        """Extract control structures from JavaScript code."""

        for i, line in enumerate(lines, 1):
            line = line.strip()

            if re.match(r"\s*if\s*\(", line):
                condition_match = re.search(r"if\s*\(([^)]+)\)", line)
                condition = condition_match.group(1) if condition_match else ""

                structure = ControlStructure(
                    structure_type="if",
                    start_line=i,
                    end_line=i,  # Simplified - would need proper parsing
                    condition=condition,
                )
                self.current_analysis.control_structures.append(structure)

            elif re.match(r"\s*(for|while)\s*\(", line):
                loop_type = "for" if line.strip().startswith("for") else "while"
                condition_match = re.search(r"(for|while)\s*\(([^)]+)\)", line)
                condition = condition_match.group(2) if condition_match else ""

                structure = ControlStructure(
                    structure_type=loop_type,
                    start_line=i,
                    end_line=i,
                    condition=condition,
                )
                self.current_analysis.control_structures.append(structure)

    def _analyze_control_structure_complexity(self, structure: ControlStructure, ast_node):
        """Analyze complexity of a control structure."""

        # Calculate nesting depth
        nesting_depth = 0
        for other_structure in self.current_analysis.control_structures:
            if (
                other_structure.start_line < structure.start_line
                and other_structure.end_line > structure.end_line
            ):
                nesting_depth += 1

        # Calculate complexity score
        base_complexity = 1.0
        nesting_penalty = nesting_depth * 0.5

        # Additional complexity for specific structures
        if structure.structure_type in ["for", "while"]:
            base_complexity += 1.0
        elif structure.structure_type == "if":
            base_complexity += 0.5
        elif structure.structure_type == "try":
            base_complexity += 1.5

        structure.complexity_score = base_complexity + nesting_penalty

    def _detect_unreachable_code(self):
        """Detect unreachable code in the control flow graph."""

        if not self.current_analysis.control_flow_graph:
            return

        # Find entry nodes
        entry_nodes = [
            node_id
            for node_id, node in self.current_analysis.control_flow_graph.items()
            if node.node_type == ControlFlowNodeType.ENTRY
        ]

        if not entry_nodes:
            return

        # Perform reachability analysis using BFS
        reachable = set()
        queue = deque(entry_nodes)

        while queue:
            current_id = queue.popleft()
            if current_id in reachable:
                continue

            reachable.add(current_id)
            current_node = self.current_analysis.control_flow_graph[current_id]

            for successor_id in current_node.successors:
                if successor_id not in reachable:
                    queue.append(successor_id)

        # Mark unreachable nodes
        for node_id, node in self.current_analysis.control_flow_graph.items():
            if node_id not in reachable:
                node.is_reachable = False
                self.current_analysis.unreachable_code.append(node.line_number)

    def _analyze_variable_scoping(self):
        """Analyze variable scoping issues."""

        # Track variable definitions and uses across control flow
        variable_defs = defaultdict(set)  # variable -> set of line numbers where defined
        variable_uses = defaultdict(set)  # variable -> set of line numbers where used

        for node in self.current_analysis.control_flow_graph.values():
            for var in node.variables_written:
                variable_defs[var].add(node.line_number)
            for var in node.variables_read:
                variable_uses[var].add(node.line_number)

        # Detect potential scoping issues
        for var, use_lines in variable_uses.items():
            def_lines = variable_defs.get(var, set())

            if not def_lines:
                # Variable used but never defined (potential undefined variable)
                self.current_analysis.scoping_issues.append(
                    {
                        "type": "undefined_variable",
                        "variable": var,
                        "lines": list(use_lines),
                    }
                )

            elif len(def_lines) > 1:
                # Variable defined multiple times (potential shadowing)
                self.current_analysis.scoping_issues.append(
                    {
                        "type": "variable_redefinition",
                        "variable": var,
                        "definition_lines": list(def_lines),
                        "use_lines": list(use_lines),
                    }
                )

        # Detect dead variables (defined but never used)
        for var, def_lines in variable_defs.items():
            if var not in variable_uses:
                self.current_analysis.dead_variables.add(var)

    def _calculate_complexity_metrics(self):
        """Calculate various complexity metrics."""

        # Cyclomatic complexity (simplified)
        decision_nodes = sum(
            1
            for node in self.current_analysis.control_flow_graph.values()
            if node.node_type in [ControlFlowNodeType.CONDITION, ControlFlowNodeType.LOOP_HEADER]
        )

        cyclomatic_complexity = decision_nodes + 1

        # Nesting depth
        max_nesting = max(
            (s.complexity_score for s in self.current_analysis.control_structures),
            default=0,
        )

        # Control structure density
        total_lines = max(
            (node.line_number for node in self.current_analysis.control_flow_graph.values()),
            default=1,
        )
        control_density = len(self.current_analysis.control_structures) / total_lines

        self.current_analysis.complexity_metrics = {
            "cyclomatic_complexity": cyclomatic_complexity,
            "max_nesting_depth": max_nesting,
            "control_structure_density": control_density,
            "total_control_structures": len(self.current_analysis.control_structures),
            "unreachable_lines": len(self.current_analysis.unreachable_code),
        }

    def _create_node(
        self, node_type: ControlFlowNodeType, line_number: int, code_snippet: str
    ) -> ControlFlowNode:
        """Create a new control flow node."""

        self.node_counter += 1
        node_id = f"node_{self.node_counter}"

        node = ControlFlowNode(
            node_id=node_id,
            node_type=node_type,
            line_number=line_number,
            code_snippet=code_snippet,
        )

        self.current_analysis.control_flow_graph[node_id] = node
        return node

    def _add_edge(self, from_node_id: str, to_node_id: str):
        """Add an edge between two nodes."""

        if (
            from_node_id in self.current_analysis.control_flow_graph
            and to_node_id in self.current_analysis.control_flow_graph
        ):

            self.current_analysis.control_flow_graph[from_node_id].successors.add(to_node_id)
            self.current_analysis.control_flow_graph[to_node_id].predecessors.add(from_node_id)

    def get_control_flow_insights(self, error_line: int) -> Dict[str, any]:
        """Get control flow insights for a specific error line."""

        if not self.current_analysis:
            return {}

        insights = {
            "in_control_structure": False,
            "control_structure_type": None,
            "nesting_level": 0,
            "reachable": True,
            "complexity_context": "low",
        }

        # Find control structures containing the error line
        containing_structures = []
        for structure in self.current_analysis.control_structures:
            if structure.start_line <= error_line <= structure.end_line:
                containing_structures.append(structure)

        if containing_structures:
            insights["in_control_structure"] = True
            insights["control_structure_type"] = containing_structures[0].structure_type
            insights["nesting_level"] = len(containing_structures)

            # Determine complexity context
            max_complexity = max(s.complexity_score for s in containing_structures)
            if max_complexity > 3:
                insights["complexity_context"] = "high"
            elif max_complexity > 1.5:
                insights["complexity_context"] = "medium"

        # Check reachability
        error_nodes = [
            node
            for node in self.current_analysis.control_flow_graph.values()
            if node.line_number == error_line
        ]

        if error_nodes and not error_nodes[0].is_reachable:
            insights["reachable"] = False

        return insights
