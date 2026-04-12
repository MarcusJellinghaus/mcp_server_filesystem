# Step 1: Swap imports and delete local log_utils

## Summary

See [summary.md](summary.md) for full context.

Replace all `mcp_workspace.log_utils` imports with `mcp_coder_utils.log_utils`, then delete the local module and its tests.

## WHERE

Files to **edit** (import swap):
- `src/mcp_workspace/main.py` — line 13
- `src/mcp_workspace/server.py` — line 18
- `src/mcp_workspace/file_tools/file_operations.py` — line 16

Files to **delete**:
- `src/mcp_workspace/log_utils.py`
- `tests/test_log_utils.py`

## WHAT

No new functions. Three single-line import changes:

```python
# main.py: BEFORE
from mcp_workspace.log_utils import setup_logging
# main.py: AFTER
from mcp_coder_utils.log_utils import setup_logging

# server.py: BEFORE
from mcp_workspace.log_utils import log_function_call
# server.py: AFTER
from mcp_coder_utils.log_utils import log_function_call

# file_operations.py: BEFORE
from mcp_workspace.log_utils import log_function_call
# file_operations.py: AFTER
from mcp_coder_utils.log_utils import log_function_call
```

## HOW

1. Edit the three import lines
2. Delete `src/mcp_workspace/log_utils.py`
3. Delete `tests/test_log_utils.py`
4. Run pylint, pytest, mypy — all must pass

## TDD Note

No new tests needed. The existing test suite (minus the deleted `test_log_utils.py`) serves as the integration verification — if `server.py` and `file_operations.py` work with the new import, the swap is correct.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement step 1: swap all `from mcp_workspace.log_utils import ...` to
`from mcp_coder_utils.log_utils import ...` in main.py, server.py, and
file_operations.py. Then delete src/mcp_workspace/log_utils.py and
tests/test_log_utils.py. Run pylint, pytest (excluding integration markers),
and mypy to verify.
```
