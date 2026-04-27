"""Unit tests for async polling primitives in branch_status.

Tests `_wait_for_ci` and `_wait_for_pr` private helpers. `asyncio.sleep`
is patched with `AsyncMock` so tests run instantly.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_workspace.checks.branch_status import _wait_for_ci, _wait_for_pr


@pytest.fixture
def project_dir() -> Path:
    """Dummy project directory path."""
    return Path("/tmp/fake-project")


class TestWaitForCI:
    """Tests for `_wait_for_ci`."""

    @pytest.mark.asyncio
    async def test_returns_immediately_on_success(self, project_dir: Path) -> None:
        ci_manager = MagicMock()
        ci_manager.get_latest_ci_status.return_value = {
            "run": {"conclusion": "success"}
        }
        with patch(
            "mcp_workspace.checks.branch_status.CIResultsManager",
            return_value=ci_manager,
        ), patch(
            "mcp_workspace.checks.branch_status.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep:
            await _wait_for_ci(project_dir, "feature/x", timeout=60)
        assert ci_manager.get_latest_ci_status.call_count == 1
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_immediately_on_failure(self, project_dir: Path) -> None:
        ci_manager = MagicMock()
        ci_manager.get_latest_ci_status.return_value = {
            "run": {"conclusion": "failure"}
        }
        with patch(
            "mcp_workspace.checks.branch_status.CIResultsManager",
            return_value=ci_manager,
        ), patch(
            "mcp_workspace.checks.branch_status.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            await _wait_for_ci(project_dir, "feature/x", timeout=60)
        assert ci_manager.get_latest_ci_status.call_count == 1

    @pytest.mark.asyncio
    async def test_returns_after_timeout_when_in_progress(
        self, project_dir: Path
    ) -> None:
        ci_manager = MagicMock()
        ci_manager.get_latest_ci_status.return_value = {
            "run": {"conclusion": None, "status": "in_progress"}
        }
        # Simulate time advancing inside the loop via monotonic side_effect.
        # Sequence: deadline calc, then 3 loop iterations, then exceed.
        times = iter([0.0, 0.0, 5.0, 10.0, 100.0])
        with patch(
            "mcp_workspace.checks.branch_status.CIResultsManager",
            return_value=ci_manager,
        ), patch(
            "mcp_workspace.checks.branch_status.asyncio.sleep",
            new_callable=AsyncMock,
        ), patch(
            "mcp_workspace.checks.branch_status.time.monotonic",
            side_effect=lambda: next(times),
        ):
            await _wait_for_ci(project_dir, "feature/x", timeout=60)
        assert ci_manager.get_latest_ci_status.call_count >= 1

    @pytest.mark.asyncio
    async def test_tolerates_two_errors_then_succeeds(
        self, project_dir: Path
    ) -> None:
        ci_manager = MagicMock()
        ci_manager.get_latest_ci_status.side_effect = [
            RuntimeError("boom1"),
            RuntimeError("boom2"),
            {"run": {"conclusion": "success"}},
        ]
        with patch(
            "mcp_workspace.checks.branch_status.CIResultsManager",
            return_value=ci_manager,
        ), patch(
            "mcp_workspace.checks.branch_status.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            await _wait_for_ci(project_dir, "feature/x", timeout=600)
        assert ci_manager.get_latest_ci_status.call_count == 3

    @pytest.mark.asyncio
    async def test_aborts_after_three_consecutive_errors(
        self, project_dir: Path
    ) -> None:
        ci_manager = MagicMock()
        ci_manager.get_latest_ci_status.side_effect = RuntimeError("boom")
        with patch(
            "mcp_workspace.checks.branch_status.CIResultsManager",
            return_value=ci_manager,
        ), patch(
            "mcp_workspace.checks.branch_status.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            await _wait_for_ci(project_dir, "feature/x", timeout=600)
        assert ci_manager.get_latest_ci_status.call_count == 3

    @pytest.mark.asyncio
    async def test_timeout_zero_returns_immediately(
        self, project_dir: Path
    ) -> None:
        ci_manager = MagicMock()
        with patch(
            "mcp_workspace.checks.branch_status.CIResultsManager",
            return_value=ci_manager,
        ), patch(
            "mcp_workspace.checks.branch_status.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep:
            await _wait_for_ci(project_dir, "feature/x", timeout=0)
        assert ci_manager.get_latest_ci_status.call_count == 0
        mock_sleep.assert_not_called()


class TestWaitForPR:
    """Tests for `_wait_for_pr`."""

    @pytest.mark.asyncio
    async def test_returns_immediately_when_pr_found(
        self, project_dir: Path
    ) -> None:
        pr_manager = MagicMock()
        pr_manager.find_pull_request_by_head.return_value = [{"number": 42}]
        with patch(
            "mcp_workspace.checks.branch_status.PullRequestManager",
            return_value=pr_manager,
        ), patch(
            "mcp_workspace.checks.branch_status.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep:
            await _wait_for_pr(project_dir, "feature/x", timeout=60)
        assert pr_manager.find_pull_request_by_head.call_count == 1
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_after_timeout_when_no_pr(
        self, project_dir: Path
    ) -> None:
        pr_manager = MagicMock()
        pr_manager.find_pull_request_by_head.return_value = []
        times = iter([0.0, 0.0, 5.0, 10.0, 100.0])
        with patch(
            "mcp_workspace.checks.branch_status.PullRequestManager",
            return_value=pr_manager,
        ), patch(
            "mcp_workspace.checks.branch_status.asyncio.sleep",
            new_callable=AsyncMock,
        ), patch(
            "mcp_workspace.checks.branch_status.time.monotonic",
            side_effect=lambda: next(times),
        ):
            await _wait_for_pr(project_dir, "feature/x", timeout=60)
        assert pr_manager.find_pull_request_by_head.call_count >= 1

    @pytest.mark.asyncio
    async def test_aborts_after_three_consecutive_errors(
        self, project_dir: Path
    ) -> None:
        pr_manager = MagicMock()
        pr_manager.find_pull_request_by_head.side_effect = RuntimeError("boom")
        with patch(
            "mcp_workspace.checks.branch_status.PullRequestManager",
            return_value=pr_manager,
        ), patch(
            "mcp_workspace.checks.branch_status.asyncio.sleep",
            new_callable=AsyncMock,
        ):
            await _wait_for_pr(project_dir, "feature/x", timeout=600)
        assert pr_manager.find_pull_request_by_head.call_count == 3

    @pytest.mark.asyncio
    async def test_timeout_zero_returns_immediately(
        self, project_dir: Path
    ) -> None:
        pr_manager = MagicMock()
        with patch(
            "mcp_workspace.checks.branch_status.PullRequestManager",
            return_value=pr_manager,
        ), patch(
            "mcp_workspace.checks.branch_status.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep:
            await _wait_for_pr(project_dir, "feature/x", timeout=0)
        assert pr_manager.find_pull_request_by_head.call_count == 0
        mock_sleep.assert_not_called()
