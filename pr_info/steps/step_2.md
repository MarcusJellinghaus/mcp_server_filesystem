# Step 2: Server Storage (TDD)

## Objective
Write tests for and implement global storage for reference projects and initialization function in the server module.

## WHERE
- **Test File**: `tests/test_reference_projects.py` (add server storage test class)
- **Implementation File**: `src/mcp_server_filesystem/server.py`
- **Module-level**: Add `_reference_projects` global variable
- **Functions**: `set_reference_projects()`, `run_server()` (updated signature)

## WHAT

### Phase 1: Write Tests First (TDD Red)
```python
# tests/test_reference_projects.py
class TestReferenceProjectServerStorage:
    """Test server storage and initialization."""
    
    def test_set_reference_projects(self):
        """Test setting reference projects storage."""
        
    def test_run_server_with_reference_projects(self):
        """Test run_server accepts reference projects parameter."""
        
    def test_reference_projects_logging(self):
        """Test INFO level logging during initialization."""
```

### Phase 2: Implement to Pass Tests (TDD Green)
```python
# src/mcp_server_filesystem/server.py

# New module-level storage
_reference_projects: Dict[str, Path] = {}

# New function
def set_reference_projects(reference_projects: Dict[str, Path]) -> None:
    """Set the reference projects for file operations."""
    pass

# Modified function signature
def run_server(project_dir: Path, reference_projects: Dict[str, Path] = None) -> None:
    """Run the MCP server with project directory and optional reference projects."""
    pass
```

## HOW (TDD Process)

### Phase 1: Write Tests (Red)
- Add `TestReferenceProjectServerStorage` class to `tests/test_reference_projects.py`
- Write 3 focused tests for storage, server initialization, and logging
- Follow exact patterns from existing `tests/test_server.py`
- Tests should initially fail (red state)

### Phase 2: Implement (Green)
- Add global `_reference_projects` variable similar to existing `_project_dir`
- Follow same pattern as `set_project_dir()` for reference project initialization
- Update `run_server()` to accept optional reference projects parameter
- Add INFO level logging for reference project initialization with context

### Phase 3: Refactor
- Clean up implementation while keeping tests green
- Ensure consistency with existing `server.py` patterns

## ALGORITHM
```
1. Initialize global _reference_projects as empty dict
2. In set_reference_projects():
   - Store reference_projects globally (already absolute paths)
   - Log each reference project name and path with context
3. In run_server():
   - Call set_project_dir() (existing)
   - IF reference_projects provided: call set_reference_projects()
   - Call mcp.run() (existing)
```

## DATA
**Input**: `Dict[str, Path]` - mapping of project names to directory paths  
**Storage**: `_reference_projects: Dict[str, Path]` - global module variable  
**Logging**: INFO level messages with reference project context for debugging

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and completing Step 1, implement Step 2: Add reference project storage to server.

In src/mcp_server_filesystem/server.py, add global storage for reference projects following the same pattern as the existing _project_dir variable. Create set_reference_projects() function and update run_server() to accept reference projects.

Use INFO level logging with reference project context. Follow exact patterns from existing code and maintain backward compatibility. The run_server() signature should have reference_projects as an optional parameter with default None.
```
