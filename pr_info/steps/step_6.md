# Step 6: CLI to Server Integration (TDD)

## Objective
Write tests for and implement the integration between CLI argument parsing and server initialization.

## WHERE
- **Test File**: `tests/test_reference_projects.py` (add integration test class)
- **Implementation File**: `src/mcp_server_filesystem/main.py`
- **Function**: `main()` - update server call
- **Import**: Update import statement for `run_server`

## WHAT

### Phase 1: Write Tests First (TDD Red)
```python
# tests/test_reference_projects.py
class TestReferenceProjectIntegration:
    """Test CLI to server integration."""
    
    def test_main_with_reference_projects(self):
        """Test main() passes reference projects to run_server()."""
        
    def test_main_without_reference_projects(self):
        """Test main() works without reference projects (backward compatibility)."""
        
    def test_main_with_auto_rename(self):
        """Test main() handles duplicate names with auto-rename."""
```

### Phase 2: Implement to Pass Tests (TDD Green)
```python
# src/mcp_server_filesystem/main.py

# Modified main() function call
def main() -> None:
    """Main entry point with reference project support."""
    # ... existing code ...
    
    # New: Parse reference projects
    reference_projects = {}
    if args.reference_project:
        reference_projects = validate_reference_projects(args.reference_project)
    
    # Updated: Pass reference projects to server
    run_server(project_dir, reference_projects)
```

## HOW (TDD Process)

### Phase 1: Write Tests (Red)
- Add `TestReferenceProjectIntegration` class to `tests/test_reference_projects.py`
- Write 3 focused tests for integration scenarios
- Mock `run_server()` to verify correct parameters are passed
- Follow exact patterns from existing `tests/test_server.py`
- Tests should initially fail (red state)

### Phase 2: Implement (Green)
- Use validation function from Step 1 to parse reference project arguments (with auto-rename for duplicates)
- Handle case where no reference projects are provided (empty dict)
- Pass parsed reference projects to `run_server()` call
- Maintain all existing functionality and error handling exactly

### Phase 3: Refactor
- Clean up implementation while keeping tests green
- Ensure code follows existing patterns in `main.py`

## ALGORITHM
```
1. Parse CLI arguments (existing functionality)
2. Validate project directory (existing functionality)
3. IF --reference-project args provided:
   - Call validate_reference_projects() from Step 1 (with auto-rename)
   - Store result in reference_projects variable
4. ELSE: reference_projects = {} (empty dict)
5. Call run_server(project_dir, reference_projects)
```

## DATA
**Input**: CLI args with optional `--reference-project` arguments  
**Processing**: `validate_reference_projects()` returns `Dict[str, Path]` with auto-rename  
**Output**: Pass dict to `run_server()` (empty dict if no reference projects)  
**Backward Compatibility**: Works with existing CLI usage (no breaking changes)

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and completing Steps 1-5, implement Step 6 using TDD approach: CLI to server integration.

Phase 1 - Write Tests First:
Add TestReferenceProjectIntegration class to tests/test_reference_projects.py. Write 3 focused tests covering: main() with reference projects, without reference projects (backward compatibility), and auto-rename handling. Mock run_server() to verify correct parameters. Follow exact patterns from tests/test_server.py. Tests should initially fail.

Phase 2 - Implement to Pass Tests:
Update main() function in src/mcp_server_filesystem/main.py to parse reference project arguments using validate_reference_projects() from Step 1 (with auto-rename logic), then pass result to run_server(). Handle case where no reference projects provided (empty dict). Maintain backward compatibility.

Phase 3 - Refactor:
Clean up implementation while keeping tests green. Ensure consistency with existing main.py patterns.
```
