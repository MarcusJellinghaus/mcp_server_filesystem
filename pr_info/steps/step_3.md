# Step 3: Add `reference_name` to `git()` + tests

> **Context**: See `pr_info/steps/summary.md` for the full plan.
> This is the main feature step — making the `git()` MCP tool work with reference projects.

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 3.

Modify the `git()` tool in `server.py` to accept an optional `reference_name` parameter.
When set, resolve the reference project path via `get_reference_project_path()` and use it
as `project_dir` for `git_impl`. Make `git()` async, drop `@log_function_call`, wrap
`git_impl` in `asyncio.to_thread()`. Write tests first (TDD).
```

## WHERE

- **Test file**: `tests/test_reference_projects_mcp_tools.py` — add new test class
- **Source file**: `src/mcp_workspace/server.py` — modify `git()` function

## WHAT

```python
# server.py — modified signature
@mcp.tool()
async def git(
    command: str,
    args: Optional[List[str]] = None,
    pathspec: Optional[List[str]] = None,
    search: Optional[str] = None,
    context: int = 3,
    max_lines: Optional[int] = None,
    compact: bool = True,
    reference_name: Optional[str] = None,  # NEW
) -> str:
```

## HOW

- Add `import asyncio` to `server.py`
- Add `from mcp_workspace.server_reference_tools import get_reference_project_path`
- Remove `@log_function_call` decorator (doesn't support async — mcp-coder-utils#23)
- Make function `async`
- Wrap `git_impl(...)` call in `await asyncio.to_thread(...)`

## ALGORITHM

```
1. if reference_name is set:
2.     project_dir = await get_reference_project_path(reference_name)
3. else:
4.     if _project_dir is None → raise ValueError
5.     project_dir = _project_dir
6. return await asyncio.to_thread(git_impl, command=command, project_dir=project_dir, ...)
```

## DATA

- **New input**: `reference_name: Optional[str] = None`
- **Output**: unchanged — `str` from `git_impl`
- **Errors**: `ValueError` if `reference_name` is invalid (from helper) or `_project_dir` unset (existing)

## TESTS (add to `tests/test_reference_projects_mcp_tools.py`)

New class `TestGitReferenceProject` with 4 tests:

1. `test_git_valid_reference_project` — mock `get_reference_project_path` returning a Path and `git_impl`; verify `git_impl` called with reference project path as `project_dir`, verify correct return value
2. `test_git_invalid_reference_project` — mock `get_reference_project_path` raising `ValueError`; verify error propagates
3. `test_git_ensure_available_before_git_runs` — mock `get_reference_project_path` and `git_impl`; verify helper is awaited (i.e., `ensure_available` runs) before `git_impl` executes
4. `test_git_without_reference_name_uses_project_dir` — no `reference_name` passed; verify `git_impl` is called with `_project_dir` as `project_dir` (regression test for async conversion)

## COMMIT

```
feat(git): support reference_name in git tool

Add optional reference_name parameter to git() MCP tool. When set,
resolves the reference project path and runs the git command there.
Make git() async, wrap git_impl in asyncio.to_thread().

Closes #140
```
