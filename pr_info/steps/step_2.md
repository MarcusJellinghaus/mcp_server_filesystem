# Step 2: Rewrite Server Tool and Its Tests

## Context

Read `pr_info/steps/summary.md` for the full picture. Step 1 rewrote the utility
function. This step rewrites the server-layer `edit_file` MCP tool and its test file
`tests/file_tools/test_edit_file_api.py`.

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step file. Step 1 is complete.
> Rewrite the `edit_file` tool in `src/mcp_workspace/server.py` with async + locking,
> and rewrite `tests/file_tools/test_edit_file_api.py` (TDD: tests first, then
> implementation). Run all quality checks after. Commit as one unit.

## WHERE

- `src/mcp_workspace/server.py` — the `edit_file` MCP tool function (~lines 270-330)
- `tests/file_tools/test_edit_file_api.py` — server-layer tests

## WHAT — New server tool signature

```python
@mcp.tool()
@log_function_call
async def edit_file(
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> str:
```

## HOW — Integration points

- Add module-level lock dict: `_file_locks: Dict[str, asyncio.Lock] = {}`
- `asyncio` is already imported in server.py
- `edit_file_util` import stays the same (from `mcp_workspace.file_tools`)
- The tool docstring becomes the MCP tool description — write it to match Claude Code's Edit

## ALGORITHM — Server tool with locking

```
validate file_path is non-empty string
check _project_dir is set
check file is not gitignored
resolve absolute path: abs_path = str((_project_dir / file_path).resolve())
lock = _file_locks.setdefault(abs_path, asyncio.Lock())
async with lock:
    return edit_file_util(file_path, old_string, new_string, replace_all, _project_dir)
```

## DATA — Return value

- Returns `str` directly (diff, message, or exception propagates)
- No wrapping, no dict conversion

## WHAT — Code to remove from server.py edit_file

- `edits` parameter and all normalization logic for it
- `dry_run` parameter
- `options` parameter and supported_options validation
- The entire `normalized_edits` / `normalized_options` block
- The `List[Dict[str, str]]` and `Dict[str, Any]` return type

## WHAT — Tests to write (test_edit_file_api.py)

Rewrite the file with these test cases:

1. **Basic edit via server tool** — calls server `edit_file`, returns diff string
2. **Text not found** — raises `ValueError`
3. **replace_all via server** — replaces all occurrences
4. **Empty old_string via server** — inserts at beginning
5. **Gitignore check** — gitignored files are rejected
6. **Locking serializes same-file edits** — two concurrent async edits to same file both succeed (no lost writes)
7. **Different files not blocked** — concurrent edits to different files don't interfere

## HOW — Test patterns

- Tests use `pytest` style with `project_dir` fixture (matches existing pattern)
- Locking tests use `asyncio.gather` to run concurrent edits
- Mark async tests with `@pytest.mark.asyncio`
- Call server functions directly (not via MCP protocol) — matches existing pattern
- Use `set_project_dir()` in fixture setup

## Decisions

- No `asyncio.to_thread` — the utility is fast (file read + string replace + file write)
- Evaluate the existing try/except logging wrapper around the utility call — either keep for server-level logging or remove since the utility already logs via `@log_function_call` and the MCP framework handles exception propagation
- Lock dict grows unbounded — acceptable for MCP server lifetime (bounded by unique files edited)
- `_file_locks` is module-level, not class-level — matches existing server.py pattern (`_project_dir`)
