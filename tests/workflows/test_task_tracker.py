"""Tests for mcp_workspace.workflows.task_tracker module."""

from __future__ import annotations

import os

import pytest

from mcp_workspace.workflows.task_tracker import (
    TASK_TRACKER_TEMPLATE,
    TaskInfo,
    TaskTrackerError,
    TaskTrackerFileNotFoundError,
    TaskTrackerSectionNotFoundError,
    TaskTrackerStatus,
    get_incomplete_tasks,
    get_step_progress,
    get_task_counts,
    has_incomplete_work,
    is_task_done,
    validate_task_tracker,
)

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")


class TestTaskTrackerStatus:
    """Tests for TaskTrackerStatus enum."""

    def test_status_values(self) -> None:
        assert TaskTrackerStatus.COMPLETE == "COMPLETE"
        assert TaskTrackerStatus.INCOMPLETE == "INCOMPLETE"
        assert TaskTrackerStatus.N_A == "N_A"
        assert TaskTrackerStatus.ERROR == "ERROR"

    def test_status_is_string(self) -> None:
        assert isinstance(TaskTrackerStatus.COMPLETE, str)


class TestTaskInfo:
    """Tests for TaskInfo dataclass."""

    def test_create_task_info(self) -> None:
        task = TaskInfo(
            name="Test Task",
            is_complete=True,
            line_number=5,
            indentation_level=0,
        )
        assert task.name == "Test Task"
        assert task.is_complete is True
        assert task.line_number == 5
        assert task.indentation_level == 0


