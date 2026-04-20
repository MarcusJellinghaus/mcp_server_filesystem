# Step 1: Split matrix entry and add GitHub integration job

> **Reference**: See [summary.md](summary.md) for full context (Issue #106).

## Goal

Modify `.github/workflows/ci.yml` to:
1. Change the existing `integration-tests` matrix entry to only run `git_integration` (rename to `git-integration-tests`)
2. Add a new standalone `github-integration-tests` job with secret guards

## WHERE

- `.github/workflows/ci.yml`

## WHAT — Change 1: Modify matrix entry

In the `test` job matrix, replace:
```yaml
- {name: "integration-tests", cmd: "pytest --version && pytest -n auto -m 'git_integration or github_integration'"}
```
with:
```yaml
- {name: "git-integration-tests", cmd: "pytest --version && pytest -n auto -m 'git_integration'"}
```

## WHAT — Change 2: Add new job

Add a new top-level job `github-integration-tests` after the `test` job with:

- **`if:` guard**: `${{ secrets.GH_INTEGRATION_TOKEN != '' && secrets.GITHUB_TEST_REPO_URL != '' }}`
- **`env:` block**: Maps `GH_INTEGRATION_TOKEN` → `GITHUB_TOKEN` and `GITHUB_TEST_REPO_URL` → `GITHUB_TEST_REPO_URL`
- **Setup steps**: Same as `test` job (checkout, uv, python 3.11, install deps, env info)
- **Info step**: Prints configuration status without leaking the token
- **Test step**: Runs `pytest -n auto -m 'github_integration'`
- **No `needs:`**: Runs in parallel with other jobs

### New job YAML

```yaml
  github-integration-tests:
    runs-on: ubuntu-latest
    if: ${{ secrets.GH_INTEGRATION_TOKEN != '' && secrets.GITHUB_TEST_REPO_URL != '' }}
    name: github-integration-tests
    env:
      GITHUB_TOKEN: ${{ secrets.GH_INTEGRATION_TOKEN }}
      GITHUB_TEST_REPO_URL: ${{ secrets.GITHUB_TEST_REPO_URL }}
    steps:
      - uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: uv pip install --system -e ".[dev]"

      - name: Environment info
        run: |
          uname -a
          python --version
          uv --version
          git --version

      - name: Integration test configuration
        run: |
          echo "✅ GitHub integration tests enabled"
          echo "  Token: configured (GH_INTEGRATION_TOKEN)"
          echo "  Test repo: $GITHUB_TEST_REPO_URL"

      - name: Run github-integration-tests
        run: pytest --version && pytest -n auto -m 'github_integration'
```

## DATA

No data structures — YAML configuration only.

## Verification

- Review the YAML for syntax correctness
- Confirm `git_integration` matrix entry no longer references `github_integration`
- Confirm new job has both secret guards in `if:`
- Confirm `env` block maps secrets to expected env var names

## Commit

```
ci: configure GitHub integration tests as dedicated job (#106)

- Rename matrix entry to 'git-integration-tests' (git_integration only)
- Add standalone 'github-integration-tests' job with secret guards
- Job skips when GH_INTEGRATION_TOKEN or GITHUB_TEST_REPO_URL missing
- Secrets isolated to the job that needs them (least privilege)
```

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md, then implement step 1.

Modify .github/workflows/ci.yml with two changes:
1. In the test job matrix, change the integration-tests entry to only run git_integration marker (rename to git-integration-tests)
2. Add a new standalone github-integration-tests job with secret guards as specified in step_1.md

After editing, verify the YAML structure is correct. No Python code changes needed — skip pylint/mypy/pytest checks as this is YAML-only.
```
