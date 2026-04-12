# Step 2: Remove direct deps and update architecture configs

## Summary

See [summary.md](summary.md) for full context.

Remove `structlog` and `python-json-logger` from direct dependencies (now transitive via `mcp-coder-utils`). Update `.importlinter` and `tach.toml` to reference `mcp_coder_utils.log_utils`.

## WHERE

Files to edit:
- `pyproject.toml`
- `.importlinter`
- `tach.toml`
- `docs/ARCHITECTURE.md`
- `tools/tach_docs.py`

## WHAT

### pyproject.toml

Remove these two lines from `[project] dependencies`:
```
"structlog>=25.2.0",
"python-json-logger>=3.3.0",
```

### .importlinter

**Layered architecture contract** — remove `mcp_workspace.log_utils` from the `layers` list entirely (`mcp_coder_utils` is an external package and cannot be a layer).

**Structlog isolation contract** — remove the `ignore_imports` line (`mcp_workspace.log_utils -> structlog`) entirely. Since the import now comes from `mcp_coder_utils` which is outside the `source_modules = mcp_workspace` scope, no ignore rule is needed.

**New contract** — add `python-json-logger` isolation (no `ignore_imports` needed for the same reason):
```ini
[importlinter:contract:pythonjsonlogger_isolation]
name = Python JSON Logger Isolation
type = forbidden
source_modules =
    mcp_workspace
forbidden_modules =
    pythonjsonlogger
```

### tach.toml

Replace all `mcp_workspace.log_utils` → `mcp_coder_utils.log_utils`:
- Module path declaration
- Layer assignment
- All `depends_on` entries referencing it (in main, server, file_tools, tests modules)

### tools/tach_docs.py

Remove or update the hardcoded reference to `"src/mcp_workspace/log_utils.py"` (around line 271). The local module no longer exists after step 1.

### docs/ARCHITECTURE.md

Update the utilities layer description:
- Layer diagram: `Utilities (log_utils.py)` → `Shared Libs (mcp_coder_utils)`
- Library isolation table: `structlog` used by `mcp_coder_utils.log_utils` (external)
- Layer responsibilities table: Utilities row updated

## HOW

1. Edit `pyproject.toml` — remove two dependency lines
2. Edit `.importlinter` — update three contracts
3. Edit `tach.toml` — replace module references
4. Edit `tools/tach_docs.py` — remove stale `log_utils.py` reference
5. Edit `docs/ARCHITECTURE.md` — update layer descriptions
6. Run pylint, pytest, mypy

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement step 2: remove structlog and python-json-logger from pyproject.toml
direct deps. Update .importlinter (remove log_utils from layers, remove
structlog ignore_imports, add python-json-logger isolation contract without
ignore_imports). Update tach.toml to reference mcp_coder_utils.log_utils.
Update tools/tach_docs.py to remove stale log_utils.py reference. Update
docs/ARCHITECTURE.md layer descriptions. Run pylint, pytest (excluding
integration markers), and mypy to verify.
```
