# Issue #57 — Review and Tighten Architecture Enforcement

## Problem Summary

`import-linter` was temporarily removed from CI because two bugs in `.importlinter` would cause it to fail, and `main.py` has a direct `structlog` import that violates the intended isolation contract:

1. **`main.py` bypasses `log_utils`** — it imports `structlog` directly and creates its own `structured_logger`, breaking the architectural rule that all structlog knowledge belongs in `log_utils.py`.
2. **Broken independence contract** — `.importlinter` declares `directory_utils` and `path_utils` as mutually independent, but `directory_utils` already imports `path_utils`. The contract is factually wrong and would fail immediately.

## Architectural / Design Changes

### Before

```
main.py  ──imports──►  structlog        (direct violation)
main.py  ──imports──►  log_utils        (correct)

.importlinter:
  structlog_isolation exempts main.py   (workaround for the violation)
  file_tools_independence: directory_utils ⊥ path_utils  (false — already coupled)

CI architecture matrix: tach, pycycle, vulture  (import-linter missing)
```

### After

```
main.py  ──imports──►  log_utils only   (all structlog knowledge in one place)

.importlinter:
  structlog_isolation: only log_utils exempted  (no more main.py workaround)
  file_tools_independence: REMOVED              (was broken; coupling is legitimate)

CI architecture matrix: tach, pycycle, vulture, import-linter  (restored)
```

### Design Principle Applied

`log_utils.py` is the single home for all structlog knowledge. `main.py` uses only
`stdlogger` (standard `logging.getLogger`) and inlines contextual data into `%s`-style
format strings — consistent with the existing `stdlogger` usage already present in the file.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_server_filesystem/main.py` | Remove `import structlog` and `structured_logger`; replace calls with `stdlogger` |
| `.importlinter` | Remove broken independence contract; remove `main.py` structlog exemption |
| `.github/workflows/ci.yml` | Re-add `import-linter` to architecture matrix |

## Files Created

None.

## No-Action Items (per issue)

- `tach.toml` — `file_tools → log_utils` coupling via `file_operations.py` is legitimate; no change.
- `tests/` — test module boundary left unenforced; no change.

## Implementation Steps

| Step | File | What |
|------|------|------|
| [Step 1](step_1.md) | `main.py` | Remove structlog; replace 6 calls with stdlogger |
| [Step 2](step_2.md) | `.importlinter` | Remove broken contract + unneeded exemption |
| [Step 3](step_3.md) | `ci.yml` | Re-add import-linter; verify locally |

## TDD Note

These are logging-mechanism and config changes — function behaviour is unchanged.
The existing `pytest` suite verifies no regression. Step 3 verifies architecture with
`lint-imports` itself (the architecture test *is* the linter).
