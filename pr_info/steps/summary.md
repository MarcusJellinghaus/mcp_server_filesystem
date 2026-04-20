# Issue #20: Tighten content type hint from Any to str in save_file and append_file

## Summary

The `save_file` and `append_file` MCP tools in `server.py` declare `content: Any` but enforce `isinstance(content, str)` at runtime. This mismatch lets Pydantic accept non-string input (e.g. dicts) that then fails with a confusing runtime error. The fix tightens the type hint to `content: str` so Pydantic rejects non-string input at the validation boundary.

## Architectural / Design Changes

- **No architectural changes.** This is a type-annotation-only fix at the MCP tool boundary layer.
- The runtime `None` and `isinstance` checks are preserved as defense-in-depth for direct Python callers bypassing MCP validation.
- No auto-serialization of non-string types is introduced — the tool contract remains "write this string to a file."

## Files to Modify

| File | Change |
|------|--------|
| `src/mcp_workspace/server.py` | Change `content: Any` → `content: str` on `save_file` and `append_file` |
| `tests/test_server.py` | Add tests verifying non-string content is rejected (TDD) |

## Implementation Steps

- **Step 1**: Add tests for type rejection + change type hints (single commit)
