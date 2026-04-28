"""Tests for ``mcp_workspace._ssl.ensure_truststore()``."""

import importlib
import logging
import sys
import types
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_workspace import _ssl


@pytest.fixture(autouse=True)
def reset_activated_flag() -> Generator[None, None, None]:
    """Reset the module-level ``_activated`` flag before and after each test."""
    _ssl._activated = False
    yield
    _ssl._activated = False


@pytest.fixture
def stub_truststore() -> Generator[MagicMock, None, None]:
    """Install a stub ``truststore`` module exposing a mock ``inject_into_ssl``."""
    original = sys.modules.get("truststore")
    stub = types.ModuleType("truststore")
    inject_mock = MagicMock(name="inject_into_ssl")
    stub.inject_into_ssl = inject_mock  # type: ignore[attr-defined]
    sys.modules["truststore"] = stub
    try:
        yield inject_mock
    finally:
        if original is None:
            sys.modules.pop("truststore", None)
        else:
            sys.modules["truststore"] = original


def test_idempotent_calls_inject_once(stub_truststore: MagicMock) -> None:
    """Calling ``ensure_truststore()`` multiple times invokes inject only once."""
    _ssl.ensure_truststore()
    _ssl.ensure_truststore()
    _ssl.ensure_truststore()

    assert stub_truststore.call_count == 1
    assert _ssl._activated is True


def test_no_op_when_truststore_unavailable(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """When ``truststore`` is not importable, function logs a warning and no-ops."""
    monkeypatch.setitem(sys.modules, "truststore", None)

    with caplog.at_level(logging.WARNING, logger="mcp_workspace._ssl"):
        _ssl.ensure_truststore()

    assert _ssl._activated is False
    assert any(
        "truststore not installed" in record.message for record in caplog.records
    )


def test_import_does_not_activate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-importing ``mcp_workspace._ssl`` must NOT activate truststore."""
    stub = types.ModuleType("truststore")
    inject_mock = MagicMock(name="inject_into_ssl")
    stub.inject_into_ssl = inject_mock  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "truststore", stub)

    reloaded = importlib.reload(_ssl)
    try:
        assert inject_mock.call_count == 0
        assert reloaded._activated is False
    finally:
        importlib.reload(_ssl)


def test_inject_failure_does_not_raise(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """If ``inject_into_ssl()`` raises, the exception is swallowed and logged."""
    stub = types.ModuleType("truststore")

    def boom() -> None:
        raise RuntimeError("nope")

    stub.inject_into_ssl = boom  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "truststore", stub)

    with caplog.at_level(logging.WARNING, logger="mcp_workspace._ssl"):
        _ssl.ensure_truststore()

    assert _ssl._activated is False
    assert any(
        "truststore.inject_into_ssl() failed" in record.message
        and "nope" in record.message
        for record in caplog.records
    )
