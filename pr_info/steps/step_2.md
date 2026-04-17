# Step 2: Add Infrastructure Files (config.py, constants.py, utils/timezone_utils.py)

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. This is step 2 of 5 for issue #104.
>
> **Task:** Create three infrastructure files that `github_operations` will depend on: `config.py` (token/repo resolution), `constants.py` (duplicate protection constant), and `utils/timezone_utils.py` (timezone utility). Write tests first (TDD), then implement.
>
> **Source:** `config.py` is hand-written per the issue spec. `constants.py` and `timezone_utils.py` are copied from `mcp_coder` (use `get_library_source` to read from the installed package). These files are utilities-layer — no tool-layer dependencies.

## WHERE

### New source files

```
src/mcp_workspace/config.py               ← ~30 lines
src/mcp_workspace/constants.py             ← ~5 lines
src/mcp_workspace/utils/__init__.py        ← empty package init
src/mcp_workspace/utils/timezone_utils.py  ← copied from mcp_coder
```

### New test files

```
tests/test_config.py                       ← tests for config.py
tests/test_constants.py                    ← tests for constants.py
tests/utils/__init__.py                    ← test package init
tests/utils/test_timezone_utils.py         �� tests for timezone_utils.py
```

## WHAT

### `config.py` — Two public functions, one private helper

```python
def _read_config_value(section: str, key: str) -> str | None:
    """Read a value from ~/.mcp_coder/config.toml."""
    # Path: Path.home() / ".mcp_coder" / "config.toml"
    # Parse with tomllib (Python 3.11+)
    # Return config[section][key] or None on any error

def get_github_token() -> str | None:
    """Env var GITHUB_TOKEN → ~/.mcp_coder/config.toml [github].token → None."""

def get_test_repo_url() -> str | None:
    """Env var GITHUB_TEST_REPO_URL → ~/.mcp_coder/config.toml [github].test_repo_url → None."""
```

### `constants.py` — Single constant

```python
DUPLICATE_PROTECTION_SECONDS: int = 60  # Value from mcp_coder.constants
```

### `utils/timezone_utils.py` — Copied from mcp_coder

Read source from `mcp_coder.utils.timezone_utils` using `get_library_source`. Copy as-is, only adjusting imports if needed (likely none — timezone_utils uses only stdlib).

## HOW

### config.py algorithm

```python
def get_github_token():
    token = os.environ.get("GITHUB_TOKEN")
    if token: return token
    token = _read_config_value("github", "token")
    if token: return token
    return None

def _read_config_value(section, key):
    config_path = Path.home() / ".mcp_coder" / "config.toml"
    if not config_path.exists(): return None
    data = tomllib.loads(config_path.read_text())
    return data.get(section, {}).get(key)
```

### Test approach

**`test_config.py`:**
- Test `get_github_token()` returns env var when set (mock `os.environ`)
- Test `get_github_token()` falls back to config file (mock `Path.home()`, write temp toml)
- Test `get_github_token()` returns `None` when neither source available
- Same three tests for `get_test_repo_url()`
- Test `_read_config_value()` with missing file, malformed toml, missing section/key

**`test_constants.py`:**
- Test `DUPLICATE_PROTECTION_SECONDS` is an int > 0

**`test_timezone_utils.py`:**
- Copy/adapt tests from `mcp_coder` (use `get_library_source` to read them)

## DATA

### Return values

| Function | Returns |
|----------|---------|
| `get_github_token()` | `str \| None` |
| `get_test_repo_url()` | `str \| None` |
| `_read_config_value(section, key)` | `str \| None` |
| `DUPLICATE_PROTECTION_SECONDS` | `int` (value: 60) |

### Config file format (for reference, not created by us)

```toml
[github]
token = "ghp_..."
test_repo_url = "https://github.com/owner/repo"
```

## Verification

```
pylint, mypy, pytest (unit tests only — exclude integration markers)
```
