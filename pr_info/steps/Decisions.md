# Decisions Log

Decisions made during plan review discussion.

## Decision 1: `.absolute()` → `.resolve()` scope in tests

**Choice:** Update `.absolute()` → `.resolve()` across the **entire** test file, not just `TestReferenceProjectIntegration`.

**Reason:** `TestReferenceProjectCLI` and `TestReferenceProjectServerStorage` also build expected values with `.absolute()`. These must match the production code's `.resolve()` output to avoid mismatches on systems where the two differ (e.g., Windows with symlinks).

## Decision 2: Overlap tests use real temp directories

**Choice:** Use `tmp_path` (pytest fixture) to create real directories instead of mocking `Path.resolve`.

**Reason:** Mocking `Path.resolve` globally is fragile — it affects all Path instances in the module. Real temp directories avoid this problem entirely and are more robust.

## Decision 3: No symlink edge case test

**Choice:** Skip adding a dedicated symlink overlap test.

**Reason:** No special code path exists for symlinks — `.resolve()` handles them transparently. There's nothing unique to test beyond what the standard overlap tests already cover.

## Decision 4: Resolve `project_dir` inside `validate_reference_projects()`

**Choice:** Call `project_dir.resolve()` once at the top of `validate_reference_projects()`.

**Reason:** Cheap safety net that makes the function safe to call from anywhere, not just from `main()`. Defensive good practice for a function that could be called from tests or future call sites.

## Decision 5: Strengthen `test_path_normalization` assertion

**Choice:** Assert that the result equals `Path("./relative/path").resolve()` explicitly, not just `is_absolute()`.

**Reason:** Validates that canonicalization actually happened (no `..` segments, symlinks resolved), which is the whole point of switching from `.absolute()` to `.resolve()`.
