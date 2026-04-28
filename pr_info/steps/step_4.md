# Step 4 — Bump action versions in `.github/workflows/ci.yml`

> See [`summary.md`](./summary.md) for context. **Independent** of steps 1, 2, 3.

## WHERE

- **File:** `.github/workflows/ci.yml` (modify only).

## WHAT

Update GitHub Action version pins in the existing CI workflow so the entire
repo runs one toolchain (matches the new workflows from steps 2 & 3):

| Action | Old | New | Occurrences |
|---|---|---|---|
| `astral-sh/setup-uv` | `@v4` | `@v8` | 4 (in jobs `test`, `github-integration-tests`, `file-size`, `architecture`) |
| `actions/setup-python` | `@v5` | `@v6` | 3 (in jobs `test`, `github-integration-tests`, `architecture` — `file-size` does not use `setup-python`) |
| `actions/checkout` | `@v6` | `@v6` | already current — **no change** |

That is exactly **7 line changes**, all simple version-pin substitutions. No
restructuring, no logic changes, no new jobs.

## HOW

Two `replace_all` edits via `mcp__workspace__edit_file`:

1. Replace `astral-sh/setup-uv@v4` → `astral-sh/setup-uv@v8` (replace_all).
2. Replace `actions/setup-python@v5` → `actions/setup-python@v6` (replace_all).

After each edit, verify the diff shows exactly the expected number of
substitutions (4 and 3 respectively).

## ALGORITHM

n/a — pure version-pin substitution.

## DATA

Before / after grep snapshots (one occurrence shown for each action; all
occurrences receive the same substitution):

```diff
-      - name: Install uv
-        uses: astral-sh/setup-uv@v4
+      - name: Install uv
+        uses: astral-sh/setup-uv@v8

-      - uses: actions/setup-python@v5
+      - uses: actions/setup-python@v6
         with:
           python-version: "3.11"
```

## Verification (TDD-equivalent for config)

1. **Substitution-count check:**

   ```bash
   grep -c 'astral-sh/setup-uv@v8' .github/workflows/ci.yml      # expect 4
   grep -c 'actions/setup-python@v6' .github/workflows/ci.yml    # expect 3
   grep -c 'astral-sh/setup-uv@v4' .github/workflows/ci.yml      # expect 0
   grep -c 'actions/setup-python@v5' .github/workflows/ci.yml    # expect 0
   ```

2. **YAML parse check** (catches accidental indentation breakage):

   ```bash
   python -c "import yaml; \
     yaml.safe_load(open('.github/workflows/ci.yml')); \
     print('OK')"
   ```

3. **Regression** — run `pylint`, `pytest` (with integration-test exclusions),
   and `mypy` MCP checks. All must pass.

4. **(Operational, post-merge)** Next CI run on this repo uses the bumped
   actions; check the Actions tab for "Set up uv 8.x" / "Set up Python 3.11"
   step labels.

## Commit

One commit, message suggestion:
`Bump setup-uv to v8 and setup-python to v6 in ci.yml (#168)`

---

## LLM Prompt

> Implement **Step 4** as described in `pr_info/steps/step_4.md`. First read
> `pr_info/steps/summary.md`, then this step file. Use
> `mcp__workspace__edit_file` with `replace_all=True` to perform exactly two
> substitutions in `.github/workflows/ci.yml`:
>
>   1. `astral-sh/setup-uv@v4` → `astral-sh/setup-uv@v8` (4 occurrences)
>   2. `actions/setup-python@v5` → `actions/setup-python@v6` (3 occurrences)
>
> Do not change `actions/checkout@v6` — it is already current. Do not modify
> any other line. Run the substitution-count and YAML-parse verification
> one-liners from this file, then run all three MCP code-quality checks
> (`pylint`, `pytest` with the integration-test exclusions from `CLAUDE.md`,
> and `mypy`). All three must pass. Make a single commit with message
> `Bump setup-uv to v8 and setup-python to v6 in ci.yml (#168)`.
