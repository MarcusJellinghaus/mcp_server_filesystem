# Step 2 — Add `_ssl.py` helper + `truststore` dependency

> See `pr_info/steps/summary.md` for the overall plan.

## LLM Prompt

> Read `pr_info/steps/summary.md` and then implement **Step 2** as described in `pr_info/steps/step_2.md`. Follow TDD: write `tests/test_ssl.py` first, watch them fail, then add `src/mcp_workspace/_ssl.py` and the dependency to `pyproject.toml`. Register the new module in `tach.toml` and `.importlinter` as part of this step (mandatory — see config edits below). Do not wire anything into `main()` in this step — that is Step 3. Run pylint, mypy, pytest, `tach check`, and `lint-imports` after each edit. Commit with a single descriptive message once all checks are green.

## WHERE

| Action | File | Symbol |
|---|---|---|
| Create | `src/mcp_workspace/_ssl.py` | `ensure_truststore()` |
| Create | `tests/test_ssl.py` | tests for `ensure_truststore()` |
| Modify | `pyproject.toml` | add `truststore` to `[project].dependencies` |
| Modify | `tach.toml` | declare `mcp_workspace._ssl` at utilities layer (mandatory) |
| Modify | `.importlinter` | add `_ssl` to `layered_architecture` bottom row (mandatory) |

## WHAT

```python
# src/mcp_workspace/_ssl.py
def ensure_truststore() -> None: ...
```

Idempotent. No-op when `truststore` is not importable.

## HOW

- **Library-safety is non-negotiable.** This module must NOT call `ensure_truststore()` at import time.
- Module-level `_activated: bool = False` guard so `truststore.inject_into_ssl()` runs at most once across the process lifetime, even if `ensure_truststore()` is called repeatedly.
- Import `truststore` lazily inside the function (defensive `try/except ImportError`) so the module is safe to import even if the optional dep is somehow missing in a downstream consumer.
- Wrap the `truststore.inject_into_ssl()` call in a broad `except Exception` (warn-and-continue): a corporate-proxy environment failing truststore activation must NOT crash the server. PyGithub falls back to certifi if the global SSL monkeypatch isn't applied. Log a warning with the exception message.
- Use a module-level `logging.getLogger(__name__)` and emit a single `debug("truststore activated: using OS certificate store")` line on activation; emit `warning(...)` on import failure or inject failure.
- Add `truststore` (bare, unpinned — matching the `mcp-coder-utils` style) to the **end** of the `dependencies = [ ... ]` list in `[project]` in `pyproject.toml`, immediately after `"PyGithub>=1.59.0",`. Concrete diff:

  ```diff
   dependencies = [
       "pathspec>=0.12.1",
       "igittigitt>=2.1.5",
       "mcp>=1.3.0",
       "GitPython>=3.1.0",
       "mcp-coder-utils",
       "PyGithub>=1.59.0",
  +    "truststore",
   ]
  ```
- **Do not** edit `main.py` in this step.

### Config edits (mandatory in this step)

`tach.toml` — register the new module as a utilities-layer leaf alongside `mcp_workspace.utils`. Append:

```toml
[[modules]]
path = "mcp_workspace._ssl"
layer = "utilities"
depends_on = []
```

`.importlinter` — append `mcp_workspace._ssl` to the bottom (utilities) row of the `layered_architecture` contract. The current bottom row is:

```
mcp_workspace.config | mcp_workspace.constants | mcp_workspace.utils
```

Change it to:

```
mcp_workspace.config | mcp_workspace.constants | mcp_workspace.utils | mcp_workspace._ssl
```

`tach.toml` `[[modules]] path = "tests"` block: although the project sets `exact = false` (which technically allows omission), the existing `tests` block enumerates every internal `mcp_workspace.*` module it imports. For consistency, **mandatorily** append `{ path = "mcp_workspace._ssl" }` to the `tests` `depends_on` list as part of this step's `tach.toml` edit. Concrete diff:

