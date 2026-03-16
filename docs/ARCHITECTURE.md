# Architecture Guide

This document describes the architectural principles and enforcement tools for the mcp_workspace project.

## Architecture Overview

The project follows a layered architecture pattern:

```
┌─────────────────────────────────┐
│  Entry Point (main.py)          │  ← Application entry
├─────────────────────────────────┤
│  MCP Server (server.py)         │  ← Protocol implementation
├─────────────────────────────────┤
│  File Tools (file_tools/)       │  ← Business logic
├─────────────────────────────────┤
│  Utilities (log_utils.py)       │  ← Shared utilities
└─────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Purpose | Can Import From |
|-------|---------|-----------------|
| **Entry** | Application startup and initialization | All layers below |
| **Protocol** | MCP server implementation and tool registration | File Tools, Utilities |
| **Tools** | File operation implementations | Utilities only |
| **Utilities** | Logging, configuration, shared functions | Standard library only |

## Architectural Principles

### 1. Dependency Flow

Dependencies flow **downward** only:
- Entry → Protocol → Tools → Utilities
- Higher layers depend on lower layers
- Lower layers never depend on higher layers
- Prevents circular dependencies

### 2. MCP Isolation

MCP protocol concerns are isolated to:
- `main.py` - Server initialization
- `server.py` - Tool registration and handlers

File tools remain **MCP-agnostic** for:
- Reusability in non-MCP contexts
- Easier testing
- Clearer separation of concerns

### 3. Library Isolation

External libraries are isolated to specific modules:

| Library | Used By | Rationale |
|---------|---------|-----------|
| `mcp` | main.py, server.py | Protocol implementation only |
| `git` (GitPython) | file_tools/git_operations.py | Git functionality isolated |
| `structlog` | log_utils.py, main.py | Logging setup centralized |

## Architecture Enforcement Tools

We use four tools to enforce architectural boundaries:

### 1. import-linter

**Purpose:** Contract-based import validation

**Configuration:** `.importlinter`

**What it checks:**
- Layered architecture (dependency flow)
- Library isolation (external dependencies)
- Test independence

**Run:**
```bash
# Windows
tools\lint_imports.bat

# Linux/Mac
./tools/lint_imports.sh
```

### 2. tach

**Purpose:** Module boundary enforcement

**Configuration:** `tach.toml`

**What it checks:**
- Layer dependencies
- Module coupling
- Circular dependency prevention

**Run:**
```bash
# Windows
tools\tach_check.bat

# Linux/Mac
./tools/tach_check.sh
```

### 3. pycycle

**Purpose:** Circular dependency detection

**Configuration:** None needed

**What it checks:**
- Import cycles between modules
- Circular dependencies at any level

**Run:**
```bash
# Windows
tools\pycycle_check.bat

# Linux/Mac
./tools/pycycle_check.sh
```

### 4. vulture

**Purpose:** Dead code detection

**Configuration:** `vulture_whitelist.py`

**What it checks:**
- Unused functions and classes
- Unused imports
- Unreachable code

**Note:** Some code appears unused but is called dynamically (MCP handlers, pytest fixtures). These are whitelisted in `vulture_whitelist.py`.

**Run:**
```bash
# Windows
tools\vulture_check.bat

# Linux/Mac
./tools/vulture_check.sh
```

## Running All Checks

Run all quality and architecture checks at once:

```bash
# Windows
tools\run_all_checks.bat

# Linux/Mac
./tools/run_all_checks.sh
```

This runs:
1. Code formatting (black, isort)
2. Linting (pylint)
3. Type checking (mypy)
4. Tests (pytest)
5. Import contracts (import-linter)
6. Architecture boundaries (tach)
7. Circular dependencies (pycycle)

## CI/CD Integration

### Regular CI (All Branches)

Runs on every push:
- black
- isort
- pylint
- pytest
- mypy

### Architecture CI (PRs Only)

Runs only on pull requests:
- import-linter
- tach
- pycycle
- vulture

**Why PR-only?** Architecture checks are more expensive and are most valuable when reviewing code changes.

## Common Violations and Fixes

### ❌ Circular Import

**Error:**
```
Detected 1 cycle:
  mcp_workspace.file_tools.file_operations
  -> mcp_workspace.file_tools.path_utils
  -> mcp_workspace.file_tools.file_operations
```

**Fix:**
- Move shared functionality to a new module
- Use dependency injection
- Refactor to remove the circular dependency

### ❌ Layer Violation

**Error:**
```
mcp_workspace.file_tools cannot import mcp_workspace.server
(higher layer importing lower layer)
```

**Fix:**
- File tools should not know about the server
- Pass dependencies as function parameters
- Use dependency inversion principle

### ❌ Library Isolation Violation

**Error:**
```
mcp_workspace.file_tools.file_operations imports 'git' directly
(should only be imported by git_operations)
```

**Fix:**
- Use `git_operations.py` functions instead of importing GitPython directly
- Maintains abstraction layer
- Makes testing easier (mock one module, not many)

## File Size Guidelines

Keep files manageable for LLM context windows:

**Maximum recommended:** 750 lines

**If a file exceeds this:**
1. Consider splitting into multiple modules
2. If splitting isn't practical, add to `.large-files-allowlist` with justification
3. Check with: `mcp-coder check file-size --max-lines 750`

## Adding New Modules

When adding new functionality:

1. **Determine the layer** - Where does it belong?
   - Tools? Protocol? Utilities?

2. **Update architecture configs:**
   - Add to `.importlinter` if it introduces new boundaries
   - Add to `tach.toml` if it's a new module

3. **Run architecture checks:**
   ```bash
   tools\run_all_checks.bat  # or .sh
   ```

4. **If a tool is dynamically called** (MCP handler, pytest fixture):
   - Add to `vulture_whitelist.py`

## References

- [Import Linter Documentation](https://import-linter.readthedocs.io/)
- [Tach Documentation](https://docs.gauge.so/tach/)
- [Pycycle on PyPI](https://pypi.org/project/pycycle/)
- [Vulture Documentation](https://github.com/jendrikseipp/vulture)
