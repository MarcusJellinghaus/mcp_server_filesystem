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

## Motivation

A simple prefix+suffix shape (`abcd...wxyz`) was chosen over a SHA-256 +
GitHub-family-prefix design because:

- It aligns with the existing redaction helper `_mask_api_key` in
  `p_coder/src/mcp_coder/llm/providers/langchain/verification.py:36`.
- The same shape is the proposed upstream API at
  [mcp-coder-utils#30](https://github.com/MarcusJellinghaus/mcp-coder-utils/issues/30),
  which will eventually replace this local helper.
- Operator recognition is the primary use case: a tail like `...a3f9` lets a
  human recognize the token in support contexts. GitHub's UI itself displays
  the last-4 publicly, so leaking it is consistent with established practice.
- No hashing, no family allow-list, no `len=N` suffix — just the minimum needed
  to make logs operator-readable while keeping the secret middle hidden.

## WHERE

- **Create**: `src/mcp_workspace/utils/token_fingerprint.py`
- **Create**: `tests/utils/test_token_fingerprint.py`

## WHAT

```python
def format_token_fingerprint(token: str | None) -> str:
    """Return '<first4>...<last4>' for tokens longer than 8 characters.

    For short tokens (1..=8 characters) returns '****' so no characters of the
    secret leak. For empty or None input returns '' (the consumer omits the
    field when empty — see step 7).
    """
```

## HOW

- Pure function, no I/O, no logging.
- No imports outside stdlib.
- No `hashlib` use.
- Lives in `mcp_workspace.utils` (leaf layer per `tach.toml`). Not exported via
  `utils/__init__.py` — direct module imports only.

## ALGORITHM

```
if not token:           # None or empty string
    return ""
if len(token) > 8:
    return f"{token[:4]}...{token[-4:]}"
return "****"           # 1 <= len <= 8
```

## DATA

- Input: `str | None`
- Output: `str`
  - empty/None → `""`
  - length 1–8 → `"****"`
  - length > 8 → `"<first4>...<last4>"`

## Tests (write first)

- Classic PAT (`ghp_` + 36 chars, total len 40) → `"ghp_...{last4}"`
- Fine-grained PAT (`github_pat_` + 82 chars, total len 93) → `"gith...{last4}"`
- Generic long token (40 hex chars) → `"<first4>...<last4>"`
- Length 9 (boundary, just over threshold) → `"<first4>...<last4>"`
- Length 8 (boundary) → `"****"`
- Length 1 → `"****"`
- Empty string `""` → `""`
- `None` → `""`
- **Strict negative**: for a token like `ghp_SECRET_MIDDLE_PART_ABC123xyz789a3f9`,
  the substring `SECRET_MIDDLE_PART` must NOT appear anywhere in the returned
  fingerprint. (This is the load-bearing assertion that proves the helper does
  not leak the raw token's middle.)
- **Strict negative**: for short input `"abcdefgh"` (len 8), the output is
  exactly `"****"` — none of `"abcdefgh"` appears in the output.
