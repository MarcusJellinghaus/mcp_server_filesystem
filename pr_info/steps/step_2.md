# Step 2: Implement Overlap Filtering in Production Code

> **Context**: See `pr_info/steps/summary.md` for full issue summary.
> Step 1 (tests) must be completed first. This step makes the tests pass.

## WHERE

- `src/mcp_workspace/main.py`

## WHAT

### 2a. Update `main()` — switch to `.resolve()`

**Line ~136**, change:
```python
project_dir = project_dir.absolute()
```
to:
```python
project_dir = project_dir.resolve()
```

### 2b. Update `validate_reference_projects()` — add `project_dir` parameter

**Function signature** changes from:
```python
def validate_reference_projects(reference_args: List[str]) -> Dict[str, Path]:
```
to:
```python
def validate_reference_projects(reference_args: List[str], project_dir: Path) -> Dict[str, Path]:
```

### 2c. Switch reference path resolution to `.resolve()`

**Inside `validate_reference_projects()`**, change:
```python
project_path = Path(path_str).absolute()
```
to:
```python
project_path = Path(path_str).resolve()
```

### 2d. Add overlap checks after existence/directory validation

After the `is_dir()` check and before the duplicate-name handling, add:

**Algorithm (pseudocode):**
```
resolved_project_dir = project_dir.resolve()
if project_path == resolved_project_dir:
    log warning "same directory"
    continue
elif project_path.is_relative_to(resolved_project_dir):
    log warning "subdirectory of the main project"
    continue
elif resolved_project_dir.is_relative_to(project_path):
    log warning "parent of the main project"
    continue
```

**Warning messages** (exact format from issue):
- `"Reference project '<name>' points to the same directory as the main project, ignoring: path=<path>"`
- `"Reference project '<name>' is a subdirectory of the main project, ignoring: path=<path>"`
- `"Reference project '<name>' is a parent of the main project, ignoring: path=<path>"`

### 2e. Update call site in `main()`

**Line ~148**, change:
```python
reference_projects = validate_reference_projects(args.reference_project)
```
to:
```python
reference_projects = validate_reference_projects(args.reference_project, project_dir)
```

## HOW

- `Path.is_relative_to()` is available in Python 3.11+ (project requires 3.11+)
- `project_dir` passed to `validate_reference_projects()` is already resolved in `main()`, but we call `.resolve()` on it again inside the function for safety (the function may be called from tests with unresolved paths)
- No new imports needed

## DATA

- Input: `reference_args: List[str]`, `project_dir: Path`
- Output: `Dict[str, Path]` — same as before, but overlapping entries are excluded
- Side effects: warning log messages for each filtered entry

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.
Implement Step 2: modify src/mcp_workspace/main.py to add overlap filtering.
- Change .absolute() → .resolve() in main() and validate_reference_projects()
- Add project_dir parameter to validate_reference_projects()
- Add overlap detection (same dir, subdirectory, parent) after existence checks
- Update the call site in main()
After editing, run all three code quality checks (pylint, mypy, pytest).
All tests from Step 1 should now pass.
```