class TestGetIncompleteTasks:
    """Tests for get_incomplete_tasks function."""

    def test_all_incomplete(self, tmp_path: object) -> None:
        """Test with all tasks incomplete."""
        # Copy test data to tmp_path with expected structure
        tracker_content = _read_fixture("all_incomplete.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        result = get_incomplete_tasks(folder)
        assert len(result) == 3
        assert "Step 1: Create package structure" in result
        assert "Step 2: Add core module" in result
        assert "Step 3: Add tests" in result

    def test_mixed_status(self, tmp_path: object) -> None:
        """Test with mixed complete/incomplete tasks."""
        tracker_content = _read_fixture("mixed_status.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        result = get_incomplete_tasks(folder)
        assert len(result) == 1
        assert "Step 2: Add core module" in result

    def test_all_complete_returns_empty(self, tmp_path: object) -> None:
        """Test with all tasks complete returns empty list."""
        tracker_content = _read_fixture("all_complete.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        result = get_incomplete_tasks(folder)
        assert result == []

    def test_exclude_meta_tasks(self, tmp_path: object) -> None:
        """Test excluding meta tasks (step-level entries)."""
        tracker_content = _read_fixture("with_subtasks.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        result = get_incomplete_tasks(folder, exclude_meta_tasks=True)
        # Should exclude "Step 1: ..." meta task, only return sub-tasks
        assert all(not name.startswith("Step ") for name in result)

    def test_file_not_found(self, tmp_path: object) -> None:
        """Test with missing tracker file."""
        with pytest.raises(TaskTrackerFileNotFoundError):
            get_incomplete_tasks(str(tmp_path))


class TestHasIncompleteWork:
    """Tests for has_incomplete_work function."""

    def test_has_incomplete(self, tmp_path: object) -> None:
        tracker_content = _read_fixture("all_incomplete.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        assert has_incomplete_work(folder) is True

    def test_all_complete(self, tmp_path: object) -> None:
        tracker_content = _read_fixture("all_complete.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        assert has_incomplete_work(folder) is False


class TestGetTaskCounts:
    """Tests for get_task_counts function."""

    def test_all_complete(self, tmp_path: object) -> None:
        tracker_content = _read_fixture("all_complete.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        total, completed = get_task_counts(folder)
        assert total == 3
        assert completed == 3

    def test_all_incomplete(self, tmp_path: object) -> None:
        tracker_content = _read_fixture("all_incomplete.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        total, completed = get_task_counts(folder)
        assert total == 3
        assert completed == 0

    def test_mixed_status(self, tmp_path: object) -> None:
        tracker_content = _read_fixture("mixed_status.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        total, completed = get_task_counts(folder)
        assert total == 3
        assert completed == 2

    def test_with_subtasks(self, tmp_path: object) -> None:
        tracker_content = _read_fixture("with_subtasks.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        total, completed = get_task_counts(folder)
        # 2 steps + 5 sub-tasks in step 1 + 3 sub-tasks in step 2 = 10
        assert total == 10
        assert completed == 7  # 1 step + 3 sub (step1) + 3 sub (step2)


class TestGetStepProgress:
    """Tests for get_step_progress function."""

    def test_with_subtasks(self, tmp_path: object) -> None:
        tracker_content = _read_fixture("with_subtasks.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        progress = get_step_progress(folder)
        assert "Step 1: Create Package Structure" in progress
        step1 = progress["Step 1: Create Package Structure"]
        assert step1["total"] == 5
        assert step1["completed"] == 3
        assert step1["incomplete"] == 2
        incomplete_list = step1["incomplete_tasks"]
        assert isinstance(incomplete_list, list)
        assert "Add type hints" in incomplete_list
        assert "Add docstrings" in incomplete_list

    def test_step_with_all_subtasks_complete(self, tmp_path: object) -> None:
        tracker_content = _read_fixture("with_subtasks.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        progress = get_step_progress(folder)
        step2 = progress["Step 2: Add Core Module"]
        assert step2["total"] == 3
        assert step2["completed"] == 3
        assert step2["incomplete"] == 0
        assert step2["incomplete_tasks"] == []

    def test_no_subtasks(self, tmp_path: object) -> None:
        tracker_content = _read_fixture("all_incomplete.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        progress = get_step_progress(folder)
        # Each step has no sub-tasks, so counts itself
        for step_data in progress.values():
            assert step_data["total"] == 1


class TestValidateTaskTracker:
    """Tests for validate_task_tracker function."""

    def test_valid_tracker(self, tmp_path: object) -> None:
        tracker_content = _read_fixture("mixed_status.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        # Should not raise
        validate_task_tracker(folder)

    def test_missing_file(self, tmp_path: object) -> None:
        with pytest.raises(TaskTrackerFileNotFoundError):
            validate_task_tracker(str(tmp_path))

    def test_missing_tasks_section(self, tmp_path: object) -> None:
        tracker_content = _read_fixture("no_tasks_section.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        with pytest.raises(TaskTrackerSectionNotFoundError):
            validate_task_tracker(folder)


class TestIsTaskDone:
    """Tests for is_task_done function."""

    def test_complete_task(self, tmp_path: object) -> None:
        tracker_content = _read_fixture("mixed_status.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        assert is_task_done("Step 1: Create package structure", folder) is True

    def test_incomplete_task(self, tmp_path: object) -> None:
        tracker_content = _read_fixture("mixed_status.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        assert is_task_done("Step 2: Add core module", folder) is False

    def test_task_not_found(self, tmp_path: object) -> None:
        tracker_content = _read_fixture("mixed_status.md")
        folder = str(tmp_path)
        _write_tracker(folder, tracker_content)
        with pytest.raises(TaskTrackerError, match="Task not found"):
            is_task_done("Nonexistent task", folder)


class TestTaskTrackerTemplate:
    """Tests for the TASK_TRACKER_TEMPLATE constant."""

    def test_template_contains_required_sections(self) -> None:
        assert "## Tasks" in TASK_TRACKER_TEMPLATE
        assert "## Instructions for LLM" in TASK_TRACKER_TEMPLATE
        assert "- [ ]" in TASK_TRACKER_TEMPLATE

    def test_template_is_valid(self, tmp_path: object) -> None:
        """Template should parse without errors."""
        folder = str(tmp_path)
        _write_tracker(folder, TASK_TRACKER_TEMPLATE)
        validate_task_tracker(folder)


# --- Test helpers ---


def _read_fixture(filename: str) -> str:
    """Read a test data fixture file."""
    filepath = os.path.join(TEST_DATA_DIR, filename)
    with open(filepath, encoding="utf-8") as f:
        return f.read()


def _write_tracker(folder: str, content: str) -> None:
    """Write a TASK_TRACKER.md file to a folder."""
    filepath = os.path.join(folder, "TASK_TRACKER.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
