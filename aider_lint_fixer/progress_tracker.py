"""
Enhanced Progress Tracking for Long-Running Lint Fixes

This module provides comprehensive progress tracking for systems with many lint failures,
including visual progress bars, time estimates, and detailed status updates.
"""

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from colorama import Fore, Style

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class ProgressStage(Enum):
    """Stages of the lint fixing process."""

    INITIALIZING = "initializing"
    ANALYZING = "analyzing"
    PROCESSING_FILES = "processing_files"
    FIXING_ERRORS = "fixing_errors"
    VERIFYING = "verifying"
    COMPLETED = "completed"


@dataclass
class ProgressMetrics:
    """Metrics for tracking progress."""

    total_files: int = 0
    processed_files: int = 0
    total_errors: int = 0
    processed_errors: int = 0
    fixed_errors: int = 0
    failed_errors: int = 0
    start_time: float = 0.0
    current_stage: ProgressStage = ProgressStage.INITIALIZING
    current_file: Optional[str] = None
    estimated_completion: Optional[datetime] = None


@dataclass
class ProgressSession:
    """Session data for progress tracking."""

    session_id: str
    project_path: str
    start_time: datetime
    metrics: ProgressMetrics
    stage_history: List[Dict[str, Any]]
    is_large_project: bool = False  # 100+ errors


