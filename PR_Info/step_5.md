# Step 5: Handle Edge Cases and Final Integration

## Objective
Ensure the move functionality handles all edge cases gracefully and complete the final integration.

## Implementation Tasks

### 1. Add Edge Case Tests
Add these edge case tests to `tests/file_tools/test_move_operations.py`:

```python
# Add to existing TestBasicMoveOperations class:

def test_move_symlinks(self, tmp_path):
    """Test moving symbolic links."""
    # Implementation

def test_move_large_directory(self, tmp_path):
    """Test moving directories with many files."""
    # Implementation

def test_move_with_special_characters(self, tmp_path):
    """Test filenames with special characters."""
    # Implementation

def test_destination_already_exists(self, tmp_path):
    """Test that moving to existing destination raises error."""
    # Implementation
```

### 2. Enhance Error Handling
The `@log_function_call` decorator already handles:
- Automatic logging of parameters and results
- Exception capturing and logging
- Timing information

No additional error handling needed.

## Success Criteria
- [ ] Symlinks handled correctly
- [ ] Large directories move successfully
- [ ] Special characters in filenames work
- [ ] Concurrent operations are safe
- [ ] All edge cases tested

## Final Integration Tasks

### Update Documentation
Ensure README.md includes:
- Clear description of move_file tool
- Simple usage example: `move_file("old_name.txt", "new_name.txt")`
- Note that it works within project directory only

### Verify MCP Integration
Test with Claude Desktop:
1. Update Claude Desktop configuration
2. Restart Claude Desktop
3. Test move operations through the interface

### Run Comprehensive Tests
```bash
# Run all tests
pytest tests/ -v

# Check test coverage
pytest tests/ --cov=mcp_server_filesystem --cov-report=term-missing

# Run linting
pylint src/mcp_server_filesystem

# Run type checking
mypy src/mcp_server_filesystem
```

## Notes
- This step focuses on robustness, edge cases, and final integration
- All errors should be clear and actionable
- Simple boolean return hides all complexity from the LLM
- Leverage existing error handling infrastructure
