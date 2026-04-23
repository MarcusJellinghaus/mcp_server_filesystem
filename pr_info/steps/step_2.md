# Step 2: Refactor existing reference tools to use helper

> **Context**: See `pr_info/steps/summary.md` for the full plan.
> This step replaces the inlined lookup+ensure pattern in 3 existing tools with the helper from Step 1.

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 2.

Refactor `read_reference_file`, `list_reference_directory`, and `search_reference_files`
in `server_reference_tools.py` to use `get_reference_project_path()` instead of inlining
the lookup+ensure_available pattern. This is a pure DRY refactor — no behavior change.
Existing tests in test_reference_projects_mcp_tools.py must continue to pass unchanged.
```

## WHERE

- **Source file**: `src/mcp_workspace/server_reference_tools.py` — modify 3 existing async functions

## WHAT

Replace this repeated 4-line pattern in each function:

```python
# BEFORE (repeated in 3 tools)
if reference_name not in _reference_projects:
    raise ValueError(f"Reference project '{reference_name}' not found")
project = _reference_projects[reference_name]
await ensure_available(project)
ref_path = project.path
```

With:

```python
# AFTER (one line)
ref_path = await get_reference_project_path(reference_name)
```

## HOW

- `get_reference_project_path` is in the same module — no new imports needed
- Remove the now-unused per-function validation/lookup code
- Remove per-function debug logging about reference project path (the helper handles the resolution)
- Keep all other function logic unchanged

## FUNCTIONS AFFECTED

1. `read_reference_file()` — replace lines doing lookup+ensure+path with helper call
2. `list_reference_directory()` — same replacement
3. `search_reference_files()` — same replacement

## TESTS

No new tests. Existing tests in `TestReferenceProjectMCPTools` and `TestSearchReferenceFiles` validate behavior is preserved. Run full test suite to confirm.

## COMMIT

```
refactor(ref): use get_reference_project_path in existing tools

Replace inlined lookup+ensure_available pattern with shared helper
in read_reference_file, list_reference_directory, and
search_reference_files. Pure DRY refactor — no behavior change.

Refs #140
```
