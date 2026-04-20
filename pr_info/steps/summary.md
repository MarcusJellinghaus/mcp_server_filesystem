# Issue #106: Configure GitHub integration test secrets for CI

## Summary

Modify the CI workflow so that GitHub integration tests (`@pytest.mark.github_integration`) run as a **dedicated job** with proper secret management, separate from the existing test matrix. The `git_integration` tests remain in the matrix as a standalone entry (no secrets needed).

## Architectural / Design Changes

- **Secret isolation via separate job**: GitHub integration tests move from the shared `test` matrix to a standalone `github-integration-tests` job. This follows the principle of least privilege — secrets (`GH_INTEGRATION_TOKEN`, `GITHUB_TEST_REPO_URL`) are only exposed to the job that needs them, not to pylint/mypy/unit-tests/etc.
- **Graceful degradation for forks**: The new job uses a GitHub Actions `if:` guard on both secrets. When secrets aren't configured (forks, new contributors), the job is skipped at the Actions level (greyed out in UI) rather than running and producing misleading green results.
- **No Python code changes**: This is purely a CI configuration change.

## Files Modified

| File | Change |
|------|--------|
| `.github/workflows/ci.yml` | Rename matrix entry `integration-tests` → `git-integration-tests` with only `git_integration` marker; add new standalone `github-integration-tests` job with secret guards |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| [Step 1](step_1.md) | Split matrix entry and add GitHub integration job | `ci: configure GitHub integration tests as dedicated job (#106)` |

## Constraints

- No TDD applicable — this is a YAML-only CI configuration change with no Python code
- The repo owner must separately create the two repository secrets (`GH_INTEGRATION_TOKEN`, `GITHUB_TEST_REPO_URL`) — that is a manual step outside this PR
