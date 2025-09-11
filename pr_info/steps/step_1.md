# Step 1: Extend CLI Argument Parsing

## Objective
Add support for `--reference-project` CLI arguments with validation and parsing.

## WHERE
- **File**: `src/mcp_server_filesystem/main.py`
- **Function**: `parse_args()` - extend argument parser
- **Function**: `main()` - add validation logic

## WHAT
```python
# New argument in parse_args()
parser.add_argument(
    "--reference-project",
    action="append",
    help="Reference project in format name=/path/to/dir (can be repeated)"
)

# New validation function
def validate_reference_projects(reference_args: List[str]) -> Dict[str, Path]:
    """Parse and validate reference project arguments.
    
    Validates name format and path existence. Logs warnings for invalid
    references and continues with valid ones only.
    """
    pass

# Extended main() function signature remains the same
def main() -> None:
    """Main entry point with reference project support."""
    pass
```

## HOW
- Add argument to existing `argparse.ArgumentParser` in `parse_args()`
- Create helper function for parsing `name=/path` format
- Integrate validation into existing `main()` function flow
- Pass validated reference projects to server initialization

## ALGORITHM
```
1. Parse CLI args with new --reference-project option
2. FOR each reference_project_arg:
   - Split on '=' to get name and path
   - Validate name format (alphanumeric + underscore/hyphen)
   - Convert path to absolute path (same as main project)
   - Validate path exists and is directory
   - IF invalid: log warning and skip
3. Check for duplicate names
4. Return Dict[str, Path] mapping (only valid references)
5. Pass to server initialization
```

## DATA
**Input**: `List[str]` like `["proj1=/path/to/proj1", "proj2=/path/to/proj2"]`  
**Output**: `Dict[str, Path]` like `{"proj1": Path("/path/to/proj1"), "proj2": Path("/path/to/proj2")}`  
**Validation**: Name regex `^[a-zA-Z0-9_-]+$`, path converted to absolute and validated as existing directory  
**Error Handling**: Log warnings for invalid references, continue with valid ones

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md, implement Step 1: Extend CLI argument parsing for reference projects.

Add support for --reference-project CLI arguments in src/mcp_server_filesystem/main.py. The argument should accept format "name=/path/to/dir" and be repeatable. Create validation that ensures names are alphanumeric+underscore/hyphen only and paths exist as directories. Convert paths to absolute paths (same as main project). Names must be unique.

Log warnings for invalid references and continue with valid ones only. Follow the existing code patterns in main.py and maintain all current functionality.
```
