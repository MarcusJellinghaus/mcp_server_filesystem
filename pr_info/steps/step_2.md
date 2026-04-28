# Step 2 — Add `_ssl.py` helper + `truststore` dependency

> See `pr_info/steps/summary.md` for the overall plan.

## LLM Prompt

> Read `pr_info/steps/summary.md` and then implement **Step 2** as described in `pr_info/steps/step_2.md`. Follow TDD: write `tests/test_ssl.py` first, watch them fail, then add `src/mcp_workspace/_ssl.py` and the dependency to `pyproject.toml`. Do not wire anything into `main()` in this step — that is Step 3. Run pylint, mypy, pytest after each edit; if `tach check` or `lint-imports` flag the new module, add the minimal config declaration needed. Commit with a single descriptive message once all checks are green.

## WHERE

| Action | File | Symbol |
|---|---|---|
| Create | `src/mcp_workspace/_ssl.py` | `ensure_truststore()` |
| Create | `tests/test_ssl.py` | tests for `ensure_truststore()` |
| Modify | `pyproject.toml` | add `truststore` to `[project].dependencies` |
| Conditional modify | `tach.toml` | declare `mcp_workspace._ssl` (only if `tach check` flags it) |
| Conditional modify | `.importlinter` | add `_ssl` to `layered_architecture` (only if `lint-imports` flags it) |

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
- Use a module-level `logging.getLogger(__name__)` and emit a single `debug("truststore activated: using OS certificate store")` line on activation.
- Add `truststore` (bare, unpinned) to `[project].dependencies` in `pyproject.toml`. Place it alongside the other core deps.
- **Do not** edit `main.py` in this step.

## ALGORITHM

```
if _activated: return
try: import truststore
except ImportError: return
truststore.inject_into_ssl()
_activated = True
log.debug("truststore activated: using OS certificate store")
```

## DATA

Returns `None`. Mutates module-level `_activated` flag and (on success) global `ssl.SSLContext`.

## Tests to Add (TDD — write first)

`tests/test_ssl.py`:

1. **`test_idempotent_calls_inject_once`** — patch `sys.modules['truststore']` with a `MagicMock`, reset the module's `_activated` flag (or reload the module), call `ensure_truststore()` twice, assert the mock's `inject_into_ssl` was called exactly once.
2. **`test_no_op_when_truststore_unavailable`** — simulate `ImportError` (e.g. `monkeypatch.setitem(sys.modules, "truststore", None)` or use a custom meta-path finder). Call `ensure_truststore()`. Assert no exception, `_activated` stays `False`.

Reset `_activated` between tests via a fixture so test order doesn't matter.

Test file path: `tests/test_ssl.py` (mirrors flat source layout `src/mcp_workspace/_ssl.py`).

## Quality Gates

- `mcp__tools-py__run_pytest_check` (standard `-n auto -m "not ..."` exclusion pattern)
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_mypy_check`
- Manually run `tach check` and `lint-imports` (if MCP tooling exposes them, otherwise via the `tools/` shell scripts). Add the **minimal** declaration needed if a contract breaks:
  - `tach.toml`: a `[[modules]]` block for `mcp_workspace._ssl` at the utilities layer, `depends_on = []`
  - `.importlinter`: append `| mcp_workspace._ssl` to the bottom utilities row of `layered_architecture`

## Commit Message Suggestion

`Add ensure_truststore() helper and truststore dependency`
