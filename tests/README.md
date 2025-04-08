# Testing Structure

This directory contains tests for the project. The test structure is designed to mirror the source code structure:

## Directory Structure

```
tests/
├── file_tools/             # Tests for src/file_tools package
│   ├── test_directory_utils.py   # Tests for directory_utils.py
│   ├── test_edit_file_api.py     # Tests for edit_file API
│   ├── test_edit_file_issues.py  # Tests for edit_file issues
│   ├── test_edit_file.py         # Tests for edit_file functionality
│   ├── test_file_operations.py   # Tests for file_operations.py
│   ├── test_markdown_indentation.py # Tests for markdown indentation
│   └── test_path_utils.py        # Tests for path_utils.py
├── test_file_tools/        # Test files for edit_file API tests
│   └── indentation_test.py       # Test file for indentation tests
├── testdata/               # Test data directory
│   └── tests/                    # Nested test data
│       └── testdata/             # Further nested test data
│           └── test_file_tools/  # Test files for various tests
├── test_log_utils.py       # Tests for log_utils.py
├── test_server.py          # Tests for server.py
└── conftest.py             # Test configuration and fixtures
```

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
