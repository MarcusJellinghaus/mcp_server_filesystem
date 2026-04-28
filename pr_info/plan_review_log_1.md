# Plan Review Log 1

**Issue**: #169
**Date started**: 2026-04-28
**Branch**: 169-ghe-cloud-ghe-com-support-fix-api-url-shape-add-truststore-for-corporate-proxies

## Round 1 — 2026-04-28

**Findings**:
- Critical 1.1: `tach.toml` / `.importlinter` change framed as conditional, but predictably required for new `_ssl` module
- Critical 1.2: Step 3 wiring test had multiple options requiring brittle patching
- Improvement 2.1: Missing test that `_ssl` module does not activate at import time
- Improvement 2.2: Missing assertion that `RepoIdentifier.api_base_url` propagates `*.ghe.com` correctly
- Improvement 2.3: `_ssl.py` only caught `ImportError`; broad failures could crash the server
- Improvement 2.4: New URL tests not parameterized
- Improvement 2.5: Step 1 docstring update underspecified
- Improvement 2.6: tach `[[modules]] path = "tests"` block needed confirmation re `_ssl` import
- Improvement 2.7: Out-of-scope list did not mention `BaseGitHubManager` integration test
- Question 3.1: How should `ensure_truststore()` handle `inject_into_ssl()` failure? (silent vs crash)
- Question 3.2: Should wiring test assert ordering vs lazy `run_server` import?
- Question 3.3: Confirm one-PR vs split

**Decisions**:
- 1.1, 1.2, 2.1, 2.2, 2.4, 2.5, 2.6, 2.7: accept — apply
- 2.3: defer to user answer on 3.1
- 3.1: ask user
- 3.2: accept — issue says "before any GitHub work"; add assertion
- 3.3: skip — issue text already specifies one PR

**User decisions**:
- 3.1: Option A — silent warn-and-continue. A corporate-proxy environment failing truststore activation must not take down the MCP server (PyGithub falls back to certifi).

**Changes**:
- `pr_info/steps/summary.md`: tach/importlinter edits marked mandatory (split across steps 2/3); added "Out of Scope" bullet for `BaseGitHubManager` E2E test
- `pr_info/steps/step_1.md`: target docstring text spelled out for all three hostname patterns; `pytest.parametrize` suggestion added; `RepoIdentifier.api_base_url` propagation assertion added
- `pr_info/steps/step_2.md`: tach `[[modules]]` block + `.importlinter` bottom row diffs made mandatory; `tests` block note (`exact = false` covers it); ALGORITHM extended with broad `except Exception` warn-and-continue; added `test_import_does_not_activate` and `test_inject_failure_does_not_raise`; quality gates now include tach + lint-imports
- `pr_info/steps/step_3.md`: `mcp_workspace.main.depends_on` += `_ssl` diff added; wiring test simplified to single approach using shared `parent = Mock()` + `mock_calls.index(...)` ordering (covers `setup_logging < ensure_truststore < run_server`); Option B dropped

**Status**: pending commit


## Round 2 — 2026-04-28

**Findings**:
- No critical findings
- Improvement: `_activated` flag in `_ssl.py` ALGORITHM needed `global` declaration (idempotency test would otherwise fail)
- Improvement: pyproject.toml insertion position underspecified
- Improvement: step 3 wiring test — clarify `--reference-project` not passed (default `None` skips that branch)
- Improvement: tach.toml `tests` block conditional addition of `_ssl` should be mandatory for consistency with surrounding entries
- No questions for user

**Decisions**:
- All four improvements: accept — apply

**User decisions**: none needed this round

**Changes**:
- `pr_info/steps/step_2.md`: added `global _activated` declaration to ALGORITHM pseudocode; pyproject.toml diff made concrete (truststore appended to `dependencies` after `PyGithub>=1.59.0`, bare/unpinned); tach.toml `tests` depends_on update made mandatory with concrete diff
- `pr_info/steps/step_3.md`: added note that wiring test argv excludes `--reference-project`

**Status**: pending commit
