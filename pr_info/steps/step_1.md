# Step 1: CLI Argument Parsing (TDD)

## Objective
Write tests for and implement `--reference-project` CLI arguments with validation and parsing using TDD approach.

## WHERE
- **Test File**: `tests/test_reference_projects.py` (create CLI test class)
- **Implementation File**: `src/mcp_server_filesystem/main.py`
- **Functions**: `parse_args()` - extend argument parser, `validate_reference_projects()` - validation logic

## WHAT

### Phase 1: Write Tests First (TDD Red)
```python
# tests/test_reference_projects.py
class TestReferenceProjectCLI:
    """Test CLI argument parsing and validation."""
    
    def test_parse_single_reference_project(self):
        """Test parsing single reference project argument."""
        
    def test_parse_multiple_reference_projects(self):
        """Test parsing multiple reference project arguments."""
        
    def test_auto_rename_duplicates(self):
        """Test auto-renaming duplicate project names."""
        
    def test_invalid_format_warnings(self):
        """Test warnings for invalid argument formats."""
        
    def test_path_normalization(self):
        """Test conversion to absolute paths."""
```

### Phase 2: Implement to Pass Tests (TDD Green)
```python
# src/mcp_server_filesystem/main.py

# New argument in parse_args()
parser.add_argument(
    "--reference-project",
    action="append",
    help="Reference project in format name=/path/to/dir (can be repeated)"
)

# New validation function
def validate_reference_projects(reference_args: List[str]) -> Dict[str, Path]:
    """Parse and validate reference project arguments.
    
    Validates name format (very permissive) and path existence. Logs warnings for invalid
    references and continues with valid ones only. Auto-renames duplicates.
    """
    pass
```

## HOW (TDD Process)

### Phase 1: Write Tests (Red)
- Create `tests/test_reference_projects.py` with `TestReferenceProjectCLI` class
- Write 5 focused tests covering essential CLI parsing functionality
- Follow exact patterns from existing `tests/test_server.py`
- Tests should initially fail (red state)

### Phase 2: Implement (Green)
- Add argument to existing `argparse.ArgumentParser` in `parse_args()`
- Create helper function for parsing `name=/path` format with auto-rename logic
- Implement validation that makes all tests pass
- Follow exact error message patterns from existing code

### Phase 3: Refactor
- Clean up implementation while keeping tests green
- Ensure code follows existing patterns in `main.py`

## ALGORITHM
```
1. Parse CLI args with new --reference-project option
2. FOR each reference_project_arg:
   - Split on '=' to get name and path (split on first '=' only)
   - Validate name format (any non-empty string)
   - Convert path to absolute path (same as main project)
   - Validate path exists and is directory
   - IF invalid: log warning and skip
3. Handle duplicate names with auto-rename (name_2, name_3, etc.)
4. Return Dict[str, Path] mapping (only valid references)
5. Pass to server initialization
```

## DATA
**Input**: `List[str]` like `["proj1=/path/to/proj1", "proj2=/path/to/proj2"]`  
**Output**: `Dict[str, Path]` like `{"proj1": Path("/path/to/proj1"), "proj2": Path("/path/to/proj2")}`  
**Validation**: Name must be non-empty string (very permissive), path converted to absolute and validated as existing directory  
**Error Handling**: Log warnings for invalid references, continue with valid ones

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md, implement Step 1 using TDD approach: CLI argument parsing for reference projects.

Phase 1 - Write Tests First:
Create tests/test_reference_projects.py with TestReferenceProjectCLI class. Write 5 focused tests covering: single/multiple reference projects, auto-rename duplicates, invalid format warnings, and path normalization. Follow exact patterns from tests/test_server.py. Tests should initially fail.

Phase 2 - Implement to Pass Tests:
Add --reference-project CLI argument to src/mcp_server_filesystem/main.py. Format: "name=/path/to/dir" (repeatable). Create validate_reference_projects() function with auto-rename logic for duplicates. Use very permissive name validation, convert paths to absolute, log warnings for invalid references. Follow exact error message patterns from existing code.

Phase 3 - Refactor:
Clean up implementation while keeping tests green. Ensure consistency with existing main.py patterns.
```
