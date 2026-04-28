# Issue #168 — Cross-repo CI plumbing

## Goal

This repo (`mcp-workspace`) sits in the middle of a 4-repo dependency chain:

```
mcp-coder-utils  ──▶  mcp-workspace  ──▶  mcp_coder
   (upstream)         (this repo)        (downstream)
```

Wire up cross-repo type-check signals so a breaking change in `mcp-coder-utils`'s
`main` is caught by `mypy --strict` here within minutes, and a corresponding signal
fans out to `mcp_coder` whenever this repo's `main` updates.

## Architectural / design changes

This is a **CI/build-system change only** — no Python source code is added, removed,
or refactored. Architecture documented in `docs/ARCHITECTURE.md` is unaffected.

What changes:

1. **New `typecheck` extra in `pyproject.toml`** — a *lean* (mypy + types-requests
   only) optional install group, intentionally separate from `dev` rather than a
   slice of it. The duplication with `[dev]` (which already pins `mypy>=1.13.0`
   and `types-requests>=2.31.0`) is deliberate per the issue's Decisions table:
   keeps the cross-repo signal install fast and decoupled from formatter/linter/test
   tooling that the upstream-mypy job does not need.

2. **New cross-repo CI signal pair** — two new GitHub Actions workflows form a
   "fan-in / fan-out" pattern with sibling repos:
   - **Inbound (fan-in):** `upstream-mypy-check.yml` listens for a
     `repository_dispatch` event of type `upstream-main-updated` (sent by
     `mcp-coder-utils` once its `#28` ships) and runs `mypy --strict src tests`
     against the latest upstream `main`.
   - **Outbound (fan-out):** `notify-downstream.yml` fires on every push to this
     repo's `main` and sends an `upstream-main-updated` `repository_dispatch` to
     `mcp_coder`. Uses a fine-grained PAT stored as repo secret `DOWNSTREAM_PAT`.

3. **GitHub Actions version pinning bumped** in existing `ci.yml`:
   `astral-sh/setup-uv@v4 → @v6`, `actions/setup-python@v5 → @v6`. Brings the
   whole repo to one toolchain version for consistency with the new workflows.

### Load-bearing constraints (do not alter without re-reading the issue)

- **Install order in `upstream-mypy-check.yml`**: `mcp-coder-utils @ git+main`
  must install **before** `.[typecheck]`. The bare `mcp-coder-utils` requirement
  in this repo's `dependencies` is then satisfied by the already-installed git
  version; reordering would resolve to the PyPI version and silence the signal.
- **Identical mypy invocation** between `ci.yml`'s mypy matrix entry and
  `upstream-mypy-check.yml`: both run `mypy --strict src tests`. The only
  varying input is the `mcp-coder-utils` version. Don't drift these apart.
- **`types-requests` is required, not optional** in the `typecheck` extra:
  `requests` is imported in `src/mcp_workspace/github_operations/ci_results_manager.py`
  and 3 test files; `mypy --strict` would fail without the stubs.

## Files to create / modify

| Path | Action | Purpose |
|---|---|---|
| `pyproject.toml` | modify | Add `typecheck` extra |
| `.github/workflows/upstream-mypy-check.yml` | create | Inbound signal from `mcp-coder-utils` |
| `.github/workflows/notify-downstream.yml` | create | Outbound signal to `mcp_coder` |
| `.github/workflows/ci.yml` | modify | Bump action versions to match new workflows |

No source modules, no test modules, no `docs/`, no `tools/` are touched.

## Out-of-band setup (manual, not in this PR)

- Add repo secret `DOWNSTREAM_PAT` (Settings → Secrets and variables → Actions).
  PAT scope: `Contents: Read & write` on `mcp_coder`, `Metadata: Read`. The PAT
  created for `mcp-coder-utils#28` can be reused as-is.
- Post-merge verification: trigger `Upstream mypy check` via `workflow_dispatch`
  and confirm mypy runs to completion.

## TDD note

This change is YAML / TOML configuration only — no Python logic to unit-test.
The verification per step is:

1. **Static**: file parses (TOML/YAML), required keys/values present.
2. **Regression**: existing pylint / pytest / mypy checks still pass via
   `mcp__tools-py__run_pylint_check`, `run_pytest_check`, `run_mypy_check`.
3. **Operational** (out-of-band, post-merge): manual `workflow_dispatch` of
   `upstream-mypy-check.yml` confirms install order and mypy invocation.

Where helpful, each step embeds a short Python one-liner in the verification
section that re-parses the file and asserts the expected key — a lightweight
stand-in for a unit test on config.

## Steps (one commit each)

1. **`step_1.md`** — Add `typecheck` extra to `pyproject.toml`.
2. **`step_2.md`** — Create `.github/workflows/upstream-mypy-check.yml`
   (depends on step 1: uses `.[typecheck]`).
3. **`step_3.md`** — Create `.github/workflows/notify-downstream.yml`
   (independent of steps 1 / 2).
4. **`step_4.md`** — Bump `setup-uv@v4 → @v6` and `setup-python@v5 → @v6` in
   `.github/workflows/ci.yml`.

Steps 3 and 4 are independent of each other and of steps 1 / 2; the listed
order matches dependency direction and minimizes review-time confusion.

## Acceptance criteria mapping

| Criterion | Step |
|---|---|
| `[typecheck]` extra exists in `pyproject.toml` | 1 |
| `notify-downstream.yml` exists and parses | 3 |
| `upstream-mypy-check.yml` exists, parses, uses pinned action versions | 2 |
| `ci.yml` bumped to `setup-uv@v6` / `setup-python@v6` | 4 |
| `DOWNSTREAM_PAT` secret set | manual (out of scope of code) |
| Manual `workflow_dispatch` of `Upstream mypy check` runs to completion | manual (post-merge) |
| Auto-trigger after `mcp-coder-utils#28` ships | depends on upstream issue |
| Push to `main` triggers `repository_dispatch` run in `mcp_coder` | manual (post-merge) |