class EnhancedProgressTracker:
    """Enhanced progress tracker for long-running lint fixes."""

    LARGE_PROJECT_THRESHOLD = 100  # Errors threshold for enhanced tracking
    PROGRESS_UPDATE_INTERVAL = 2.0  # Seconds between updates

    def __init__(self, project_path: str, total_errors: int, verbose: bool = False):
        """Initialize the progress tracker."""
        self.project_path = project_path
        self.total_errors = total_errors
        self.verbose = verbose
        self.is_large_project = total_errors >= self.LARGE_PROJECT_THRESHOLD

        # Initialize session
        self.session = ProgressSession(
            session_id=f"progress_{int(time.time())}",
            project_path=project_path,
            start_time=datetime.now(),
            metrics=ProgressMetrics(total_errors=total_errors, start_time=time.time()),
            stage_history=[],
            is_large_project=self.is_large_project,
        )

        # Progress bars (if tqdm available and large project)
        self.file_progress_bar = None
        self.error_progress_bar = None
        self.last_update_time = 0.0

        # Initialize progress bars for large projects
        if self.is_large_project and TQDM_AVAILABLE:
            self._init_progress_bars()

        self._log_stage_change(ProgressStage.INITIALIZING)

    def _init_progress_bars(self) -> None:
        """Initialize progress bars for large projects."""
        if not TQDM_AVAILABLE:
            return

        print(
            f"\n{Fore.CYAN}🚀 Large Project Detected ({self.total_errors} errors){Style.RESET_ALL}"
        )
        print("   Enhanced progress tracking enabled")

        # File processing progress bar
        self.file_progress_bar = tqdm(
            total=0,  # Will be set when we know total files
            desc="📁 Files",
            unit="file",
            position=0,
            leave=True,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
        )

        # Error fixing progress bar
        self.error_progress_bar = tqdm(
            total=self.total_errors,
            desc="🔧 Errors",
            unit="error",
            position=1,
            leave=True,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
        )

    def set_total_files(self, total_files: int) -> None:
        """Set the total number of files to process."""
        self.session.metrics.total_files = total_files

        if self.file_progress_bar:
            self.file_progress_bar.total = total_files
            self.file_progress_bar.refresh()

    def update_stage(self, stage: ProgressStage, details: Optional[Dict] = None) -> None:
        """Update the current processing stage."""
        self.session.metrics.current_stage = stage
        self._log_stage_change(stage, details)

        if self.is_large_project:
            stage_msg = {
                ProgressStage.ANALYZING: "🔍 Analyzing errors and planning fixes...",
                ProgressStage.PROCESSING_FILES: "📁 Processing files...",
                ProgressStage.FIXING_ERRORS: "🔧 Fixing errors with AI assistance...",
                ProgressStage.VERIFYING: "✅ Verifying fixes...",
                ProgressStage.COMPLETED: "🎉 Process completed!",
            }.get(stage, f"Processing stage: {stage.value}")

            print(f"\n{Fore.YELLOW}{stage_msg}{Style.RESET_ALL}")

    def update_file_progress(self, current_file: str, file_errors: int) -> None:
        """Update progress for file processing."""
        self.session.metrics.current_file = current_file
        self.session.metrics.processed_files += 1

        if self.file_progress_bar:
            self.file_progress_bar.set_description(f"📁 {Path(current_file).name}")
            self.file_progress_bar.update(1)

        # Update error progress bar description
        if self.error_progress_bar:
            self.error_progress_bar.set_description(f"🔧 Fixing {file_errors} errors")

    def update_error_progress(self, fixed: int = 0, failed: int = 0) -> None:
        """Update progress for error fixing."""
        self.session.metrics.fixed_errors += fixed
        self.session.metrics.failed_errors += failed
        self.session.metrics.processed_errors += fixed + failed

        if self.error_progress_bar:
            self.error_progress_bar.update(fixed + failed)

            # Update description with success rate
            total_processed = self.session.metrics.processed_errors
            success_rate = (
                (self.session.metrics.fixed_errors / total_processed * 100)
                if total_processed > 0
                else 0
            )
            self.error_progress_bar.set_description(f"🔧 Errors (Success: {success_rate:.1f}%)")

    def update_time_estimate(self) -> None:
        """Update estimated completion time."""
        if self.session.metrics.processed_errors == 0:
            return

        elapsed = time.time() - self.session.metrics.start_time
        rate = self.session.metrics.processed_errors / elapsed
        remaining_errors = self.session.metrics.total_errors - self.session.metrics.processed_errors

        if rate > 0:
            estimated_seconds = remaining_errors / rate
            self.session.metrics.estimated_completion = datetime.now() + timedelta(
                seconds=estimated_seconds
            )

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary."""
        elapsed = time.time() - self.session.metrics.start_time

        return {
            "session_id": self.session.session_id,
            "elapsed_time": elapsed,
            "total_files": self.session.metrics.total_files,
            "processed_files": self.session.metrics.processed_files,
            "total_errors": self.session.metrics.total_errors,
            "processed_errors": self.session.metrics.processed_errors,
            "fixed_errors": self.session.metrics.fixed_errors,
            "failed_errors": self.session.metrics.failed_errors,
            "success_rate": (
                (self.session.metrics.fixed_errors / self.session.metrics.processed_errors * 100)
                if self.session.metrics.processed_errors > 0
                else 0
            ),
            "current_stage": self.session.metrics.current_stage.value,
            "current_file": self.session.metrics.current_file,
            "estimated_completion": (
                self.session.metrics.estimated_completion.isoformat()
                if self.session.metrics.estimated_completion
                else None
            ),
            "is_large_project": self.is_large_project,
        }

    def print_progress_summary(self) -> None:
        """Print a detailed progress summary."""
        summary = self.get_progress_summary()
        elapsed_str = str(timedelta(seconds=int(summary["elapsed_time"])))

        print(f"\n{Fore.CYAN}📊 Progress Summary:{Style.RESET_ALL}")
        print(f"   Files: {summary['processed_files']}/{summary['total_files']}")
        print(f"   Errors: {summary['processed_errors']}/{summary['total_errors']}")
        print(f"   Fixed: {summary['fixed_errors']} ({summary['success_rate']:.1f}%)")
        print(f"   Failed: {summary['failed_errors']}")
        print(f"   Elapsed: {elapsed_str}")

        if summary["estimated_completion"]:
            eta = datetime.fromisoformat(summary["estimated_completion"])
            print(f"   ETA: {eta.strftime('%H:%M:%S')}")

    def print_real_time_status(self) -> None:
        """Print real-time status update for large projects."""
        if not self.is_large_project:
            return

        current_time = time.time()
        if current_time - self.last_update_time < self.PROGRESS_UPDATE_INTERVAL:
            return

        self.last_update_time = current_time

        # Calculate rates
        elapsed = current_time - self.session.metrics.start_time
        if elapsed > 0:
            file_rate = self.session.metrics.processed_files / elapsed * 60  # files per minute
            error_rate = self.session.metrics.processed_errors / elapsed * 60  # errors per minute

            print(f"\n{Fore.GREEN}⚡ Real-time Status:{Style.RESET_ALL}")
            print(f"   Processing rate: {file_rate:.1f} files/min, {error_rate:.1f} errors/min")

            if self.session.metrics.processed_errors > 0:
                success_rate = (
                    self.session.metrics.fixed_errors / self.session.metrics.processed_errors * 100
                )
                print(
                    f"   Success rate: {success_rate:.1f}% ({self.session.metrics.fixed_errors}/{self.session.metrics.processed_errors})"
                )

    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics for the current session."""
        elapsed = time.time() - self.session.metrics.start_time

        if elapsed == 0:
            return {
                "files_per_minute": 0.0,
                "errors_per_minute": 0.0,
                "success_rate": 0.0,
            }

        return {
            "files_per_minute": self.session.metrics.processed_files / elapsed * 60,
            "errors_per_minute": self.session.metrics.processed_errors / elapsed * 60,
            "success_rate": (
                (self.session.metrics.fixed_errors / self.session.metrics.processed_errors * 100)
                if self.session.metrics.processed_errors > 0
                else 0.0
            ),
            "elapsed_minutes": elapsed / 60,
        }

    def _log_stage_change(self, stage: ProgressStage, details: Optional[Dict] = None) -> None:
        """Log stage changes for debugging and analysis."""
        stage_entry = {
            "stage": stage.value,
            "timestamp": datetime.now().isoformat(),
            "metrics": asdict(self.session.metrics),
            "details": details or {},
        }
        self.session.stage_history.append(stage_entry)

    def save_progress(self, cache_dir: Optional[Path] = None) -> None:
        """Save progress to disk for recovery."""
        if not cache_dir:
            cache_dir = Path(self.project_path) / ".aider-lint-cache"

        cache_dir.mkdir(exist_ok=True)
        progress_file = cache_dir / f"progress_{self.session.session_id}.json"

        with open(progress_file, "w") as f:
            json.dump(asdict(self.session), f, indent=2, default=str)

    @classmethod
    def load_progress(
        cls, session_id: str, project_path: str, cache_dir: Optional[Path] = None
    ) -> Optional["EnhancedProgressTracker"]:
        """Load progress from disk for recovery."""
        if not cache_dir:
            cache_dir = Path(project_path) / ".aider-lint-cache"

        progress_file = cache_dir / f"progress_{session_id}.json"

        if not progress_file.exists():
            return None

        try:
            with open(progress_file, "r") as f:
                session_data = json.load(f)

            # Create new tracker instance
            tracker = cls.__new__(cls)
            tracker.project_path = project_path
            tracker.total_errors = session_data["metrics"]["total_errors"]
            tracker.is_large_project = session_data["is_large_project"]
            tracker.verbose = False  # Default to non-verbose for recovered sessions

            # Restore session data
            tracker.session = ProgressSession(**session_data)
            tracker.last_update_time = 0.0

            # Reinitialize progress bars if needed
            if tracker.is_large_project and TQDM_AVAILABLE:
                tracker._init_progress_bars()
                # Update progress bars to current state
                if tracker.file_progress_bar:
                    tracker.file_progress_bar.n = tracker.session.metrics.processed_files
                    tracker.file_progress_bar.refresh()
                if tracker.error_progress_bar:
                    tracker.error_progress_bar.n = tracker.session.metrics.processed_errors
                    tracker.error_progress_bar.refresh()

            print(f"\n{Fore.GREEN}🔄 Resumed progress session: {session_id}{Style.RESET_ALL}")
            tracker.print_progress_summary()

            return tracker

        except Exception as e:
            print(
                f"{Fore.YELLOW}⚠️  Failed to load progress session {session_id}: {e}{Style.RESET_ALL}"
            )
            return None

    @classmethod
    def list_recoverable_sessions(
        cls, project_path: str, cache_dir: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """List all recoverable progress sessions."""
        if not cache_dir:
            cache_dir = Path(project_path) / ".aider-lint-cache"

        if not cache_dir.exists():
            return []

        sessions = []
        for progress_file in cache_dir.glob("progress_*.json"):
            try:
                with open(progress_file, "r") as f:
                    session_data = json.load(f)

                sessions.append(
                    {
                        "session_id": session_data["session_id"],
                        "start_time": session_data["start_time"],
                        "total_errors": session_data["metrics"]["total_errors"],
                        "processed_errors": session_data["metrics"]["processed_errors"],
                        "is_large_project": session_data["is_large_project"],
                        "file_path": str(progress_file),
                    }
                )
            except Exception:
                continue  # Skip corrupted files

        return sorted(sessions, key=lambda x: x["start_time"], reverse=True)

    def cleanup_old_sessions(self, max_age_days: int = 7, cache_dir: Optional[Path] = None) -> None:
        """Clean up old progress sessions."""
        if not cache_dir:
            cache_dir = Path(self.project_path) / ".aider-lint-cache"

        if not cache_dir.exists():
            return

        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        cleaned_count = 0

        for progress_file in cache_dir.glob("progress_*.json"):
            try:
                file_time = datetime.fromtimestamp(progress_file.stat().st_mtime)
                if file_time < cutoff_time:
                    progress_file.unlink()
                    cleaned_count += 1
            except Exception:
                continue

        if cleaned_count > 0:
            print(f"   🧹 Cleaned up {cleaned_count} old progress sessions")

    def close(self) -> None:
        """Close progress bars and finalize tracking."""
        if self.file_progress_bar:
            self.file_progress_bar.close()
        if self.error_progress_bar:
            self.error_progress_bar.close()

        self.update_stage(ProgressStage.COMPLETED)

        if self.is_large_project:
            self.print_progress_summary()


def create_enhanced_progress_callback(tracker: EnhancedProgressTracker, verbose: bool = False):
    """Create an enhanced progress callback that works with the existing system."""

    def enhanced_progress_callback(progress_info: dict):
        """Enhanced progress callback with visual indicators."""
        stage = progress_info.get("stage", "unknown")

        if stage == "processing_file":
            current_file_path = progress_info.get("current_file_path", "unknown")
            file_errors = progress_info.get("file_errors", 0)

            tracker.update_file_progress(current_file_path, file_errors)

            # Always show file progress - users find it helpful regardless of project size
            current = progress_info.get("current_file", 0)
            total = progress_info.get("total_files", 0)
            print(
                f"\n{Fore.CYAN}📁 Processing file {current}/{total}: {Path(current_file_path).name} ({file_errors} errors){Style.RESET_ALL}"
            )

        elif stage == "fixing_error_group":
            complexity = progress_info.get("complexity", "unknown")
            group_errors = progress_info.get("group_errors", 0)

            # Always show error group progress - helpful for all project sizes
            print(f"   🔧 Fixing {group_errors} {complexity} errors...")

        elif stage == "file_completed":
            session_results = progress_info.get("session_results", 0)
            file_errors = progress_info.get("file_errors", 0)
            failed_errors = file_errors - session_results

            tracker.update_error_progress(fixed=session_results, failed=failed_errors)
            tracker.update_time_estimate()

            # Print real-time status for large projects
            tracker.print_real_time_status()

            # Always show completion progress - helpful for all project sizes
            completed = progress_info.get("completed_files", 0)
            total = progress_info.get("total_files", 0)
            processed_errors = progress_info.get("processed_errors", 0)
            total_errors = progress_info.get("total_errors", 0)

            print(f"   ✅ File completed: {session_results} successful fixes")

            file_progress = (completed / total * 100) if total > 0 else 0
            error_progress = (processed_errors / total_errors * 100) if total_errors > 0 else 0

            print(
                f"   📊 Progress: {completed}/{total} files ({file_progress:.1f}%), {processed_errors}/{total_errors} errors ({error_progress:.1f}%)"
            )

    return enhanced_progress_callback
