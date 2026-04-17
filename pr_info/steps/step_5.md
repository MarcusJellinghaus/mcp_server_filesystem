# Step 5: Update Architecture Enforcement + CI

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. This is step 5 of 5 for issue #104.
>
> **Task:** Update `.importlinter`, `tach.toml`, `vulture_whitelist.py`, `docs/ARCHITECTURE.md` for the new module layout. Split CI pytest into `unit-tests` and `integration-tests` matrix entries. Run full verification.
>
> **Key changes:** Layered architecture now has three tool-layer peers. New isolation contracts for PyGithub and requests. CI split ensures integration tests only run when secrets are available.

## WHERE

### Files to modify

```
.importlinter                    ← layered arch + new isolation contracts
tach.toml                        ← register new modules, peer dependencies
vulture_whitelist.py             ← update/add entries for new modules
docs/ARCHITECTURE.md             ← update diagram, layer table
.github/workflows/ci.yml         ← split pytest matrix
```

## WHAT

### `.importlinter` changes

Note: Layered architecture and gitpython isolation updates for `git_operations` were applied in Step 1. This step adds `github_operations`-related changes.

**1. Update layered architecture contract:**

```ini
[importlinter:contract:layered_architecture]
name = Layered Architecture
type = layers
layers =
    mcp_workspace.main
    mcp_workspace.server
    mcp_workspace.file_tools | mcp_workspace.git_operations | mcp_workspace.github_operations
    mcp_workspace.config | mcp_workspace.constants | mcp_workspace.utils
```

**2. Update GitPython isolation — expand to new path:**

```ini
[importlinter:contract:gitpython_isolation]
name = GitPython Library Isolation
type = forbidden
source_modules =
    mcp_workspace
forbidden_modules =
    git
ignore_imports =
    mcp_workspace.git_operations.* -> git
```

**3. Add PyGithub isolation contract:**

```ini
[importlinter:contract:pygithub_isolation]
name = PyGithub Library Isolation
type = forbidden
source_modules =
    mcp_workspace
forbidden_modules =
    github
ignore_imports =
    mcp_workspace.github_operations.* -> github
```

**4. Add requests isolation contract:**

```ini
[importlinter:contract:requests_isolation]
name = Requests Library Isolation
type = forbidden
source_modules =
    mcp_workspace
forbidden_modules =
    requests
ignore_imports =
    mcp_workspace.github_operations.* -> requests
```

### `tach.toml` changes

Note: `git_operations` module registration and `file_tools` depends_on update were applied in Step 1. This step adds `github_operations`, `config`, `constants`, and `utils` registrations.

Register new modules as tools-layer peers:

```toml
[[modules]]
path = "mcp_workspace.git_operations"
layer = "tools"
depends_on = [
    { path = "mcp_coder_utils.log_utils" },
    { path = "mcp_coder_utils.subprocess_runner" },
]

[[modules]]
path = "mcp_workspace.github_operations"
layer = "tools"
depends_on = [
    { path = "mcp_workspace.git_operations" },
    { path = "mcp_workspace.config" },
    { path = "mcp_workspace.constants" },
    { path = "mcp_workspace.utils" },
    { path = "mcp_coder_utils.log_utils" },
    { path = "mcp_coder_utils.subprocess_runner" },
]

[[modules]]
path = "mcp_workspace.config"
layer = "utilities"
depends_on = []

[[modules]]
path = "mcp_workspace.constants"
layer = "utilities"
depends_on = []

[[modules]]
path = "mcp_workspace.utils"
layer = "utilities"
depends_on = []
```

Update existing `file_tools` module to depend on `git_operations`:

```toml
[[modules]]
path = "mcp_workspace.file_tools"
layer = "tools"
depends_on = [
    { path = "mcp_workspace.git_operations" },
    { path = "mcp_coder_utils.log_utils" },
    { path = "mcp_coder_utils.subprocess_runner" },
]
```

Update `server` to also depend on new tool modules (if it imports from them):

```toml
[[modules]]
path = "mcp_workspace.server"
layer = "protocol"
depends_on = [
    { path = "mcp_workspace.file_tools" },
    { path = "mcp_coder_utils.log_utils" },
]
```

Update `tests` module to depend on new modules:

```toml
[[modules]]
path = "tests"
depends_on = [
    { path = "mcp_workspace" },
    { path = "mcp_workspace.main" },
    { path = "mcp_workspace.server" },
    { path = "mcp_workspace.file_tools" },
    { path = "mcp_workspace.git_operations" },
    { path = "mcp_workspace.github_operations" },
    { path = "mcp_workspace.config" },
    { path = "mcp_workspace.constants" },
    { path = "mcp_workspace.utils" },
    { path = "mcp_coder_utils.log_utils" },
]
```

### CI changes (`.github/workflows/ci.yml`)

Split the single `pytest` matrix entry into two:

```yaml
matrix:
  check:
    - {name: "black", cmd: "..."}
    - {name: "isort", cmd: "..."}
    - {name: "pylint", cmd: "..."}
    - {name: "unit-tests", cmd: "pytest --version && pytest -n auto -m 'not git_integration and not github_integration'"}
    - {name: "integration-tests", cmd: "pytest --version && pytest -n auto -m 'git_integration or github_integration'"}
    - {name: "mypy", cmd: "..."}
```

Note: `integration-tests` will auto-skip github tests when no `GITHUB_TOKEN` is set. CI secrets deferred to #106.

### `vulture_whitelist.py` changes

Add entries for any new publicly-exported symbols that appear unused (e.g., github_operations API). Review after running vulture and add as needed.

### `docs/ARCHITECTURE.md` changes

Update the ASCII diagram to show the new layout:

```
┌─────────────────────────────────┐
│  Entry Point (main.py)          │  ← Application entry
├─────────────────────────────────┤
│  MCP Server (server.py)         │  ← Protocol implementation
├─────────────────────────────────┤
│  file_tools/  │  git_operations/│  ← Business logic (peers)
│               │  github_ops/    │
├─────────────────────────────────┤
│  config │ constants │ utils     │  ← Utilities
├─────────────────────────────────┤
│  Shared Libs (mcp_coder_utils)  │  ← External shared libraries
└─────────────────────────────────┘
```

Update the layer table accordingly.

## HOW

### Pseudocode

```
edit(.importlinter: update layers, add 2 new contracts, update gitpython path)
edit(tach.toml: add 5 new module entries, update file_tools depends_on, update tests depends_on)
edit(ci.yml: replace "pytest" entry with "unit-tests" and "integration-tests")
edit(ARCHITECTURE.md: update diagram and tables)
run(vulture → add whitelist entries as needed)
```

## DATA

No new data structures. Configuration-only changes.

## Verification — Full Suite

```
pylint pass
mypy pass
pytest unit-tests pass (exclude integration markers)
lint-imports pass
tach check pass (if tach is installed)
vulture pass
grep "mcp_coder\." src/mcp_workspace/ — must return nothing
grep "file_tools.git_operations" src/ tests/ — must return nothing
mcp-coder check file-size --max-lines 750 — all files under limit
Verify: label_config.py, labels.json, labels_schema.md NOT present in mcp_workspace
```
