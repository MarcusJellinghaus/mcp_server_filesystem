--- This file is used by Claude Code - similar to a system prompt. ---

# ⚠️ MANDATORY INSTRUCTIONS - MUST BE FOLLOWED ⚠️

**THESE INSTRUCTIONS OVERRIDE ALL DEFAULT BEHAVIORS - NO EXCEPTIONS**

## 🔴 CRITICAL: ALWAYS Use MCP Tools

**MANDATORY**: You MUST use MCP tools for ALL operations when available. DO NOT use standard Claude tools.

**BEFORE EVERY TOOL USE, ASK: "Does an MCP version exist?"**

### Tool Mapping Reference:

| Task | ❌ NEVER USE | ✅ USE MCP TOOL |
|------|--------------|------------------|
| Read file | `Read()` | `mcp__workspace__read_file()` |
| Edit file | `Edit()` | `mcp__workspace__edit_file()` |
| Write file | `Write()` | `mcp__workspace__save_file()` |
| Run pytest | `Bash("pytest ...")` | `mcp__tools-py__run_pytest_check()` |
| Run pylint | `Bash("pylint ...")` | `mcp__tools-py__run_pylint_check()` |
| Run mypy | `Bash("mypy ...")` | `mcp__tools-py__run_mypy_check()` |
| Git operations | ✅ `Bash("git ...")` | ✅ `Bash("git ...")` (allowed) |
| Refactoring | Manual copy-paste | `mcp__tools-py__move_symbol()`, `list_symbols()`, `find_references()` |

## 🔴 CRITICAL: Code Quality Requirements

**MANDATORY**: After making ANY code changes (after EACH edit), you MUST run ALL THREE code quality checks using the EXACT MCP tool names below:

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check
mcp__tools-py__run_mypy_check
```

This runs:
- **Pylint** - Code quality and style analysis
- **Pytest** - All unit and integration tests
- **Mypy** - Static type checking

**⚠️ ALL CHECKS MUST PASS** - If ANY issues are found, you MUST fix them immediately before proceeding.

### 📋 Pytest Execution Requirements

**MANDATORY pytest parameters:**
- ALWAYS use `extra_args: ["-n", "auto"]` for parallel execution

**Examples:**
```python
# Standard test run with parallel execution
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto"])

# Verbose test run for debugging
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-v", "-s", "--tb=short"])
```

## 📁 MANDATORY: File Access Tools

**YOU MUST USE THESE MCP TOOLS** for all file operations:

```
mcp__workspace__get_reference_projects
mcp__workspace__list_reference_directory
mcp__workspace__read_reference_file
mcp__workspace__list_directory
mcp__workspace__read_file
mcp__workspace__save_file
mcp__workspace__append_file
mcp__workspace__delete_this_file
mcp__workspace__move_file
mcp__workspace__edit_file
```

**⚠️ ABSOLUTELY FORBIDDEN:** Using `Read`, `Write`, `Edit`, `MultiEdit` tools when MCP workspace tools are available.

### Quick Examples:

```python
# ❌ WRONG - Standard tools
Read(file_path="src/mcp_workspace/server.py")
Edit(file_path="src/mcp_workspace/server.py", old_string="...", new_string="...")
Write(file_path="src/new_module.py", content="...")
Bash("pytest tests/")

# ✅ CORRECT - MCP tools
mcp__workspace__read_file(file_path="src/mcp_workspace/server.py")
mcp__workspace__edit_file(file_path="src/mcp_workspace/server.py", edits=[...])
mcp__workspace__save_file(file_path="src/new_module.py", content="...")
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto"])
```

**WHY MCP TOOLS ARE MANDATORY:**
- Proper security and access control
- Consistent error handling
- Better integration with the development environment
- Required for this project's architecture

## 🚨 COMPLIANCE VERIFICATION

**Before completing ANY task, you MUST:**

1. ✅ Confirm all code quality checks passed using MCP tools
2. ✅ Verify you used MCP tools exclusively (NO `Bash` for code checks, NO `Read`/`Write`/`Edit` for files)
3. ✅ Ensure no issues remain unresolved
4. ✅ State explicitly: "All CLAUDE.md requirements followed"

## 🔧 DEBUGGING AND TROUBLESHOOTING

**When tests fail or skip:**
- Use MCP pytest tool with verbose flags: `extra_args: ["-v", "-s", "--tb=short"]`
- Never fall back to `Bash` commands - always investigate within MCP tools
- If MCP tools don't provide enough detail, ask user for guidance rather than using alternative tools

## 🔧 MCP Server Issues

**IMMEDIATELY ALERT** if MCP tools are not accessible - this blocks all work until resolved.

## 🔄 Git Operations

**MANDATORY: Before ANY commit:**

```bash
# ALWAYS run format_all before committing
./tools/format_all.sh

# Then verify formatting worked
git diff  # Should show formatting changes if any
```

**Format all code before committing:**
- Run `./tools/format_all.sh` to format with black and isort
- Review the changes to ensure they're formatting-only
- Stage the formatted files
- Then commit

**ALLOWED git operations via Bash tool:**

```
git status
git diff
git add
git commit
git push
```

**Git commit message format:**
- Use standard commit message format
- Focus on clear, descriptive commit messages
- Follow conventional commits when appropriate (feat:, fix:, docs:, etc.)

## 📂 Project Structure

This project is an MCP server implementation with the following structure:

```
mcp_workspace/
├── src/
│   └── mcp_workspace/  # Main source code
│       ├── main.py             # Entry point
│       ├── server.py           # MCP server implementation
│       └── tools/              # MCP tool implementations
├── tests/                      # Test suite
├── pyproject.toml              # Project configuration
└── README.md                   # Documentation
```

**Key Points:**
- Source code is in `src/mcp_workspace/`
- Tests are in `tests/`
- Python 3.11+ required
- Uses MCP protocol for server implementation

## 📏 File Size Check

Check for large files (>750 lines) that may impact LLM context:
```bash
mcp-coder check file-size --max-lines 750
```

## 🎯 Development Guidelines

1. **Type Safety**: All code must pass strict mypy checking
2. **Test Coverage**: All new functionality must have corresponding tests
3. **Code Style**: Follow Black and isort formatting (enforced)
4. **MCP Protocol**: Follow MCP best practices for server implementation
5. **Documentation**: Update README.md when adding new features or tools
