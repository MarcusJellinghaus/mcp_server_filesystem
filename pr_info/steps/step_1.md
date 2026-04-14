# Step 1: Add read_github_deps.py with tests

> **Context**: See [summary.md](summary.md) for full issue context (#94).

## Commit Message
```
feat: add read_github_deps.py with tests
```

## Overview
Create the `tools/read_github_deps.py` helper (verbatim copy from `p_mcp_utils` reference) and its test file. This script reads `[tool.mcp-coder.install-from-github]` from `pyproject.toml` and prints `uv pip install` commands — used by `reinstall_local.bat` in Step 2.

## Files

### CREATE: `tools/read_github_deps.py`
- **Copy verbatim** from reference project `p_mcp_utils` at `tools/read_github_deps.py`
- Self-contained: only uses `tomllib` and `pathlib` (stdlib)
- No modifications needed

**Function signature:**
```python
def main() -> None:
```

> **Note:** `main()` resolves the project directory from `__file__` (parent of the script's directory). Tests need to handle this — e.g., run as subprocess in a temp dir, or monkeypatch path resolution.

**Algorithm:**
```
1. Resolve project_dir (default: parent of script's directory)
2. Read pyproject.toml with tomllib
3. Extract tool.mcp-coder.install-from-github config
4. Print "uv pip install <quoted-packages>" for 'packages' key
5. Print "uv pip install --no-deps <quoted-packages>" for 'packages-no-deps' key
```

**Data — Output format** (stdout, one command per line):
```
uv pip install "pkg-a @ git+https://..." "pkg-b @ git+https://..."
uv pip install --no-deps "pkg-c @ git+https://..."
```

### CREATE: `tests/test_read_github_deps.py`
- **Written from scratch** (no reference test file exists to copy from)
- Uses `tmp_path` fixture to create temporary `pyproject.toml` files
- Imports: `from tools.read_github_deps import main`

**Test cases** (all from reference):

| Test | What it verifies |
|------|-----------------|
| `test_packages_generates_install_command` | `packages` key → `uv pip install "pkg"` output |
| `test_packages_no_deps_generates_no_deps_command` | `packages-no-deps` key → `uv pip install --no-deps "pkg"` output |
| `test_both_packages_and_no_deps` | Both keys → 2 lines, correct order (packages first) |
| `test_missing_pyproject_returns_silently` | No pyproject.toml → no output, no error |
| `test_empty_config_returns_silently` | No install-from-github section → no output |
| `test_multiple_packages_grouped_in_one_command` | Multiple entries joined in single command |

## Integration Points
- `tools/__init__.py` already exists → `tools.read_github_deps` is importable
- `pyproject.toml` already has `[tool.mcp-coder.install-from-github]` config

## Verification
1. Run tests: `mcp__tools-py__run_pytest_check(extra_args=["-n", "auto"])`
2. Run pylint: `mcp__tools-py__run_pylint_check()`
3. Run mypy: `mcp__tools-py__run_mypy_check()`

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for full context.

Implement Step 1 of Issue #94: Add tools/read_github_deps.py and tests/test_read_github_deps.py.

1. Copy tools/read_github_deps.py verbatim from reference project p_mcp_utils (use read_reference_file)
2. Write tests/test_read_github_deps.py from scratch based on the test cases listed above
3. Run all three quality checks (pylint, pytest, mypy)
4. Fix any issues until all checks pass
5. Commit with message: "feat: add read_github_deps.py with tests"
```
