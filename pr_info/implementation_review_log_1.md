# Implementation Review Log — Run 1

**Issue:** #140 — feat(git): support git operations on reference projects
**Date:** 2026-04-23
**Branch:** 140-feat-git-support-git-operations-on-reference-projects

## Round 1 — 2026-04-23
**Findings**:
- `server_reference_tools.py:75` (missing-requirement): `get_reference_projects()` usage string lists tools that accept `reference_name` but omits the newly-supported `git()`.

**Decisions**:
- **Accept**: Real gap — callers won't discover git() works with reference projects. One-line fix, bounded effort.

**Changes**:
- Updated usage string in `get_reference_projects()` to include `git()`
- Updated 2 test assertions to match new usage string

**Status**: committed
