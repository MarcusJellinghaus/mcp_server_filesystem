# Step 2: `reference_projects.py` — Dataclass, URL Normalizer, URL Verifier

## LLM Prompt

> Implement Step 2 of Issue #92. See `pr_info/steps/summary.md` for full context.
> Create the new `reference_projects.py` module with dataclass, URL normalizer, and URL verifier. TDD approach.
> Run all code quality checks (pylint, pytest, mypy) after changes. Commit: `feat(ref-projects): add ReferenceProject dataclass, URL normalizer and verifier`

## WHERE

- **Tests:** `tests/test_reference_projects.py` (add new test classes — keep existing classes intact for now)
- **Implementation:** `src/mcp_workspace/reference_projects.py` (new file)

## WHAT

### `ReferenceProject` dataclass

```python
@dataclass
class ReferenceProject:
    name: str
    path: Path
    url: Optional[str] = None
```

### `normalize_git_url(url: str) -> str`

General URL normalizer for mismatch detection. Works with any git host.

```
def normalize_git_url(url: str) -> str:
    url = url.strip()
    match SSH pattern (git@host:org/repo.git) → convert to https://host/org/repo
    strip trailing ".git"
    strip trailing "/"
    lowercase the host portion
    return normalized
```

**SSH regex:** `r'^git@([^:]+):(.+)$'` → `https://{host}/{path}`

### `verify_url_match(explicit_url: str, detected_url: str) -> None`

Compares two URLs after normalization. Raises on mismatch.

```
def verify_url_match(explicit_url: str, detected_url: str, project_name: str) -> None:
    if normalize_git_url(explicit_url) != normalize_git_url(detected_url):
        raise ValueError(f"URL mismatch for '{project_name}': ...")
```

### `detect_and_verify_url(path: Path, explicit_url: Optional[str], project_name: str) -> Optional[str]`

Detect URL from git repo and/or verify against explicit URL. Returns the resolved URL (explicit or auto-detected), or None. Raises ValueError if explicit URL doesn't match detected URL.

```
def detect_and_verify_url(path: Path, explicit_url: Optional[str], project_name: str) -> Optional[str]:
    from mcp_workspace.git_operations.remotes import get_remote_url
    if explicit_url and path.exists() and is_git_repository(path):
        detected = get_remote_url(path)
        if detected:
            verify_url_match(explicit_url, detected, project_name)
        return explicit_url
    if explicit_url and (not path.exists() or not is_git_repository(path)):
        return explicit_url  # will be used for lazy cloning
    if not explicit_url and path.exists() and is_git_repository(path):
        return get_remote_url(path)  # auto-detect, may be None
    return None  # no explicit URL, path doesn't exist or not a git repo
```

**Note:** `is_git_repository` is imported from `mcp_workspace.git_operations.core`. The `get_remote_url` import is deferred (inside function body) to keep module-level imports minimal until Step 3 adds `git_operations` imports.

## HOW

- New file at `src/mcp_workspace/reference_projects.py`
- Imports: `dataclasses.dataclass`, `pathlib.Path`, `typing.Optional`, `re`, `logging`
- `detect_and_verify_url` imports `get_remote_url` locally (deferred import) and `is_git_repository` from `git_operations.core`
- `normalize_git_url` is a pure function — no I/O, easy to test

## DATA

```python
# normalize_git_url examples:
"git@github.com:org/repo.git"     → "https://github.com/org/repo"
"https://GitHub.com/org/repo.git" → "https://github.com/org/repo"
"https://github.com/org/repo/"    → "https://github.com/org/repo"
"git@gitlab.self-hosted.com:team/project.git" → "https://gitlab.self-hosted.com/team/project"

# verify_url_match:
# Returns None on match, raises ValueError on mismatch
```

## TESTS

New test classes in `tests/test_reference_projects.py`:

### `TestReferenceProjectDataclass`
- `test_create_with_defaults` — name + path only, url is None
- `test_create_with_url` — all fields set
- `test_path_is_path_object` — path stored as Path

### `TestNormalizeGitUrl`
- `test_ssh_to_https` — `git@github.com:org/repo.git` → `https://github.com/org/repo`
- `test_https_strip_dotgit` — `https://github.com/org/repo.git` → strip .git
- `test_strip_trailing_slash` — trailing `/` removed
- `test_lowercase_host` — `GitHub.COM` → `github.com`
- `test_ssh_non_github` — `git@gitlab.example.com:team/proj.git` → works
- `test_https_already_clean` — clean URL passes through unchanged
- `test_ssh_nested_path` — `git@host:org/sub/repo.git` → preserves path

### `TestVerifyUrlMatch`
- `test_matching_urls_no_error` — SSH vs HTTPS for same repo → no exception
- `test_mismatching_urls_raises` — different repos → ValueError
- `test_mismatch_error_includes_project_name` — error message contains project name

### `TestDetectAndVerifyUrl`

Mock `get_remote_url` and `is_git_repository` from `git_operations` in all tests.

- `test_detect_explicit_url_matches_remote` — explicit URL provided, path exists, is git repo, remote matches → returns explicit URL, no error
- `test_detect_explicit_url_mismatch` — explicit URL provided, path exists, is git repo, remote differs → raises ValueError
- `test_detect_auto_from_git` — no explicit URL, path exists, is git repo → returns auto-detected URL
- `test_detect_no_url_no_git` — no explicit URL, path doesn't exist → returns None
- `test_detect_explicit_url_path_missing` — explicit URL provided, path doesn't exist → returns explicit URL (for lazy cloning)
