# Step 1: Add `get_reference_project_path()` helper + tests

> **Context**: See `pr_info/steps/summary.md` for the full plan.
> This step adds the shared helper that encapsulates reference project resolution.

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 1.

Add an async helper `get_reference_project_path()` to `server_reference_tools.py` that
encapsulates the lookup + validation + ensure_available + return path sequence.
Write tests first (TDD), then implement the helper.
Do NOT modify `git()` or refactor existing tools — that's later steps.
```

## WHERE

- **Test file**: `tests/test_reference_projects_mcp_tools.py` — add new test class
- **Source file**: `src/mcp_workspace/server_reference_tools.py` — add helper function

## WHAT

```python
# server_reference_tools.py
async def get_reference_project_path(name: str) -> Path:
    """Resolve a reference project name to its local path, ensuring availability."""
```

## HOW

- Uses existing `_reference_projects` module-level dict (same module — no cross-module import of private state)
- Calls existing `ensure_available()` from `reference_projects.py` (already imported)
- Returns `project.path` after ensuring the project is cloned/available

## ALGORITHM

```
1. if name not in _reference_projects → raise ValueError
2. project = _reference_projects[name]
3. await ensure_available(project)
4. return project.path
```

## DATA

- **Input**: `name: str` — reference project identifier (e.g. `"p_coder-utils"`)
- **Output**: `Path` — absolute path to the reference project directory
- **Errors**: `ValueError` if project name not found; propagates `ValueError` from `ensure_available` on clone failure

## TESTS (add to `tests/test_reference_projects_mcp_tools.py`)

New class `TestGetReferenceProjectPath` with 3 tests:

1. `test_get_reference_project_path_success` — valid name returns correct `Path`, `ensure_available` awaited
2. `test_get_reference_project_path_not_found` — invalid name raises `ValueError`
3. `test_get_reference_project_path_ensure_failure_propagates` — `ensure_available` raises → propagates

## COMMIT

```
feat(ref): add get_reference_project_path helper

Encapsulates lookup + validation + ensure_available + return path
for reference project resolution. Will be used by git() and to
DRY up existing reference tools.

Refs #140
```
