# Step 1 — Write the Failing Test (TDD Red Phase)

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`), then implement
> the test described below. Do **not** modify any source files in this step —
> only create the new test file. The test must fail (or error) before Step 2 is applied.

---

## WHERE

**Create** `tests/file_tools/test_edit_file_backslash.py`

No other files are created or modified in this step.

---

## WHAT

### Class: `TestEditFileBackslashHint`

One test method:

```python
def test_single_backslash_old_text_gives_hint(self) -> None:
```

**Purpose:** Verifies that when `old_text` uses single backslashes but the file stores
double backslashes (raw bytes), the failure `details` contains the backslash hint, while
the top-level `message` and `error` remain the generic count summary.

---

## HOW

Standard `unittest.TestCase`. Imports:

```python
import tempfile
import unittest
from pathlib import Path

from mcp_server_filesystem.file_tools.edit_file import edit_file
```

No additional imports required — `edit_file` is the only function under test.

---

## ALGORITHM

```
1. Create a TemporaryDirectory; write a JSON file containing a
   Windows path stored with double backslashes on disk, e.g.:
       {"path": "C:\\Users\\test\\file.json"}
   (Python raw string: '{"path": "C:\\\\Users\\\\test\\\\file.json"}')

2. Call edit_file() with old_text using SINGLE backslashes
   (simulating the LLM's decoded understanding):
       old_text = '{"path": "C:\\Users\\test\\file.json"}'

3. Assert result["success"] is False.

4. Assert result["match_results"][0]["match_type"] == "failed".

5. Assert the backslash hint string is present in
   result["match_results"][0]["details"].

6. Assert result["message"] == "Failed to find exact match for 1 edit(s)".
   Assert result["error"]   == "Failed to find exact match for 1 edit(s)".
```

---

## DATA

### Input — file on disk (raw bytes)
```
{"path": "C:\\Users\\test\\file.json"}
```
(Two backslashes between each path component, as JSON encoding requires.)

### Input — `edit_file()` call
```python
edit_file(
    str(test_file),
    [{"old_text": '{"path": "C:\\Users\\test\\file.json"}',
      "new_text": '{"path": "C:\\Users\\test\\file_NEW.json"}'}]
)
```

### Expected result shape
```python
{
    "success": False,
    "match_results": [
        {
            "edit_index": 0,
            "match_type": "failed",
            "details": "<contains 'Text not found' AND the backslash hint>",
        }
    ],
    "message": "Failed to find exact match for 1 edit(s)",
    "error":   "Failed to find exact match for 1 edit(s)",
    "diff": "",
    ...
}
```

### Hint string to assert (substring check)
```
"Hint: file may store backslashes as `\\\\` (double backslashes)"
```
