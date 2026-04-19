# Step 4: `main.py` — New KV CLI Parser + URL Verification

## LLM Prompt

> Implement Step 4 of Issue #92. See `pr_info/steps/summary.md` for full context.
> Rewrite `validate_reference_projects()` in `main.py` for the new KV CLI format and add URL verification at startup. TDD — update existing tests first, then modify implementation.
> Run all code quality checks (pylint, pytest, mypy) after changes. Commit: `feat(cli): switch to KV reference project format with URL verification`

## WHERE

- **Tests:** `tests/test_reference_projects.py` — update `TestReferenceProjectCLI` and `TestReferenceProjectIntegration`
- **Implementation:** `src/mcp_workspace/main.py` — rewrite `validate_reference_projects()`

## WHAT

### Updated `validate_reference_projects()`

```python
def validate_reference_projects(
    reference_args: List[str], project_dir: Path
) -> Dict[str, ReferenceProject]:
```

Parse comma-separated KV pairs: `name=proj,path=/dir,url=https://...`

```
def validate_reference_projects(reference_args, project_dir):
    for arg in reference_args:
        parse comma-separated key=value pairs into dict
        validate "name" and "path" are present
        if url provided AND path exists AND is_git_repository(path):
            detected = get_remote_url(path)
            if detected: verify_url_match(url, detected, name)  # fatal on mismatch
        elif url not provided AND path exists AND is_git_repository(path):
            auto_url = get_remote_url(path)  # store if detected, None otherwise
        if path doesn't exist AND url is None:
            warn and skip (path required without URL)
        if path doesn't exist AND url is set:
            allow (will be cloned lazily)
        # existing overlap/duplicate checks remain
        build ReferenceProject(name, path, url)
    return validated dict
```

### Updated CLI help text

```python
parser.add_argument(
    "--reference-project",
    action="append",
    help="Reference project as key-value pairs: name=myproj,path=/path/to/dir,url=https://... (name and path required, url optional)",
)
```

## HOW

- Import `ReferenceProject` from `mcp_workspace.reference_projects`
- Import `get_remote_url` from `mcp_workspace.git_operations.remotes`
- Import `verify_url_match` from `mcp_workspace.reference_projects`
- KV parsing: `dict(pair.split("=", 1) for pair in arg.split(","))` — split on comma first, then on first `=` per pair
- Path existence check relaxed when `url` is provided
- URL mismatch raises `SystemExit` (fatal — server refuses to start)

## ALGORITHM (KV parsing)

```
1. Split arg on "," → list of "key=value" strings
2. Split each on first "=" → dict of key→value
3. Check "name" in dict → warn + skip if missing
4. Check "path" in dict → warn + skip if missing
5. Resolve path, apply overlap/duplicate checks
6. Handle URL verification and auto-detection
7. Create ReferenceProject(name, path, url)
```

## DATA

```python
# Input:  "name=p_coder,path=/home/user/mcp_coder,url=https://github.com/org/repo"
# Output: {"p_coder": ReferenceProject(name="p_coder", path=Path("/home/user/mcp_coder"), url="https://github.com/org/repo")}

# Input:  "name=p_tools,path=/home/user/tools"
# Output: {"p_tools": ReferenceProject(name="p_tools", path=Path("/home/user/tools"), url=<auto-detected or None>)}
```

## TESTS

Update existing test classes in `tests/test_reference_projects.py`:

### `TestReferenceProjectCLI` (update existing tests)
- `test_parse_single_reference_project` — update CLI arg to new KV format
- `test_parse_multiple_reference_projects` — update to KV format
- `test_auto_rename_duplicates` — update arg format, assert `ReferenceProject` in result
- `test_invalid_format_warnings` — test missing `name` key, missing `path` key
- `test_path_normalization` — update format, check `ReferenceProject.path`
- `test_overlap_detection` — update format, check `ReferenceProject` in result
- `test_nonexistent_path_warning` — test skip when no URL, allow when URL set

### New tests in `TestReferenceProjectCLI`
- `test_url_auto_detected_from_git` — path is git repo → URL auto-populated (mock `get_remote_url`)
- `test_url_verification_passes` — explicit URL matches detected → no error (mock both)
- `test_url_mismatch_fatal` — explicit URL differs from detected → `SystemExit` / `ValueError`
- `test_path_missing_with_url_allowed` — path doesn't exist but URL set → accepted
- `test_path_missing_without_url_skipped` — path doesn't exist, no URL → warning + skip

### `TestReferenceProjectIntegration` (update existing tests)
- Update all test args to new KV format
- Update assertions to check for `ReferenceProject` instances
