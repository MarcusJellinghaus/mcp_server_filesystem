# Step 3 — Wire `ensure_truststore()` into `main()`

> See `pr_info/steps/summary.md` for the overall plan. Depends on Step 2.

## LLM Prompt

> Read `pr_info/steps/summary.md` and then implement **Step 3** as described in `pr_info/steps/step_3.md`. Step 2 must already be merged/complete before starting this. Add the import and the single call site to `main()`. Add a small test that confirms `ensure_truststore()` is invoked when `main()` runs (mock the helper to keep the test isolated and fast). Run pylint, mypy, pytest after each edit. Commit once all checks are green.

## WHERE

| Action | File | Symbol |
|---|---|---|
| Modify | `src/mcp_workspace/main.py` | `main()` |
| Modify | `tach.toml` | add `mcp_workspace._ssl` to `mcp_workspace.main` `depends_on` |
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

### Config edit (mandatory in this step)

`tach.toml` — extend the `mcp_workspace.main` `depends_on` list with the new module. Concretely, add `{ path = "mcp_workspace._ssl" }`:

```toml
[[modules]]
path = "mcp_workspace.main"
layer = "entry"
depends_on = [
    { path = "mcp_workspace.server" },
    { path = "mcp_workspace.reference_projects" },
    { path = "mcp_workspace._ssl" },              # NEW in step 3
    { path = "mcp_coder_utils.log_utils" },
]
```

`.importlinter` requires no further edit — the `layered_architecture` contract was extended in step 2 and `entry -> utilities` is already a downward import.

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

One wiring test in `tests/test_ssl.py` (or a new `tests/test_main_wiring.py` if preferred):

- Patch `mcp_workspace.main.ensure_truststore`, `mcp_workspace.main.setup_logging`, and `mcp_workspace.server.run_server` (the lazy import target — patch on its source module so the late `from mcp_workspace.server import run_server` inside `main()` picks up the mock).
- Use `monkeypatch.setattr(sys, "argv", [...])` with `--project-dir <real tmp dir>` (use the `tmp_path` pytest fixture) so `parse_args` / `validate_reference_projects` accept real input without further mocking.
- Attach all three patched callables to a single shared `parent = Mock()` (e.g. `parent.attach_mock(mock_setup_logging, "setup_logging")`, etc.).
- Call `main()`, then assert call ordering via `parent.mock_calls.index(...)`:
  - `setup_logging` index < `ensure_truststore` index — proves the helper runs after logging is configured (so its log lines land in the configured handler).
  - `ensure_truststore` index < `run_server` index — proves the SSL monkeypatch is active before any GitHub work; this also covers the "before any GitHub-related code path" property.

Drop any source-text-inspection variant — the patched-callable ordering test is sufficient.

## Quality Gates

- `mcp__tools-py__run_pytest_check` (standard `-n auto -m "not ..."` exclusion pattern)
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_mypy_check`
- `mcp__tools-py__run_tach_check` — must pass with `mcp_workspace._ssl` added to the `mcp_workspace.main` `depends_on` list.
- `mcp__tools-py__run_lint_imports_check` — must continue to pass (no new contract change in this step).

All five must pass independently after this step's commit.

## Commit Message Suggestion

`Activate truststore in main() before server import`
