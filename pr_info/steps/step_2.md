# Step 2 — Implement the Backslash Hint (TDD Green Phase)

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`), then implement
> the change described below in `src/mcp_server_filesystem/file_tools/edit_file.py`.
> After implementing, run the tests to confirm the test from Step 1 now passes and no
> existing tests are broken.

---

## WHERE

**Modify** `src/mcp_server_filesystem/file_tools/edit_file.py`

Locate the failure branch inside the `for i, edit in enumerate(edits):` loop.
It currently ends with:

```python
else:
    match_results.append(
        {
            "edit_index": i,
            "match_type": "failed",
            "details": f"Text not found: {_truncate(old_text)}",
        }
    )
    edits_failed += 1
```

This is the **only** location to change.

No other files are modified in this step.

---

## WHAT

Replace the bare `match_results.append(...)` call above with a `details` variable
computed by a backslash-doubling check, then append using that variable.

**No new functions. No new imports.**

---

## HOW

Inline code added directly before the existing `match_results.append(...)`:

```python
# LLM/raw-bytes semantic gap: read_file returns raw bytes (e.g. \\ for
# JSON-escaped Windows paths), but an LLM may decode \\ to \ and pass
# single backslashes in old_text — causing an exact-match failure.
doubled = old_text.replace("\\", "\\\\")
if doubled != old_text and doubled in current_content:
    details = (
        f"Text not found: {_truncate(old_text)}\n"
        "Hint: file may store backslashes as `\\\\` (double backslashes)"
        " — use double backslashes in both `old_text` and `new_text`."
    )
else:
    details = f"Text not found: {_truncate(old_text)}"
match_results.append(
    {"edit_index": i, "match_type": "failed", "details": details}
)
edits_failed += 1
```

---

## ALGORITHM

```
1. doubled = old_text with every \ replaced by \\
2. Guard: doubled != old_text   → only act when backslashes are present
3. Check: doubled in current_content → would-have-matched test
4. If both: details = "Text not found: ..." + newline + hint sentence
5. Else:    details = "Text not found: ..."  (unchanged generic message)
6. Append match_result with computed details; increment edits_failed
```

---

## DATA

### Changed fields (failure case only)

| Field | Before | After (when hint applies) |
|-------|--------|--------------------------|
| `match_results[i]["details"]` | `"Text not found: <truncated>"` | `"Text not found: <truncated>\nHint: file may store backslashes as \`\\\\\` (double backslashes) — use double backslashes in both \`old_text\` and \`new_text\`."` |
| `result["message"]` | unchanged | unchanged |
| `result["error"]` | unchanged | unchanged |
| `result["success"]` | unchanged | unchanged |

### Unchanged behaviour (when hint does NOT apply)

- `old_text` contains no backslashes → `doubled == old_text` → guard fails → generic message
- `old_text` contains backslashes but `doubled` is not in `current_content` → check fails → generic message
- All success/skip paths → completely unaffected
