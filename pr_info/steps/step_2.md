# Step 2: Docstring Updates in Server Wrappers

**Ref:** See `pr_info/steps/summary.md` for full context (Issue #139)

## LLM Prompt

> Implement step 2 of the plan in `pr_info/steps/summary.md`.
> Read `pr_info/steps/step_2.md` for detailed instructions.
> Read all files listed in WHERE before making changes.
> Run all checks after changes.

## WHERE

- `src/mcp_workspace/server.py` — line ~111, `pattern` param docstring
- `src/mcp_workspace/server_reference_tools.py` — line ~174, `pattern` param docstring

## WHAT

Update the `pattern` parameter description in both MCP tool docstrings to document the auto-fallback behavior.

## HOW

Text-only edit in docstrings. No logic changes.

## CHANGES

### `server.py` — `search_files()` docstring

Change:
```
        pattern: Regex to match file contents (e.g. "def foo", "TODO.*fix")
```
to:
```
        pattern: Python regex to match file contents. Invalid regex patterns are
            automatically treated as literal text. (e.g. "def foo", "TODO.*fix")
```

### `server_reference_tools.py` — `search_reference_files()` docstring

Change:
```
        pattern: Regex to match file contents (e.g. "def foo", "TODO.*fix")
```
to:
```
        pattern: Python regex to match file contents. Invalid regex patterns are
            automatically treated as literal text. (e.g. "def foo", "TODO.*fix")
```
