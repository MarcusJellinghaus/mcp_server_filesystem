# Step 1: Add `[tool.mcp-coder.from-github]` config to pyproject.toml

## References
- [Summary](summary.md)
- Issue #82

## WHERE
- `pyproject.toml` — insert new section between `[tool.isort]` and `[tool.pylint.messages_control]`

## WHAT
Add the following TOML config block:

```toml
[tool.mcp-coder.from-github]
# Installed WITH deps (leaves — picks up new external deps)
packages = [
    "mcp-config-tool @ git+https://github.com/MarcusJellinghaus/mcp-config.git",
]
# Installed WITHOUT deps (depend on siblings — avoid downgrading)
packages-no-deps = [
    "mcp-tools-py @ git+https://github.com/MarcusJellinghaus/mcp-tools-py.git",
    "mcp-coder @ git+https://github.com/MarcusJellinghaus/mcp_coder.git",
]
```

## HOW
- Use `mcp__workspace__edit_file` to insert the block after the last line of `[tool.isort]` (after `float_to_top = true`) and before `[tool.pylint.messages_control]`.

## ALGORITHM
1. Read `pyproject.toml`
2. Locate the blank line between `[tool.isort]` block and `[tool.pylint.messages_control]`
3. Insert the `[tool.mcp-coder.from-github]` section there
4. Run `./tools/format_all.sh` (formatting check)
5. Run pylint, pytest, mypy checks (all should pass — no code changes)
6. Commit

## DATA
No return values or data structures — config-only change.

## TDD
Not applicable — this is a declarative config addition with no testable behavior in this project. The config is consumed by the external `mcp-coder` tool.

## Commit
```
chore: add [tool.mcp-coder.from-github] config to pyproject.toml
```

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement Step 1: Add the [tool.mcp-coder.from-github] section to pyproject.toml.
Insert it between the [tool.isort] and [tool.pylint.messages_control] sections.
Use the exact content specified in step_1.md.

After editing, run format_all.sh, then run pylint, pytest (unit tests only), and mypy checks.
Commit with message: "chore: add [tool.mcp-coder.from-github] config to pyproject.toml"
```
