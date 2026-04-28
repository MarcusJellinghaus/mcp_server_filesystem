# Step 3 — Wire `ensure_truststore()` into `main()`

> See `pr_info/steps/summary.md` for the overall plan. Depends on Step 2.

## LLM Prompt

> Read `pr_info/steps/summary.md` and then implement **Step 3** as described in `pr_info/steps/step_3.md`. Step 2 must already be merged/complete before starting this. Add the import and the single call site to `main()`. Add a small test that confirms `ensure_truststore()` is invoked when `main()` runs (mock the helper to keep the test isolated and fast). Run pylint, mypy, pytest after each edit. Commit once all checks are green.

## WHERE

| Action | File | Symbol |
|---|---|---|
| Modify | `src/mcp_workspace/main.py` | `main()` |
| Modify | `tests/test_server.py` *or* extend `tests/test_ssl.py` | one wiring test |

## WHAT

Add to `main()`:

```python
from mcp_workspace._ssl import ensure_truststore   # top of file with other imports
...
def main() -> None:
    ...
    setup_logging(args.log_level, log_file)
    stdlogger.debug("Logger initialized in main")

    ensure_truststore()                              # <-- new line, immediately after setup_logging block

    ...
    from mcp_workspace.server import run_server     # <-- must remain AFTER ensure_truststore()
```

## HOW

- **Exact placement matters.** `ensure_truststore()` is called:
  - **After** `setup_logging(...)` and the `stdlogger.debug("Logger initialized in main")` line — so the helper's debug log lands in the configured handler.
  - **Before** the lazy `from mcp_workspace.server import run_server` import — so the SSL monkeypatch is active before any GitHub-related code path can run.
- The call goes **only** in `main()`. Do not add a call to `__main__.py`, `server.py`, or any module-level location. `__main__.py` already forwards to `main()`, and `server.py` has no `if __name__` block — single entry point is confirmed.
- No changes to `parse_args()`, `validate_reference_projects()`, or argument schema.

## ALGORITHM

(No new logic; just placement.)

```
parse_args()
validate project_dir
compute log_file
setup_logging(level, log_file)
stdlogger.debug("Logger initialized in main")
ensure_truststore()                  # NEW
parse reference_projects
from mcp_workspace.server import run_server
run_server(...)
```

## DATA

No return value or signature changes.

## Tests to Add (TDD — write first)

One small test confirming the wiring. Two reasonable options — pick the simpler:

- **Option A (preferred):** in `tests/test_ssl.py`, add a test that imports `mcp_workspace.main`, patches `mcp_workspace.main.ensure_truststore` with a `MagicMock`, also patches `parse_args` / `setup_logging` / `run_server` / `Path.exists` etc. as needed, calls `main()`, asserts the helper was invoked exactly once and **after** `setup_logging` was called (use a shared `MagicMock` parent with `mock_calls` to assert order).
- **Option B:** integration-style — assert by reading `main.py` source that the call appears between the two anchor lines. Simpler but brittle. Avoid unless A proves disproportionately complex.

## Quality Gates

- `mcp__tools-py__run_pytest_check` (standard `-n auto -m "not ..."` exclusion pattern)
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_mypy_check`
- `tach check` and `lint-imports` should still pass (Step 2 already handled any needed config).

## Commit Message Suggestion

`Activate truststore in main() before server import`
