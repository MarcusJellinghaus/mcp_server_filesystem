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

## HOW

- New file at `src/mcp_workspace/reference_projects.py`
- Imports: `dataclasses.dataclass`, `pathlib.Path`, `typing.Optional`, `re`, `logging`
- No imports from `git_operations` yet (that comes in Step 3)
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
