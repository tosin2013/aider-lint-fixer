"""
Performance and benchmark test utilities for aider-lint-fixer.

This module provides performance testing infrastructure including
execution time measurements, memory usage tracking, and benchmark 
comparison utilities.
"""

import functools
import gc
import time
import tracemalloc
from typing import Any, Callable, Dict, List, Optional, Tuple
from pathlib import Path
import pytest


class PerformanceTracker:
    """Track performance metrics during test execution."""
    
    def __init__(self):
        self.measurements: List[Dict[str, Any]] = []
        self.baseline_data: Dict[str, Any] = {}
    
    def measure_execution(
        self,
        func: Callable,
        name: str,
        *args,
        **kwargs
    ) -> Tuple[Any, Dict[str, Any]]:
        """Measure execution time and memory usage of a function."""
        # Start memory tracking
        tracemalloc.start()
        gc.collect()  # Clean up before measurement
        
        # Record initial memory
        snapshot_before = tracemalloc.take_snapshot()
        
        # Measure execution time
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        finally:
            end_time = time.perf_counter()
            
            # Record final memory
            snapshot_after = tracemalloc.take_snapshot()
            tracemalloc.stop()
        
        # Calculate metrics
        execution_time = end_time - start_time
        memory_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
        memory_usage = sum(stat.size_diff for stat in memory_stats) / 1024 / 1024  # MB
        
        metrics = {
            "name": name,
            "execution_time": execution_time,
            "memory_usage_mb": memory_usage,
            "timestamp": time.time()
        }
        
        self.measurements.append(metrics)
        return result, metrics
    
    def set_baseline(self, name: str, metrics: Dict[str, Any]) -> None:
        """Set baseline metrics for comparison."""
        self.baseline_data[name] = metrics
    
    def compare_to_baseline(self, name: str, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current metrics to baseline."""
        if name not in self.baseline_data:
            return {"status": "no_baseline", "metrics": current_metrics}
        
        baseline = self.baseline_data[name]
        time_ratio = current_metrics["execution_time"] / baseline["execution_time"]
        memory_ratio = current_metrics["memory_usage_mb"] / max(baseline["memory_usage_mb"], 0.001)
        
        return {
            "status": "compared",
            "time_ratio": time_ratio,
            "memory_ratio": memory_ratio,
            "time_change_percent": (time_ratio - 1) * 100,
            "memory_change_percent": (memory_ratio - 1) * 100,
            "baseline": baseline,
            "current": current_metrics
        }


def performance_test(
    name: Optional[str] = None,
    max_execution_time: Optional[float] = None,
    max_memory_mb: Optional[float] = None
):
    """Decorator for performance testing functions."""
    def decorator(func: Callable) -> Callable:
        test_name = name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracker = PerformanceTracker()
            result, metrics = tracker.measure_execution(func, test_name, *args, **kwargs)
            
            # Check against thresholds
            if max_execution_time and metrics["execution_time"] > max_execution_time:
                pytest.fail(
                    f"Function {test_name} exceeded time threshold: "
                    f"{metrics['execution_time']:.3f}s > {max_execution_time}s"
                )
            
            if max_memory_mb and metrics["memory_usage_mb"] > max_memory_mb:
                pytest.fail(
                    f"Function {test_name} exceeded memory threshold: "
                    f"{metrics['memory_usage_mb']:.2f}MB > {max_memory_mb}MB"
                )
            
            return result
        
        return wrapper
    return decorator


class BenchmarkSuite:
    """Collection of benchmark tests for common operations."""
    
    def __init__(self):
        self.tracker = PerformanceTracker()
    
    def benchmark_file_processing(
        self,
        file_processor: Callable,
        file_path: Path,
        iterations: int = 10
    ) -> Dict[str, Any]:
        """Benchmark file processing operations."""
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            file_processor(file_path)
            end = time.perf_counter()
            times.append(end - start)
        
        return {
            "min_time": min(times),
            "max_time": max(times),
            "avg_time": sum(times) / len(times),
            "total_time": sum(times),
            "iterations": iterations
        }
    
    def benchmark_linter_execution(
        self,
        linter_runner: Callable,
        project_path: Path,
        linter_name: str
    ) -> Dict[str, Any]:
        """Benchmark linter execution performance."""
        result, metrics = self.tracker.measure_execution(
            linter_runner,
            f"linter_{linter_name}",
            project_path,
            linter_name
        )
        
        return {
            "linter": linter_name,
            "execution_time": metrics["execution_time"],
            "memory_usage": metrics["memory_usage_mb"],
            "result_size": len(str(result)) if result else 0
        }
    
    def benchmark_error_analysis(
        self,
        analyzer: Callable,
        errors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Benchmark error analysis operations."""
        result, metrics = self.tracker.measure_execution(
            analyzer,
            "error_analysis",
            errors
        )
        
        return {
            "input_errors": len(errors),
            "execution_time": metrics["execution_time"],
            "memory_usage": metrics["memory_usage_mb"],
            "analysis_result": result
        }


# Performance test fixtures
@pytest.fixture
def performance_tracker():
    """Provide a performance tracker for tests."""
    return PerformanceTracker()


@pytest.fixture
def benchmark_suite():
    """Provide a benchmark suite for tests."""
    return BenchmarkSuite()


# Common performance assertions
def assert_execution_time_under(seconds: float):
    """Assert that a function executes within the given time limit."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                execution_time = time.perf_counter() - start
                assert execution_time < seconds, (
                    f"Function took {execution_time:.3f}s, "
                    f"exceeding limit of {seconds}s"
                )
        return wrapper
    return decorator


def assert_memory_usage_under(max_mb: float):
    """Assert that a function uses less than the specified memory."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracemalloc.start()
            snapshot_before = tracemalloc.take_snapshot()
            
            try:
                result = func(*args, **kwargs)
            finally:
                snapshot_after = tracemalloc.take_snapshot()
                tracemalloc.stop()
                
                memory_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
                memory_usage_mb = sum(stat.size_diff for stat in memory_stats) / 1024 / 1024
                
                assert memory_usage_mb < max_mb, (
                    f"Function used {memory_usage_mb:.2f}MB, "
                    f"exceeding limit of {max_mb}MB"
                )
            
            return result
        return wrapper
    return decorator


# Regression test utilities
class RegressionDetector:
    """Detect performance regressions by comparing to historical data."""
    
    def __init__(self, baseline_file: Optional[Path] = None):
        self.baseline_file = baseline_file or Path("performance_baseline.json")
        self.baseline_data = self._load_baseline()
    
    def _load_baseline(self) -> Dict[str, Any]:
        """Load baseline performance data."""
        if self.baseline_file.exists():
            import json
            with open(self.baseline_file) as f:
                return json.load(f)
        return {}
    
    def save_baseline(self, data: Dict[str, Any]) -> None:
        """Save baseline performance data."""
        import json
        with open(self.baseline_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def check_regression(
        self,
        test_name: str,
        current_metrics: Dict[str, Any],
        time_threshold: float = 1.5,  # 50% slower is regression
        memory_threshold: float = 1.3  # 30% more memory is regression
    ) -> Dict[str, Any]:
        """Check if current metrics indicate a performance regression."""
        if test_name not in self.baseline_data:
            return {"status": "no_baseline", "action": "save_as_baseline"}
        
        baseline = self.baseline_data[test_name]
        time_ratio = current_metrics["execution_time"] / baseline["execution_time"]
        memory_ratio = current_metrics["memory_usage_mb"] / max(baseline["memory_usage_mb"], 0.001)
        
        regressions = []
        if time_ratio > time_threshold:
            regressions.append(f"Execution time regression: {time_ratio:.2f}x slower")
        
        if memory_ratio > memory_threshold:
            regressions.append(f"Memory usage regression: {memory_ratio:.2f}x more memory")
        
        return {
            "status": "regression" if regressions else "ok",
            "regressions": regressions,
            "time_ratio": time_ratio,
            "memory_ratio": memory_ratio,
            "baseline": baseline,
            "current": current_metrics
        }