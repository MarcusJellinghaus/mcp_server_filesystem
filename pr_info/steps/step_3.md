# Step 3 — Re-enable `import-linter` in CI and verify

## Context

See [summary.md](summary.md) for the full picture.

With Steps 1 and 2 complete, `lint-imports` should now pass cleanly.
This step re-adds it to the CI architecture matrix and runs a local verification.

---

## WHERE

`.github/workflows/ci.yml` — the `architecture` job's `matrix.check` list.

---

## WHAT

Add one entry to the `matrix.check` list in the `architecture` job:

```yaml
# BEFORE (architecture matrix):
matrix:
  check:
    - {name: "tach", cmd: "tach check"}
    - {name: "pycycle", cmd: "pycycle --here"}
    - {name: "vulture", cmd: "vulture src tests vulture_whitelist.py --min-confidence 60"}

# AFTER:
matrix:
  check:
    - {name: "tach", cmd: "tach check"}
    - {name: "pycycle", cmd: "pycycle --here"}
    - {name: "vulture", cmd: "vulture src tests vulture_whitelist.py --min-confidence 60"}
    - {name: "import-linter", cmd: "lint-imports"}
```

---

## HOW

- Edit `.github/workflows/ci.yml` only.
- `import-linter` runs in the existing `architecture` job (PR-only), under the same
  `pip install -e ".[dev,architecture]"` setup — no job-level changes needed.
- `lint-imports` is the CLI entry point installed by the `import-linter` package,
  already present in `[dev,architecture]` extras.

---

## ALGORITHM

```
1. Open .github/workflows/ci.yml
2. Locate the architecture job's matrix.check list
3. Append: - {name: "import-linter", cmd: "lint-imports"}
4. Run locally: lint-imports  →  all contracts must pass ("All contracts ok.")
5. Run locally: pytest         →  all tests must still pass (regression check)
```

---

## DATA

CI config change only. No runtime data affected.

**Expected `lint-imports` output (success):**
```
All contracts ok.
```

**Expected contracts checked:**
- `Layered Architecture` ✓
- `MCP Library Isolation` ✓
- `GitPython Library Isolation` ✓
- `Structlog Library Isolation` ✓  (main.py no longer exempted or violating)
- `Source Code Independence from Tests` ✓
- (`File Tools Module Independence` — gone, no longer checked)

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Implement Step 3 exactly as specified:

1. Open .github/workflows/ci.yml.
2. In the `architecture` job's matrix.check list, add:
       - {name: "import-linter", cmd: "lint-imports"}
   after the existing vulture entry.
3. Save the file.
4. Run lint-imports locally and confirm the output is "All contracts ok."
5. Run pytest locally and confirm all tests pass.

If lint-imports reports any failure, do NOT proceed — diagnose and fix before
marking this step complete.
```
