# Step 2 — Add `token_fingerprint.py` utility

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 2 only: create
> `src/mcp_workspace/utils/token_fingerprint.py` with the
> `format_token_fingerprint()` pure function, plus tests in
> `tests/utils/test_token_fingerprint.py`. Follow TDD: write the tests first,
> then the module. Include a strict negative test that asserts the raw token
> never appears anywhere in the returned string. Run
> `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`, and
> `mcp__tools-py__run_pytest_check` (with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`)
> until all pass. Commit with message:
> `feat(utils): add token_fingerprint formatter for redacted token logs`.

## WHERE

- **Create**: `src/mcp_workspace/utils/token_fingerprint.py`
- **Create**: `tests/utils/test_token_fingerprint.py`

## WHAT

```python
def format_token_fingerprint(token: str) -> str:
    """Return '<prefix>...XXXX, len=N' for known/unknown families.

    Malformed tokens (len < 8) return '<malformed>, len=N' with no token
    characters exposed.
    """
```

## HOW

- Pure function, no I/O, no logging.
- No imports outside stdlib.
- Lives in `mcp_workspace.utils` (leaf layer per `tach.toml`). Not exported via `utils/__init__.py` — direct module imports only.

## ALGORITHM

```
KNOWN = ("github_pat_", "ghp_", "gho_", "ghu_", "ghs_", "ghr_")  # check longest first
N = len(token)
if N < 8: return f"<malformed>, len={N}"
prefix = first matching KNOWN family, else token[:4] + "_"
return f"{prefix}...{token[-4:]}, len={N}"
```

## DATA

- Input: any `str`
- Output: `str` of the form `<prefix>...XXXX, len=N` or `<malformed>, len=N`

## Tests (write first)

- Classic PAT (`ghp_` + 36 chars) → `ghp_...{last4}, len=40`
- Fine-grained PAT (`github_pat_` + 82 chars) → `github_pat_...{last4}, len=93`
- Other known families: `gho_`, `ghu_`, `ghs_`, `ghr_`
- Unknown family (e.g. `abcd1234...`) → `abcd_...{last4}, len=N`
- Empty string → `<malformed>, len=0`
- Length 7 → `<malformed>, len=7` (boundary)
- Length 8 with unknown prefix → uses `<first4>_` form (boundary, not malformed)
- **Strict negative**: for a token like `ghp_SECRET_MIDDLE_PART_ABC123xyz789a3f9`, the substring `SECRET_MIDDLE_PART` must NOT appear in the returned fingerprint
- **Strict negative**: for malformed input `"abc"`, no character of `"abc"` appears in output
