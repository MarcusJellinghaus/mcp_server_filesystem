# Step 1 — Add `typecheck` extra to `pyproject.toml`

> See [`summary.md`](./summary.md) for full context, design rationale, and
> load-bearing constraints. This step is the prerequisite for step 2 (which
> installs `.[typecheck]`).

## WHERE

- **File:** `pyproject.toml` (modify only).
- **Section:** `[project.optional-dependencies]`.

## WHAT

Add a new `typecheck` extra immediately after the existing `dev` extra, with
exactly the two entries from the issue:

```toml
typecheck = ["mypy>=1.13.0", "types-requests>=2.31.0"]
```

The values **must match** the pins already in `[dev]`. If `[dev]` ever drifts,
that drift is intentional — see Decisions table in the issue.

## HOW

Plain TOML edit. No imports, decorators, or wiring elsewhere. The new extra
becomes installable as `pip install -e ".[typecheck]"` and is consumed by step 2.

## ALGORITHM

n/a — single-line config addition.

## DATA

```toml
[project.optional-dependencies]
dev = [ ... existing entries unchanged ... ]
typecheck = ["mypy>=1.13.0", "types-requests>=2.31.0"]
architecture = [ ... existing entries unchanged ... ]
config = [ ... existing entries unchanged ... ]
```

## Verification (TDD-equivalent for config)

1. **Parse + key-presence check** (lightweight stand-in for a unit test):

   ```bash
   python -c "import tomllib, sys; \
     d = tomllib.load(open('pyproject.toml','rb')); \
     tc = d['project']['optional-dependencies']['typecheck']; \
     assert 'mypy>=1.13.0' in tc and 'types-requests>=2.31.0' in tc, tc; \
     print('OK', tc)"
   ```

2. **Regression — run all three quality checks** (mandated by `CLAUDE.md`):
   - `mcp__tools-py__run_pylint_check`
   - `mcp__tools-py__run_pytest_check` with
     `extra_args=["-n", "auto", "-m", "not git_integration and not github_integration"]`
   - `mcp__tools-py__run_mypy_check`

   All three must pass before commit.

3. **(Optional, manual)** confirm `pip install -e ".[typecheck]"` resolves.

## Commit

One commit, message suggestion:
`Add typecheck extra to pyproject.toml (#168)`

---

## LLM Prompt

> Implement **Step 1** as described in `pr_info/steps/step_1.md`. First read
> `pr_info/steps/summary.md` for context, then read this step file. Add the
> `typecheck = ["mypy>=1.13.0", "types-requests>=2.31.0"]` line to the
> `[project.optional-dependencies]` section of `pyproject.toml`, placed
> immediately after the `dev = [...]` block. Do not modify any other entry.
> After editing, run the verification one-liner from this file, then run all
> three MCP code-quality checks (`pylint`, `pytest` with the integration-test
> exclusions from `CLAUDE.md`, and `mypy`). All three must pass. Make a single
> commit with message `Add typecheck extra to pyproject.toml (#168)`.