```diff
 [[modules]]
 path = "tests"
 depends_on = [
     { path = "mcp_workspace" },
     { path = "mcp_workspace.main" },
     { path = "mcp_workspace.server" },
     { path = "mcp_workspace.server_reference_tools" },
     { path = "mcp_workspace.file_tools" },
     { path = "mcp_workspace.git_operations" },
     { path = "mcp_workspace.github_operations" },
     { path = "mcp_workspace.checks" },
     { path = "mcp_workspace.workflows" },
     { path = "mcp_workspace.reference_projects" },
     { path = "mcp_workspace.config" },
     { path = "mcp_workspace.constants" },
     { path = "mcp_workspace.utils" },
+    { path = "mcp_workspace._ssl" },
     { path = "mcp_coder_utils.log_utils" },
 ]
```

## ALGORITHM

```python
def ensure_truststore() -> None:
    global _activated                       # MANDATORY: assignment below would
                                            # otherwise create a local name and
                                            # break the idempotency guard.
    if _activated:                          # idempotent guard
        return
    try:
        import truststore
    except ImportError:
        log.warning("truststore not installed; skipping OS trust-store activation")
        return
    try:
        truststore.inject_into_ssl()
    except Exception as exc:                # noqa: BLE001 — intentional broad catch
        log.warning(
            "truststore.inject_into_ssl() failed: %s; falling back to certifi", exc
        )
        return
    _activated = True
    log.debug("truststore activated: using OS certificate store")
```

The `global _activated` declaration is **required** — without it, the `_activated = True` assignment creates a function-local variable, leaving the module-level flag at `False` and breaking the `test_idempotent_calls_inject_once` test.

The broad `except Exception` is intentional — see HOW above. Failures must warn-and-continue, not propagate.

## DATA

Returns `None`. Mutates module-level `_activated` flag and (on success) global `ssl.SSLContext`.

## Tests to Add (TDD — write first)

`tests/test_ssl.py`:

1. **`test_idempotent_calls_inject_once`** — patch `sys.modules['truststore']` with a `MagicMock`, reset the module's `_activated` flag (or reload the module), call `ensure_truststore()` twice, assert the mock's `inject_into_ssl` was called exactly once.
2. **`test_no_op_when_truststore_unavailable`** — simulate `ImportError` (e.g. `monkeypatch.setitem(sys.modules, "truststore", None)` or use a custom meta-path finder). Call `ensure_truststore()`. Assert no exception, `_activated` stays `False`, and a warning is logged.
3. **`test_import_does_not_activate`** — proves the library-safety guarantee: importing `mcp_workspace._ssl` must NOT activate truststore. Patch `truststore.inject_into_ssl` (e.g. via `monkeypatch.setattr` on a stub `truststore` module in `sys.modules`) **before** importing/reloading `mcp_workspace._ssl`. After the import statement, assert `inject_into_ssl` was **not** called and the module's `_activated` flag is `False`.
4. **`test_inject_failure_does_not_raise`** — corporate-proxy resilience: mock `truststore.inject_into_ssl` to raise (`RuntimeError("nope")` or similar). Call `ensure_truststore()`. Assert no exception propagates, `_activated` stays `False`, and a warning is logged with the exception message.

Reset `_activated` between tests via a fixture so test order doesn't matter.

Test file path: `tests/test_ssl.py` (mirrors flat source layout `src/mcp_workspace/_ssl.py`).

## Quality Gates

- `mcp__tools-py__run_pytest_check` (standard `-n auto -m "not ..."` exclusion pattern)
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_mypy_check`
- `mcp__tools-py__run_tach_check` — must pass with the new `[[modules]]` block declared.
- `mcp__tools-py__run_lint_imports_check` — must pass with `mcp_workspace._ssl` listed in the bottom row of `layered_architecture`.

All five must pass independently after this step's commit (the module exists and is registered, even though `main.py` does not yet import it — that is step 3).

## Commit Message Suggestion

`Add ensure_truststore() helper and truststore dependency`
