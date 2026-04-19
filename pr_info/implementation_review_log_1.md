# Implementation Review Log — Issue #92

Reference project: repo URL, verify config, lazy auto-clone, search

## Round 1 — 2026-04-19

**Findings**:
- (Accept) Old CLI format gets confusing "missing 'name' key" warning instead of migration hint
- (Skip) Comma-in-path limitation undocumented — edge case, spec chose this format deliberately
- (Skip) Inconsistent deferred vs module-level imports — cosmetic, deliberate design choice
- (Skip) List comprehension vs `any()` for remote check — trivial, repos have 1-3 remotes
- (Skip) `ssh://` URL format not handled by normalizer — speculative edge case
- (Skip) Unnecessary `str()` cast on `p["name"]` — cosmetic only
- (Skip) Double-wrapped ValueError messages — works correctly, chained exception preserves context
- (Skip) Patch target for deferred import — confirmed correct
- (Skip) `setdefault` creates Lock on every call — not a bug, trivial overhead

**Decisions**:
- Accept #7: Detect old `name=path` CLI format and suggest new KV format. Bounded fix, improves breaking-change UX.
- All others skipped: cosmetic, speculative, or pre-existing per review principles.

**Changes**: Added old-format detection in `main.py:parse_and_validate_references()`. When a single KV pair has an unknown key and a path-like value, warns with migration hint. Existing "missing 'name' key" warning kept as fallback.

**Status**: Committed (2b12256)

## Round 2 — 2026-04-19

**Findings**: None. Round 1 fix reviewed — clean and correct.
**Decisions**: N/A
**Changes**: None
**Status**: No changes needed

## Final Status

- **Rounds**: 2 (1 with code changes, 1 clean)
- **Commits**: 1 (feat(config): detect old --reference-project format and suggest migration)
- **Quality checks**: All passing (pylint, pytest 842/844, mypy)
- **Open issues**: None

