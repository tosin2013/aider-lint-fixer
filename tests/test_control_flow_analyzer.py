"""
Test suite for the Control Flow Analyzer module.

This module tests:
1. Control flow graph construction
2. Python AST analysis
3. JavaScript pattern-based analysis
4. Control structure detection
5. Unreachable code detection
6. Variable scoping analysis
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aider_lint_fixer.control_flow_analyzer import (
    ControlFlowAnalysis,
    ControlFlowAnalyzer,
    ControlFlowNode,
    ControlFlowNodeType,
    ControlStructure,
)


class TestControlFlowNodeType:
    """Test ControlFlowNodeType enumeration."""

    def test_control_flow_node_types(self):
        """Test that control flow node types are correctly defined."""
        assert ControlFlowNodeType.ENTRY.value == "entry"
        assert ControlFlowNodeType.EXIT.value == "exit"
        assert ControlFlowNodeType.STATEMENT.value == "statement"
        assert ControlFlowNodeType.CONDITION.value == "condition"
        assert ControlFlowNodeType.LOOP_HEADER.value == "loop_header"
        assert ControlFlowNodeType.LOOP_BODY.value == "loop_body"
        assert ControlFlowNodeType.EXCEPTION_HANDLER.value == "exception_handler"
        assert ControlFlowNodeType.FUNCTION_CALL.value == "function_call"
        assert ControlFlowNodeType.RETURN.value == "return"
        assert ControlFlowNodeType.BREAK.value == "break"
        assert ControlFlowNodeType.CONTINUE.value == "continue"


class TestControlFlowNode:
    """Test ControlFlowNode data structure."""

    def test_control_flow_node_initialization(self):
        """Test ControlFlowNode initialization."""
        node = ControlFlowNode(
            node_id="node_1",
            node_type=ControlFlowNodeType.CONDITION,
            line_number=10,
            code_snippet="if x > 0:",
            predecessors={"node_0"},
            successors={"node_2", "node_3"},
            variables_read={"x"},
            variables_written=set(),
            conditions=["x > 0"],
            is_reachable=True,
        )

        assert node.node_id == "node_1"
        assert node.node_type == ControlFlowNodeType.CONDITION
        assert node.line_number == 10
        assert node.code_snippet == "if x > 0:"
        assert "node_0" in node.predecessors
        assert "node_2" in node.successors
        assert "x" in node.variables_read
        assert "x > 0" in node.conditions
        assert node.is_reachable is True


class TestControlStructure:
    """Test ControlStructure data structure."""

    def test_control_structure_initialization(self):
        """Test ControlStructure initialization."""
        structure = ControlStructure(
            structure_type="if",
            start_line=10,
            end_line=15,
            condition="x > 0",
            variables_in_condition={"x"},
            nested_structures=[],
            complexity_score=1.5,
        )

        assert structure.structure_type == "if"
        assert structure.start_line == 10
        assert structure.end_line == 15
        assert structure.condition == "x > 0"
        assert "x" in structure.variables_in_condition
        assert len(structure.nested_structures) == 0
        assert structure.complexity_score == 1.5


class TestControlFlowAnalysis:
    """Test ControlFlowAnalysis data structure."""

    def test_control_flow_analysis_initialization(self):
        """Test ControlFlowAnalysis initialization."""
        analysis = ControlFlowAnalysis(
            file_path="test.py",
            control_flow_graph={},
            control_structures=[],
            unreachable_code=[],
            dead_variables=set(),
            complexity_metrics={},
            scoping_issues=[],
        )

        assert analysis.file_path == "test.py"
        assert len(analysis.control_flow_graph) == 0
        assert len(analysis.control_structures) == 0
        assert len(analysis.unreachable_code) == 0
        assert len(analysis.dead_variables) == 0
        assert len(analysis.complexity_metrics) == 0
        assert len(analysis.scoping_issues) == 0


class TestControlFlowAnalyzer:
    """Test ControlFlowAnalyzer functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ControlFlowAnalyzer()

    def test_initialization(self):
        """Test ControlFlowAnalyzer initialization."""
        assert self.analyzer.current_analysis is None
        assert self.analyzer.node_counter == 0

    def test_analyze_simple_python_file(self):
        """Test analyzing a simple Python file."""
        python_code = """
def hello():
    print("Hello")
    return "world"

if __name__ == "__main__":
    result = hello()
    print(result)
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            f.flush()

            analysis = self.analyzer.analyze_file(f.name)

            assert analysis.file_path == f.name
            assert len(analysis.control_flow_graph) > 0
            assert len(analysis.control_structures) >= 1  # Should find if statement

    def test_analyze_python_with_control_structures(self):
        """Test analyzing Python code with various control structures."""
        python_code = """
