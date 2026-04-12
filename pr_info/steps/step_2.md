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

## WHAT

### pyproject.toml

Remove these two lines from `[project] dependencies`:
```
"structlog>=25.2.0",
"python-json-logger>=3.3.0",
```

### .importlinter

**Layered architecture contract** — replace `mcp_workspace.log_utils` with `mcp_coder_utils.log_utils` in the `layers` list.

**Structlog isolation contract** — change `ignore_imports` from `mcp_workspace.log_utils -> structlog` to `mcp_coder_utils.log_utils -> structlog`.

**New contract** — add `python-json-logger` isolation:
```ini
[importlinter:contract:pythonjsonlogger_isolation]
name = Python JSON Logger Isolation
type = forbidden
source_modules =
    mcp_workspace
forbidden_modules =
    pythonjsonlogger
ignore_imports =
    mcp_coder_utils.log_utils -> pythonjsonlogger
```

### tach.toml

Replace all `mcp_workspace.log_utils` → `mcp_coder_utils.log_utils`:
- Module path declaration
- Layer assignment
- All `depends_on` entries referencing it (in main, server, file_tools, tests modules)

### docs/ARCHITECTURE.md

Update the utilities layer description:
- Layer diagram: `Utilities (log_utils.py)` → `Shared Libs (mcp_coder_utils)`
- Library isolation table: `structlog` used by `mcp_coder_utils.log_utils` (external)
- Layer responsibilities table: Utilities row updated

## HOW

1. Edit `pyproject.toml` — remove two dependency lines
2. Edit `.importlinter` — update three contracts
3. Edit `tach.toml` — replace module references
4. Edit `docs/ARCHITECTURE.md` — update layer descriptions
5. Run pylint, pytest, mypy

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement step 2: remove structlog and python-json-logger from pyproject.toml
direct deps. Update .importlinter (layered arch, structlog isolation, new
python-json-logger isolation contract). Update tach.toml to reference
mcp_coder_utils.log_utils. Update docs/ARCHITECTURE.md layer descriptions.
Run pylint, pytest (excluding integration markers), and mypy to verify.
```
