"""Test configuration and shared fixtures for file_tools tests."""

import os
import shutil
from collections.abc import Generator
from pathlib import Path

import pytest

# Python path is now configured via pytest configuration in pyproject.toml

# Set up the project directory for testing
PROJECT_DIR = Path(os.path.abspath(os.path.dirname(__file__)))

# Test constants
TEST_DIR = Path("testdata/test_file_tools")
TEST_FILE = TEST_DIR / "test_file.txt"
TEST_CONTENT = "This is test content."


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Fixture to provide an isolated project directory for each test.

    Uses pytest's tmp_path to ensure tests don't interfere with each other
    when running in parallel with -n auto.
    """
    # Copy reference test data (read-only files like indent_testing_data.txt)
    testdata_src = PROJECT_DIR / "testdata"
    if testdata_src.exists():
        shutil.copytree(testdata_src, tmp_path / "testdata")

    # Ensure test file tools directory exists
    (tmp_path / TEST_DIR).mkdir(parents=True, exist_ok=True)

    return tmp_path


@pytest.fixture(autouse=True)
def setup_and_cleanup() -> Generator[None, None, None]:
    """
    Fixture to set up and clean up test environment.

    Tests use isolated tmp_path directories via the project_dir fixture,
    so no shared-state cleanup is needed here.
    """
    yield
