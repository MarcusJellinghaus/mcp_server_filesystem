# Step 7: Add Test Coverage for Reference Projects

## Objective
Create comprehensive test coverage for the new reference project functionality using TDD principles.

## WHERE
- **File**: `tests/test_reference_projects.py` (new file)
- **Test Categories**: CLI parsing, server integration, MCP tools
- **Framework**: pytest with existing test patterns

## WHAT
```python
# Test classes to create
class TestReferenceProjectCLI:
    """Test CLI argument parsing and validation."""
    
class TestReferenceProjectServer:
    """Test server initialization and storage."""
    
class TestReferenceProjectTools:
    """Test MCP tools: get_reference_projects, list_reference_directory, read_reference_file."""
```

## HOW
- Follow existing test patterns in `tests/test_server.py`
- Use pytest fixtures for temporary directories and test data
- Test both success cases and error conditions
- Mock file system operations where appropriate
- Test CLI parsing with various argument combinations

## ALGORITHM
```
1. Create test fixtures (temp directories, sample reference projects)
2. Test CLI parsing: valid args, invalid formats, duplicate names, path normalization
3. Test validation: startup warnings for invalid references, continuing with valid ones
4. Test server integration: initialization, storage, logging with context
5. Test MCP tools: discovery, listing, reading, error cases with existing error patterns
6. Test security: path traversal prevention, directory containment
7. Test edge cases: empty projects, missing directories, relative/absolute paths
```

## DATA
**Test Fixtures**: Temporary directories with sample files  
**Test Cases**: Valid/invalid CLI args, reference project operations  
**Coverage**: All new functions and error paths  
**Integration**: Verify end-to-end CLI to MCP tool functionality

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and completing Steps 1-6, implement Step 7: Add comprehensive test coverage for reference projects.

Create tests/test_reference_projects.py with test classes for CLI parsing, server integration, and MCP tools. Follow existing test patterns from tests/test_server.py.

Test both success and error cases, including path normalization, startup validation with warnings, security (path traversal), and edge cases. Test that error handling reuses existing patterns. Use pytest fixtures for temporary directories and ensure tests are isolated and repeatable.
```
