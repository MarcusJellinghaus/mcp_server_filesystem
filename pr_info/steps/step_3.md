# Step 3: `reference_projects.py` — `ensure_available()` with Async Locking

## LLM Prompt

> Implement Step 3 of Issue #92. See `pr_info/steps/summary.md` for full context.
> Add `ensure_available()` to `reference_projects.py` with per-project asyncio.Lock and clone failure caching. TDD approach.
> Run all code quality checks (pylint, pytest, mypy) after changes. Commit: `feat(ref-projects): add ensure_available with lazy cloning and failure cache`

## WHERE

- **Tests:** `tests/test_reference_projects.py` (add new test class)
- **Implementation:** `src/mcp_workspace/reference_projects.py` (extend existing file)

## WHAT

### Module-level state

```python
_project_locks: Dict[str, asyncio.Lock] = {}
_clone_failure_cache: Dict[str, str] = {}  # project_name -> error message
```

### `ensure_available(project: ReferenceProject) -> None`

Async function. Ensures the reference project directory exists, cloning if needed.

```
async def ensure_available(project: ReferenceProject) -> None:
    lock = _project_locks.setdefault(project.name, asyncio.Lock())
    async with lock:
        if project.name in _clone_failure_cache:
            raise ValueError(f"Clone previously failed for '{project.name}': {cached_error}")
        if project.path.exists():
            return
        if project.url is None:
            raise ValueError(f"Reference project '{project.name}' directory missing and no URL configured")
        try:
            await asyncio.to_thread(clone_repo, project.url, project.path)
        except Exception as e:
            _clone_failure_cache[project.name] = str(e)
            raise ValueError(f"Failed to clone '{project.name}' from {project.url}: {e}") from e
```

### `clear_clone_failure_cache() -> None`

Utility for testing. Clears failure cache and locks.

```python
def clear_clone_failure_cache() -> None:
    _clone_failure_cache.clear()
    _project_locks.clear()
```

## HOW

- Import `asyncio` and `from mcp_workspace.git_operations.remotes import clone_repo`
- `asyncio.to_thread()` wraps the blocking `clone_repo` call
- Per-project lock via `dict.setdefault()` — creates lock on first access
- Failure cache is a simple dict — cleared on server restart (module reload)

## ALGORITHM

```
1. Get or create asyncio.Lock for this project name
2. Acquire lock
3. Check failure cache → raise cached error if found
4. Check if path exists → return if yes
5. Check if URL is set → raise if not
6. Clone via asyncio.to_thread(clone_repo) → cache failure on error
```

## DATA

```python
# _clone_failure_cache structure:
{"project_name": "Failed to clone: authentication required"}

# ensure_available returns None on success, raises ValueError on failure
```

## TESTS

New test class in `tests/test_reference_projects.py`:

### `TestEnsureAvailable`

All tests use `asyncio` — either `@pytest.mark.asyncio` or `asyncio.run()`.

- `test_dir_exists_returns_immediately` — path exists → no clone attempted
- `test_no_dir_no_url_raises` — path missing, no URL → ValueError
- `test_clone_triggered_when_url_set` — path missing, URL set → `clone_repo` called (mock)
- `test_clone_failure_cached` — first call fails → second call raises immediately without re-cloning (mock)
- `test_cache_cleared` — after `clear_clone_failure_cache()`, retry is allowed
- `test_concurrent_access_single_clone` — two concurrent calls → only one clone (mock with asyncio.gather)

Mock `clone_repo` in all tests to avoid real git operations.
