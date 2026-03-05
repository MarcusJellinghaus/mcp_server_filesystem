# Step 1 — Remove `structlog` from `main.py`

## Context

See [summary.md](summary.md) for the full picture.

`main.py` has `import structlog` and `structured_logger = structlog.get_logger(...)`,
bypassing the rule that all structlog knowledge lives in `log_utils.py`.
This step removes the violation and replaces the six affected log calls with
standard `stdlogger` calls using `%s`-style formatting (consistent with the
existing `stdlogger` usage already in the file).

## TDD Note

This is a pure logging-mechanism refactor — function behaviour is unchanged.
No new tests are required. The existing `pytest` suite (run at the end of the step)
is sufficient to verify no regression.

---

## WHERE

`src/mcp_server_filesystem/main.py`

---

## WHAT

**Removals (module level):**
- `import structlog`
- `structured_logger = structlog.get_logger(__name__)`

**Replacements in `validate_reference_projects(reference_args)`:**

| Old call | New call |
|----------|----------|
| `structured_logger.warning("Invalid reference project format (missing '=')", argument=arg, expected_format="name=/path/to/dir")` | `stdlogger.warning("Invalid reference project format (missing '='): argument=%s, expected_format=name=/path/to/dir", arg)` |
| `structured_logger.warning("Invalid reference project format (empty name)", argument=arg, expected_format="name=/path/to/dir")` | `stdlogger.warning("Invalid reference project format (empty name): argument=%s, expected_format=name=/path/to/dir", arg)` |
| `structured_logger.warning("Reference project path does not exist", name=name, path=str(project_path))` | `stdlogger.warning("Reference project path does not exist: name=%s, path=%s", name, str(project_path))` |
| `structured_logger.warning("Reference project path is not a directory", name=name, path=str(project_path))` | `stdlogger.warning("Reference project path is not a directory: name=%s, path=%s", name, str(project_path))` |

**Replacements in `main()`:**

| Old call | New call |
|----------|----------|
| `structured_logger.debug("Structured logger initialized in main", log_level=args.log_level)` | **Delete** — semantically identical to `stdlogger.debug("Logger initialized in main")` on the line above |
| `if log_file: structured_logger.info("Starting MCP server", project_dir=..., log_level=..., log_file=...)` | **Delete the `if log_file:` block**; extend the existing `stdlogger.info(...)` call above it to include `log_level` and `log_file` |

**Extended `stdlogger.info` in `main()`:**
```python
# BEFORE:
stdlogger.info("Starting MCP server with project directory: %s", project_dir)
if log_file:
    structured_logger.info(
        "Starting MCP server",
        project_dir=str(project_dir),
        log_level=args.log_level,
        log_file=log_file,
    )

# AFTER:
stdlogger.info(
    "Starting MCP server: project_dir=%s, log_level=%s, log_file=%s",
    project_dir,
    args.log_level,
    log_file,
)
```

---

## HOW

- Edit `src/mcp_server_filesystem/main.py` only.
- No imports added — `stdlogger` already exists (`logging.getLogger(__name__)`).
- No other files touched in this step.

---

## ALGORITHM

```
1. Delete the two structlog lines at module level (import + structured_logger assignment)
2. In validate_reference_projects: replace each structured_logger.warning() with
   stdlogger.warning(), inlining keyword args as %s positional args in the message
3. In main(): delete the structured_logger.debug() call (redundant with line above)
4. In main(): replace stdlogger.info() + if log_file: structured_logger.info() block
   with a single stdlogger.info() that includes project_dir, log_level, log_file
5. Run: pytest  →  all existing tests must pass
```

---

## DATA

No return value or data structure changes. Logging output changes:
- Warnings in `validate_reference_projects`: structured fields are now inline in the message string (visible in both console and file modes).
- Startup info: single log line replaces the `if log_file:` conditional block.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement Step 1 exactly as specified:

1. Open src/mcp_server_filesystem/main.py.
2. Remove `import structlog` and `structured_logger = structlog.get_logger(__name__)`.
3. In validate_reference_projects(), replace all four structured_logger.warning() calls
   with stdlogger.warning() calls, inlining the keyword arguments as %s positional
   args in the message string (see the replacement table in step_1.md).
4. In main(), delete the structured_logger.debug() call after setup_logging().
5. In main(), replace the stdlogger.info("Starting MCP server...") + if log_file: block
   with a single stdlogger.info() that covers project_dir, log_level, and log_file.
6. Run pytest and confirm all tests pass.

Do not modify any other file in this step.
```