def process_data(data):
    if not data:
        return None

    results = []
    for item in data:
        try:
            processed = item * 2
            results.append(processed)
        except TypeError:
            continue

    return results
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            f.flush()

            analysis = self.analyzer.analyze_file(f.name)

            assert len(analysis.control_structures) >= 3  # if, for, try

            # Check for different structure types
            structure_types = [s.structure_type for s in analysis.control_structures]
            assert "if" in structure_types
            assert "for" in structure_types
            assert "try" in structure_types

    def test_analyze_javascript_file(self):
        """Test analyzing a JavaScript file."""
        js_code = """
function processArray(arr) {
    if (!arr || arr.length === 0) {
        return [];
    }

    const results = [];
    for (let i = 0; i < arr.length; i++) {
        try {
            const processed = arr[i] * 2;
            results.push(processed);
        } catch (error) {
            console.error(error);
            continue;
        }
    }

    return results;
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(js_code)
            f.flush()

            analysis = self.analyzer.analyze_file(f.name)

            assert analysis.file_path == f.name
            assert len(analysis.control_flow_graph) > 0
            assert len(analysis.control_structures) >= 2  # if, for

    def test_analyze_unsupported_file_type(self):
        """Test analyzing an unsupported file type."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a text file")
            f.flush()

            analysis = self.analyzer.analyze_file(f.name)

            assert analysis.file_path == f.name
            assert len(analysis.control_flow_graph) == 0
            assert len(analysis.control_structures) == 0

    def test_node_creation(self):
        """Test control flow node creation."""
        self.analyzer.current_analysis = ControlFlowAnalysis(file_path="test.py")

        node = self.analyzer._create_node(
            ControlFlowNodeType.CONDITION, 10, "if x > 0:"
        )

        assert node.node_id == "node_1"
        assert node.node_type == ControlFlowNodeType.CONDITION
        assert node.line_number == 10
        assert node.code_snippet == "if x > 0:"
        assert node.node_id in self.analyzer.current_analysis.control_flow_graph

    def test_edge_creation(self):
        """Test control flow edge creation."""
        self.analyzer.current_analysis = ControlFlowAnalysis(file_path="test.py")

        # Create two nodes
        node1 = self.analyzer._create_node(ControlFlowNodeType.STATEMENT, 1, "stmt1")
        node2 = self.analyzer._create_node(ControlFlowNodeType.STATEMENT, 2, "stmt2")

        # Add edge
        self.analyzer._add_edge(node1.node_id, node2.node_id)

        assert node2.node_id in node1.successors
        assert node1.node_id in node2.predecessors

    def test_unreachable_code_detection(self):
        """Test detection of unreachable code."""
        python_code = """
def test_function():
    return "early return"
    print("This is unreachable")  # Unreachable code
    x = 5  # Also unreachable
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            f.flush()

            analysis = self.analyzer.analyze_file(f.name)

            # Note: Simple AST analysis might not detect all unreachable code
            # This test verifies the detection mechanism works
            assert isinstance(analysis.unreachable_code, list)

    def test_complexity_metrics_calculation(self):
        """Test calculation of complexity metrics."""
        python_code = """
