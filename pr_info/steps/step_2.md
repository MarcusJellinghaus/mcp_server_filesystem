# Step 2 — Create `.github/workflows/upstream-mypy-check.yml`

> See [`summary.md`](./summary.md) for context. **Depends on step 1** — this
> workflow installs `.[typecheck]`.

## WHERE

- **File:** `.github/workflows/upstream-mypy-check.yml` (new).
- **Sibling files for reference:** existing `.github/workflows/ci.yml` (mypy
  matrix entry uses identical invocation).

## WHAT

A GitHub Actions workflow that:

1. Triggers on `repository_dispatch` of type `upstream-main-updated` (sent by
   `mcp-coder-utils` after its issue #28 ships) **and** on `workflow_dispatch`
   for manual runs.
2. Installs `mcp-coder-utils` from `git+main`, then installs this repo with the
   `[typecheck]` extra (order is load-bearing — see summary).
3. Runs `mypy --strict src tests`.

## HOW

- Pinned action versions: `actions/checkout@v6`, `astral-sh/setup-uv@v8`,
  `actions/setup-python@v6`. These match step 4's bump of `ci.yml`.
- `python-version: "3.11"` (quoted — avoids YAML float parsing turning `3.10`
  into `3.1`; matches existing `ci.yml` convention).
- Job name templated on the trigger source so the Actions tab shows which
  upstream caused the run:
  `mypy-against-upstream-${{ github.event.client_payload.upstream || github.event.inputs.upstream }}`.
- `permissions: contents: read` — minimum needed for checkout.
- The `workflow_dispatch` input `upstream` (default `'manual'`) drives the job
  name when triggered manually.

## ALGORITHM

```
on repository_dispatch[upstream-main-updated] OR workflow_dispatch:
  checkout this repo at HEAD
  setup uv + python 3.11
  uv pip install --system "mcp-coder-utils @ git+https://.../mcp-coder-utils.git"
  uv pip install --system ".[typecheck]"   # bare 'mcp-coder-utils' stays satisfied
  mypy --strict src tests
```

## DATA

Full file contents (copy verbatim from issue #168, section "3."):

```yaml
name: Upstream mypy check

# Triggered by repository_dispatch when mcp-coder-utils' main branch changes.
# Runs mypy --strict against this repo with the latest mcp-coder-utils from main.
# On failure: standard GitHub Actions email + red icon in the Actions tab.

on:
  repository_dispatch:
    types: [upstream-main-updated]
  workflow_dispatch:
    inputs:
      upstream:
        description: 'Upstream that triggered this run (shown in the job name)'
        required: false
        default: 'manual'

permissions:
  contents: read

jobs:
  mypy-against-upstream-main:
    name: mypy-against-upstream-${{ github.event.client_payload.upstream || github.event.inputs.upstream }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v8
      - uses: actions/setup-python@v6
        with:
          python-version: "3.11"

      - name: Install mcp-coder-utils from main
        run: uv pip install --system "mcp-coder-utils @ git+https://github.com/MarcusJellinghaus/mcp-coder-utils.git"

      - name: Install mcp-workspace with typecheck extra
        run: uv pip install --system ".[typecheck]"

      - name: Run mypy --strict
        run: mypy --strict src tests
```

## Verification (TDD-equivalent for config)

1. **YAML parse + structure check:**

   ```bash
   python -c "import yaml; \
     d = yaml.safe_load(open('.github/workflows/upstream-mypy-check.yml')); \
     assert d['name'] == 'Upstream mypy check'; \
     assert 'repository_dispatch' in d[True]; \
     assert d[True]['repository_dispatch']['types'] == ['upstream-main-updated']; \
     assert 'workflow_dispatch' in d[True]; \
     steps = d['jobs']['mypy-against-upstream-main']['steps']; \
     uses = [s.get('uses','') for s in steps]; \
     assert 'actions/checkout@v6' in uses; \
     assert 'astral-sh/setup-uv@v8' in uses; \
     assert any(u.startswith('actions/setup-python@v6') for u in uses); \
     print('OK')"
   ```

   Note: PyYAML parses the `on:` key as Python `True`; that's expected and
   harmless for verification.

2. **Regression** — run `pylint`, `pytest` (with integration-test exclusions),
   and `mypy` MCP checks. All must pass.

3. **(Operational, post-merge)** Trigger via Actions tab → "Upstream mypy
   check" → "Run workflow" → leave `upstream` default. Confirm mypy runs to
   completion (success or expected failure — both are acceptable signals).

## Commit

One commit, message suggestion:
`Add upstream-mypy-check workflow for cross-repo signal (#168)`

---

## LLM Prompt

> Implement **Step 2** as described in `pr_info/steps/step_2.md`. First read
> `pr_info/steps/summary.md`, then this step file. Verify step 1 has already
> shipped (`grep -A1 typecheck pyproject.toml`). Create the new file
> `.github/workflows/upstream-mypy-check.yml` with **exactly** the YAML body in
> the DATA section of this step (copied verbatim from issue #168). Do not
> reorder the install steps — the order is load-bearing. Run the YAML parse
> verification one-liner, then run all three MCP code-quality checks (`pylint`,
> `pytest` with the integration-test exclusions from `CLAUDE.md`, and `mypy`).
> All three must pass. Make a single commit with message
> `Add upstream-mypy-check workflow for cross-repo signal (#168)`.
