# MCP Coder Setup Guide

This repository is configured to work with [mcp_coder](https://github.com/MarcusJellinghaus/mcp_coder) for AI-assisted development workflows.

## Quick Start

### 1. Install mcp-coder

```bash
# Activate your virtual environment
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Install mcp-coder
pip install git+https://github.com/MarcusJellinghaus/mcp_coder.git

# Also install mcp-code-checker
pip install git+https://github.com/MarcusJellinghaus/mcp-code-checker.git
```

### 2. Launch Claude Code

```bash
# Windows
.\claude_local.bat

# Linux/Mac
./claude_local.sh  # (if available)
```

This launcher will:
- Auto-activate your local `.venv`
- Set MCP environment variables
- Launch Claude Code with proper configuration

### 3. Verify MCP Servers

Once Claude Code starts, test the MCP tools:

```python
# Test filesystem server
mcp__filesystem__read_file(file_path="README.md")

# Test code-checker server
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto"])
```

## Configuration Files

### Core Configuration

| File | Purpose |
|------|---------|
| `.mcp.windows.json` | MCP server configuration (Windows) |
| `.claude/CLAUDE.md` | Mandatory instructions for Claude Code |
| `.claude/settings.local.json` | Pre-approved permissions for tools |
| `claude_local.bat` | Claude Code launcher with environment setup |

### GitHub Actions Workflows

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | Code quality checks (black, isort, pylint, pytest, mypy) |
| `.github/workflows/label-new-issues.yml` | Auto-label new issues with `status-01:created` |
| `.github/workflows/approve-command.yml` | Handle `/approve` comments on issues |

### Development Tools

#### Code Quality Scripts

| Script | Purpose |
|--------|---------|
| `tools/format_all.bat/.sh` | Format code with black and isort |
| `tools/reinstall.bat/.sh` | Reinstall package in development mode |
| `tools/pylint_check.bat` | Run pylint error checks |
| `tools/mypy_check.bat` | Run mypy type checks |
| `tools/pytest_check.bat` | Run pytest in parallel mode |

#### Architecture Enforcement Scripts

| Script | Purpose |
|--------|---------|
| `tools/lint_imports.bat/.sh` | Check import contracts (layered architecture) |
| `tools/tach_check.bat/.sh` | Check architectural boundaries |
| `tools/pycycle_check.bat/.sh` | Detect circular dependencies |
| `tools/vulture_check.bat/.sh` | Find dead/unused code |
| `tools/run_all_checks.bat/.sh` | Run ALL checks (quality + architecture) |

## Slash Commands

Available slash commands in `.claude/commands/`:

| Command | Purpose |
|---------|---------|
| `/commit_push` | Format, commit, and push changes |
| `/implementation_review` | Perform code review on current branch |
| `/plan_review` | Review implementation plan |
| `/rebase` | Rebase current branch onto main |

## MCP Server Configuration

### Configured Servers

1. **code-checker** - Code quality and testing tools
   - Pylint checks
   - Pytest execution (parallel mode)
   - Mypy type checking

2. **filesystem** - Enhanced file operations
   - Read/write/edit files
   - Reference projects access:
     - `p_coder` - mcp_coder repository
     - `p_checker` - mcp-code-checker repository

### Environment Variables

The `claude_local.bat` launcher sets:
- `MCP_CODER_PROJECT_DIR` - Current project directory
- `MCP_CODER_VENV_DIR` - Virtual environment path
- `DISABLE_AUTOUPDATER` - Disable Claude Code auto-updates

## Workflow Integration

### Issue Workflow Labels

The repository uses status labels for issue tracking:

1. `status-01:created` - New issue (auto-applied)
2. `status-02:awaiting-planning` - Ready for planning
3. `status-03:planning` - Planning in progress
4. `status-04:plan-review` - Plan ready for review
5. `status-05:plan-ready` - Plan approved
6. `status-06:implementing` - Implementation in progress
7. `status-07:code-review` - Code ready for review
8. `status-08:ready-pr` - Ready to create PR
9. `status-09:pr-creating` - PR creation in progress
10. `status-10:pr-created` - PR created

### Using `/approve` Command

Comment `/approve` on an issue to promote it to the next stage:
- `status-01:created` → `status-02:awaiting-planning`
- `status-04:plan-review` → `status-05:plan-ready`
- `status-07:code-review` → `status-08:ready-pr`

## Development Best Practices

### Mandatory Code Quality

Claude Code is configured (via `CLAUDE.md`) to **always** run these checks after **every** code change:

```python
mcp__code-checker__run_pylint_check()
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto"])
mcp__code-checker__run_mypy_check()
```

**All checks must pass** before proceeding.

### Before Every Commit

Always format code before committing:

```bash
# Windows
tools\format_all.bat

# Linux/Mac
./tools/format_all.sh
```

Then review and commit:

```bash
git status
git diff
git add .
git commit -m "feat: your change description"
git push
```

Or use the slash command:
```
/commit_push
```

### Code Review Process

1. Complete your implementation
2. Run code quality checks (automatic via CLAUDE.md)
3. Use `/implementation_review` for AI code review
4. Address any issues found
5. Use `/commit_push` to commit and push
6. Create PR

### Rebasing

When you need to update your feature branch with main:

```
/rebase
```

This will:
- Fetch latest changes
- Rebase onto main
- Handle conflicts
- Run all quality checks
- Push with force-with-lease

## CI/CD Pipeline

### Code Quality Checks (All Branches)

Runs on every push and PR:

- ✅ **black** - Code formatting check
- ✅ **isort** - Import sorting check
- ✅ **pylint** - Error detection
- ✅ **pytest** - Test suite (parallel execution)
- ✅ **mypy** - Strict type checking

### Architecture Checks (PRs Only)

Runs only on pull requests:

- ✅ **import-linter** - Enforce layered architecture and library isolation
- ✅ **tach** - Check module boundaries and dependencies
- ✅ **pycycle** - Detect circular dependencies
- ✅ **vulture** - Find dead/unused code

All checks run in parallel with `fail-fast: false` to see all issues at once.

**Why PR-only for architecture?** These checks are more expensive and most valuable when reviewing code changes.

## Dependency Management

Dependabot is configured to:
- Check for dependency updates weekly
- Create PRs for updates
- Target the `main` branch
- Label PRs with `dependencies` and `python`

## Troubleshooting

### MCP Servers Not Working

1. Verify installation:
   ```bash
   pip list | grep mcp
   ```

2. Check environment variables:
   ```bash
   echo %MCP_CODER_PROJECT_DIR%
   echo %MCP_CODER_VENV_DIR%
   ```

3. Review MCP server logs (if available)

### Claude Not Following CLAUDE.md

1. Verify `.claude/CLAUDE.md` exists
2. Check for syntax errors in the file
3. Restart Claude Code

### Tests Failing

1. Run tests locally:
   ```bash
   pytest -n auto -v
   ```

2. Check for missing dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Review test output for specific failures

## Architecture Enforcement

This repository uses four tools to maintain clean architecture:

### Install Architecture Tools

```bash
pip install -e ".[architecture]"
```

This installs:
- **import-linter** - Contract-based import validation
- **tach** - Module boundary enforcement
- **pycycle** - Circular dependency detection
- **vulture** - Dead code detection

### Run Architecture Checks

```bash
# Run all checks at once
tools\run_all_checks.bat  # Windows
./tools/run_all_checks.sh  # Linux/Mac

# Or run individually
tools\lint_imports.bat     # Import contracts
tools\tach_check.bat       # Module boundaries
tools\pycycle_check.bat    # Circular dependencies
tools\vulture_check.bat    # Dead code
```

### Configuration Files

| File | Purpose |
|------|---------|
| `.importlinter` | Define import contracts and library isolation |
| `tach.toml` | Define architectural layers and module dependencies |
| `vulture_whitelist.py` | Whitelist intentionally "unused" code (MCP handlers, fixtures) |
| `.large-files-allowlist` | Files allowed to exceed size limits |

**See:** `docs/ARCHITECTURE.md` for detailed architecture documentation.

## Additional Resources

- [Architecture Guide](docs/ARCHITECTURE.md) - **Start here for architecture details**
- [mcp_coder Documentation](https://github.com/MarcusJellinghaus/mcp_coder)
- [Repository Setup Guide](https://github.com/MarcusJellinghaus/mcp_coder/blob/main/docs/repository-setup.md)
- [Claude Code Configuration](https://github.com/MarcusJellinghaus/mcp_coder/blob/main/docs/configuration/claude-code.md)
- [MCP Protocol](https://modelcontextprotocol.io/)

## Support

For issues or questions:
- Open an issue in this repository
- Check mcp_coder issues: https://github.com/MarcusJellinghaus/mcp_coder/issues
- Review Claude Code documentation
