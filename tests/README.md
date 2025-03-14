# Testing Structure

This directory contains tests for the project. The test structure is designed to mirror the source code structure:

## Directory Structure

```
tests/
├── file_tools/             # Tests for src/file_tools package
│   ├── test_directory_utils.py   # Tests for directory_utils.py
│   ├── test_file_operations.py   # Tests for file_operations.py
│   ├── test_init.py              # Tests for package initialization
│   └── test_path_utils.py        # Tests for path_utils.py
├── test_server.py          # Tests for server.py
└── conftest.py             # Test configuration and fixtures
```

## Deprecated Files

The following files in the root tests directory are deprecated and exist only for backward compatibility:

```
tests/test_directory_utils.py  -> moved to tests/file_tools/test_directory_utils.py
tests/test_file_operations.py  -> moved to tests/file_tools/test_file_operations.py
tests/test_file_tools.py       -> moved to tests/file_tools/test_init.py
tests/test_path_utils.py       -> moved to tests/file_tools/test_path_utils.py
```

These files contain deprecation notices and will be removed in a future update.

## Testing Philosophy

1. Tests should mirror the structure of the source code they test.
2. Each test file should test a single module or component.
3. Tests should use direct imports from the modules they test.
4. Common test configuration and fixtures are kept in conftest.py.

## Running Tests

Run all tests with:

```
pytest
```

Run tests for a specific module:

```
pytest tests/file_tools/test_file_operations.py
```

Run a specific test:

```
pytest tests/file_tools/test_file_operations.py::test_write_file
```
