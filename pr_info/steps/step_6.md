# Step 6: Connect CLI to Server Integration

## Objective
Wire up the CLI argument parsing to pass reference projects to the server initialization.

## WHERE
- **File**: `src/mcp_server_filesystem/main.py`
- **Function**: `main()` - update server call
- **Import**: Update import statement for `run_server`

## WHAT
```python
# Modified import (no signature change needed)
from mcp_server_filesystem.server import run_server

# Updated main() function call
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

## HOW
- Use validation function from Step 1 to parse reference project arguments
- Handle case where no reference projects are provided (empty dict)
- Pass parsed reference projects to `run_server()` call
- Maintain all existing functionality and error handling

## ALGORITHM
```
1. Parse CLI arguments (existing functionality)
2. Validate project directory (existing functionality)
3. IF --reference-project args provided:
   - Call validate_reference_projects() from Step 1
   - Store result in reference_projects variable
4. ELSE: reference_projects = {} (empty dict)
5. Call run_server(project_dir, reference_projects)
```

## DATA
**Input**: CLI args with optional `--reference-project` arguments  
**Processing**: `validate_reference_projects()` returns `Dict[str, Path]`  
**Output**: Pass dict to `run_server()` (empty dict if no reference projects)  
**Backward Compatibility**: Works with existing CLI usage (no breaking changes)

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and completing Steps 1-5, implement Step 6: Connect CLI parsing to server integration.

In src/mcp_server_filesystem/main.py, update the main() function to parse reference project arguments using the validate_reference_projects() function from Step 1, then pass the result to run_server().

Handle the case where no reference projects are provided (pass empty dict). Maintain backward compatibility - existing usage should work unchanged.
```
