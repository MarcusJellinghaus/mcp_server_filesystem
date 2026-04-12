# Issue #93: Adopt mcp-coder-utils (log_utils)

## Overview

Replace the local `mcp_workspace.log_utils` module with the shared `mcp_coder_utils.log_utils` from the `mcp-coder-utils` package. This removes duplicated logging code and centralises it in the shared library.

## Architectural Changes

### Before

```
mcp_workspace/
├── main.py          → imports from mcp_workspace.log_utils
├── server.py        → imports from mcp_workspace.log_utils
├── file_tools/
│   └── file_operations.py → imports from mcp_workspace.log_utils
└── log_utils.py     ← LOCAL module (structlog, python-json-logger)
```

### After

```
mcp_workspace/
├── main.py          → imports from mcp_coder_utils.log_utils
├── server.py        → imports from mcp_coder_utils.log_utils
└── file_tools/
    └── file_operations.py → imports from mcp_coder_utils.log_utils

(log_utils.py deleted — now lives in mcp-coder-utils package)
```

### Dependency changes

- `structlog` and `python-json-logger` removed from direct dependencies (become transitive via `mcp-coder-utils`)
- Architecture configs (`.importlinter`, `tach.toml`) updated to reference `mcp_coder_utils.log_utils` instead of `mcp_workspace.log_utils`

### Layer diagram update

```
┌─────────────────────────────────┐
│  Entry Point (main.py)          │
├─────────────────────────────────┤
│  MCP Server (server.py)         │
├─────────────────────────────────┤
│  File Tools (file_tools/)       │
├─────────────────────────────────┤
│  mcp_coder_utils.log_utils      │  ← EXTERNAL shared library
└─────────────────────────────────┘
```

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/main.py` | Swap import |
| `src/mcp_workspace/server.py` | Swap import |
| `src/mcp_workspace/file_tools/file_operations.py` | Swap import |
| `pyproject.toml` | Remove `structlog`, `python-json-logger` from deps |
| `.importlinter` | Update layered arch, structlog isolation, add python-json-logger isolation |
| `tach.toml` | Replace `mcp_workspace.log_utils` → `mcp_coder_utils.log_utils` |
| `docs/ARCHITECTURE.md` | Update utilities layer description |

## Files Deleted

| File | Reason |
|------|--------|
| `src/mcp_workspace/log_utils.py` | Replaced by `mcp_coder_utils.log_utils` |
| `tests/test_log_utils.py` | Tests belong in upstream `mcp-coder-utils` repo |

## Steps

1. [Swap imports and delete local log_utils](step_1.md)
2. [Remove direct deps and update architecture configs](step_2.md)
3. [Final verification and stale reference cleanup](step_3.md)
