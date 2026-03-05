# Step 2 — Fix `.importlinter`

## Context

See [summary.md](summary.md) for the full picture.

Two things need fixing in `.importlinter`:

1. **Remove the broken `file_tools_independence` contract** — it declares `directory_utils`
   and `path_utils` as mutually independent, but `directory_utils` already imports
   `path_utils` (`from mcp_server_filesystem.file_tools.path_utils import normalize_path`).
   The contract is factually wrong and would fail immediately. The coupling is intentional
   and legitimate — just remove the contract.

2. **Remove the `main.py` structlog exemption** — after Step 1, `main.py` no longer
   imports `structlog`, so the `ignore_imports` line
   `mcp_server_filesystem.main -> structlog` in `[importlinter:contract:structlog_isolation]`
   is dead config. Remove it.

## TDD Note

The "test" for this step is running `lint-imports` (Step 3). No Python unit tests apply
to config file changes.

---

## WHERE

`.importlinter` (project root)

---

## WHAT

**Remove entirely** — the `[importlinter:contract:file_tools_independence]` section:

```ini
# DELETE this entire block (including the comment header above it):

# -----------------------------------------------------------------------------
# Contract: File Tools Independence
# -----------------------------------------------------------------------------
# File tool modules should not depend on each other where possible.
# This keeps each tool focused and independently testable.
# -----------------------------------------------------------------------------
[importlinter:contract:file_tools_independence]
name = File Tools Module Independence
type = independence
modules =
    mcp_server_filesystem.file_tools.directory_utils
    mcp_server_filesystem.file_tools.path_utils
```

**Remove one line** from `[importlinter:contract:structlog_isolation]`:

```ini
# BEFORE:
ignore_imports =
    mcp_server_filesystem.log_utils -> structlog
    mcp_server_filesystem.main -> structlog    ← DELETE this line

# AFTER:
ignore_imports =
    mcp_server_filesystem.log_utils -> structlog
```

---

## HOW

- Edit `.importlinter` only.
- No Python files touched in this step.
- The remaining contracts (`layered_architecture`, `mcp_library_isolation`,
  `gitpython_isolation`, `structlog_isolation`, `no_test_imports_in_source`)
  are untouched and correct.

---

## ALGORITHM

```
1. Open .importlinter
2. Delete the file_tools_independence comment block + [importlinter:contract:file_tools_independence] section
3. In structlog_isolation, delete the line: mcp_server_filesystem.main -> structlog
4. Verify the remaining file is syntactically valid (no orphaned keys, no blank section headers)
5. Proceed to Step 3 to run lint-imports and confirm
```

---

## DATA

Config file change only. No runtime data affected.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement Step 2 exactly as specified:

1. Open .importlinter.
2. Delete the entire [importlinter:contract:file_tools_independence] section,
   including its comment header block above it.
3. In [importlinter:contract:structlog_isolation], delete the line:
       mcp_server_filesystem.main -> structlog
   Leave the mcp_server_filesystem.log_utils -> structlog line intact.
4. Save the file.

Do not modify any other file in this step.
Do not run any checks yet — that is Step 3.
```