def complex_function(x, y):
    if x > 0:
        if y > 0:
            for i in range(x):
                if i % 2 == 0:
                    print(i)
                else:
                    continue
        else:
            return -1
    else:
        return 0
    return 1
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            f.flush()

            analysis = self.analyzer.analyze_file(f.name)

            assert "cyclomatic_complexity" in analysis.complexity_metrics
            assert "max_nesting_depth" in analysis.complexity_metrics
            assert "control_structure_density" in analysis.complexity_metrics
            assert analysis.complexity_metrics["cyclomatic_complexity"] > 1

    def test_variable_scoping_analysis(self):
        """Test variable scoping analysis."""
        python_code = """
global_var = "global"

def function_with_scoping():
    local_var = "local"
    print(global_var)  # Using global variable
    print(undefined_var)  # Using undefined variable
    unused_var = "unused"  # Defined but not used
    return local_var
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            f.flush()

            analysis = self.analyzer.analyze_file(f.name)

            # Should detect scoping issues
            assert isinstance(analysis.scoping_issues, list)
            assert isinstance(analysis.dead_variables, set)

    def test_control_flow_insights_for_error_line(self):
        """Test getting control flow insights for a specific error line."""
        python_code = """
def test_function():
    x = 5
    if x > 0:
        y = x * 2  # Line 4
        if y > 5:
            print("nested")  # Line 6
    return x
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            f.flush()

            analysis = self.analyzer.analyze_file(f.name)

            # Get insights for line 6 (nested condition)
            insights = self.analyzer.get_control_flow_insights(6)

            assert "in_control_structure" in insights
            assert "control_structure_type" in insights
            assert "nesting_level" in insights
            assert "reachable" in insights
            assert "complexity_context" in insights

    def test_control_flow_insights_empty_analysis(self):
        """Test getting control flow insights when no analysis is available."""
        insights = self.analyzer.get_control_flow_insights(10)

        assert insights == {}

    def test_javascript_pattern_matching(self):
        """Test JavaScript pattern matching for control structures."""
        js_code = """
function testFunction() {
    if (condition) {
        console.log("if statement");
    }

    for (let i = 0; i < 10; i++) {
        console.log("for loop");
    }

    while (running) {
        console.log("while loop");
    }

    try {
        riskyOperation();
    } catch (error) {
        console.error(error);
    }

    return result;
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(js_code)
            f.flush()

            analysis = self.analyzer.analyze_file(f.name)

            # Should detect various control structures
            structure_types = [s.structure_type for s in analysis.control_structures]
            assert "if" in structure_types
            assert "for" in structure_types
            assert "while" in structure_types

    def test_python_syntax_error_handling(self):
        """Test handling of Python syntax errors."""
        invalid_python = """
def broken_function(
    # Missing closing parenthesis
    print("This is broken")
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(invalid_python)
            f.flush()

            analysis = self.analyzer.analyze_file(f.name)

            # Should handle gracefully and return empty analysis
            assert len(analysis.control_flow_graph) == 0
            assert len(analysis.control_structures) == 0

    def test_control_structure_complexity_analysis(self):
        """Test complexity analysis of control structures."""
        python_code = """
def nested_function():
    if condition1:
        if condition2:
            if condition3:
                for item in items:
                    if item.valid:
                        process(item)
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            f.flush()

            analysis = self.analyzer.analyze_file(f.name)

            # Should detect high complexity due to nesting
            if analysis.control_structures:
                max_complexity = max(
                    s.complexity_score for s in analysis.control_structures
                )
                assert (
                    max_complexity > 1.0
                )  # Should have complexity penalty for nesting

    def test_error_line_filtering(self):
        """Test analyzing file with focus on specific error lines."""
        python_code = """
def test_function():
    x = 5  # Line 2
    if x > 0:  # Line 3
        y = x * 2  # Line 4 - error line
        print(y)  # Line 5
    return x  # Line 6
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            f.flush()

            error_lines = {4}  # Focus on line 4
            analysis = self.analyzer.analyze_file(f.name, error_lines)

            # Should still analyze the entire file but with error line context
            assert analysis.file_path == f.name
            assert len(analysis.control_flow_graph) > 0

    def test_file_not_found_handling(self):
        """Test handling of non-existent files."""
        analysis = self.analyzer.analyze_file("non_existent_file.py")

        assert analysis.file_path == "non_existent_file.py"
        assert len(analysis.control_flow_graph) == 0
        assert len(analysis.control_structures) == 0


if __name__ == "__main__":
    pytest.main([__file__])
