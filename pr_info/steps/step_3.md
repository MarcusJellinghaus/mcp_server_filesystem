# Step 3 — Create `.github/workflows/notify-downstream.yml`

> See [`summary.md`](./summary.md) for context. **Independent** of steps 1, 2, 4.

## WHERE

- **File:** `.github/workflows/notify-downstream.yml` (new).
- **External dependency:** repo secret `DOWNSTREAM_PAT` (set out-of-band by repo
  maintainer; see summary).

## WHAT

A GitHub Actions workflow that fires on every push to this repo's `main`
(and on `workflow_dispatch`) and sends a `repository_dispatch` event of type
`upstream-main-updated` to `MarcusJellinghaus/mcp_coder` with payload
`{"upstream": "mcp-workspace", "sha": "<this commit sha>"}`.

## HOW

- Uses third-party action `peter-evans/repository-dispatch@v3` (the canonical
  action for cross-repo dispatch from GitHub Actions).
- Token: `${{ secrets.DOWNSTREAM_PAT }}` — fine-grained PAT with
  `Contents: Read & write` on `mcp_coder` and `Metadata: Read`.
- No path filter, no concurrency block — per the issue's Decisions table:
  push frequency to `main` is low; downstream mypy is idempotent; dispatch is
  cheap.
- No matching action-version bump needed elsewhere.

## ALGORITHM

```
on push[main] OR workflow_dispatch:
  send repository_dispatch event
    target  = MarcusJellinghaus/mcp_coder
    type    = upstream-main-updated
    payload = {upstream: "mcp-workspace", sha: <this commit sha>}
```

## DATA

Full file contents (copy verbatim from issue #168, section "2."):

```yaml
name: Notify downstream of main update

# When this repo's main changes, send a repository_dispatch event to mcp_coder
# so it can re-run mypy against the latest main of this package.
#
# Requires repo secret DOWNSTREAM_PAT — a fine-grained PAT with
#   Contents: Read & write   (on the target repo, mcp_coder)
#   Metadata: Read
# Create at: https://github.com/settings/personal-access-tokens/new
# Add to this repo via: Settings → Secrets and variables → Actions → New repository secret.

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  dispatch-to-mcp-coder:
    name: dispatch-to-mcp_coder
    runs-on: ubuntu-latest
    steps:
      - name: Send upstream-main-updated to mcp_coder
        uses: peter-evans/repository-dispatch@v3
        with:
          token: ${{ secrets.DOWNSTREAM_PAT }}
          repository: MarcusJellinghaus/mcp_coder
          event-type: upstream-main-updated
          client-payload: '{"upstream": "mcp-workspace", "sha": "${{ github.sha }}"}'
```

## Verification (TDD-equivalent for config)

1. **YAML parse + structure check:**

   ```bash
   python -c "from pathlib import Path; import json, yaml; \
     assert Path('.github/workflows/notify-downstream.yml').is_file(); \
     d = yaml.safe_load(open('.github/workflows/notify-downstream.yml')); \
     assert d['name'] == 'Notify downstream of main update'; \
     assert d[True]['push']['branches'] == ['main']; \
     assert 'workflow_dispatch' in d[True]; \
     step = d['jobs']['dispatch-to-mcp-coder']['steps'][0]; \
     assert step['uses'] == 'peter-evans/repository-dispatch@v3'; \
     w = step['with']; \
     assert w['repository'] == 'MarcusJellinghaus/mcp_coder'; \
     assert w['event-type'] == 'upstream-main-updated'; \
     payload = json.loads(w['client-payload'].replace('\${{ github.sha }}', 'SHA_PLACEHOLDER')); \
     assert isinstance(payload, dict) and 'upstream' in payload and 'sha' in payload; \
     assert payload['upstream'] == 'mcp-workspace'; \
     print('OK')"
   ```

2. **Regression** — run `pylint`, `pytest` (with integration-test exclusions),
   and `mypy` MCP checks. All must pass.

3. **(Operational, post-merge)**: a push to `main` should produce a
   `Notify downstream of main update` run in this repo's Actions tab AND a
   corresponding `repository_dispatch` run in `mcp_coder`'s Actions tab
   (assuming `DOWNSTREAM_PAT` is set).

## Commit

One commit, message suggestion:
`Add notify-downstream workflow to fan out main-branch updates (#168)`

---

## LLM Prompt

> Implement **Step 3** as described in `pr_info/steps/step_3.md`. First read
> `pr_info/steps/summary.md`, then this step file. Create the new file
> `.github/workflows/notify-downstream.yml` with **exactly** the YAML body in
> the DATA section of this step (copied verbatim from issue #168). Do not add
> a `concurrency` block or path filter — both are explicitly rejected in the
> issue's Decisions table. Run the YAML parse verification one-liner, then run
> all three MCP code-quality checks (`pylint`, `pytest` with the
> integration-test exclusions from `CLAUDE.md`, and `mypy`). All three must
> pass. Make a single commit with message
> `Add notify-downstream workflow to fan out main-branch updates (#168)`.
