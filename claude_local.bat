@echo off
cls
setlocal enabledelayedexpansion
REM Local launcher for Claude Code with MCP servers using active environment
REM Assumes mcp-coder is installed in currently active virtual environment

REM Check if local .venv exists
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Local virtual environment not found at .venv
    echo Please run: tools\reinstall.bat
    exit /b 1
)

REM Get expected virtual environment path
set "EXPECTED_VENV=%CD%\.venv"

REM Check if wrong virtual environment is activated
if not "!VIRTUAL_ENV!"=="" (
    if not "!VIRTUAL_ENV!"=="!EXPECTED_VENV!" (
        echo INFO: Deactivating wrong virtual environment
        echo   Current: !VIRTUAL_ENV!
        echo   Expected: !EXPECTED_VENV!
        call deactivate 2>nul
        set "VIRTUAL_ENV="
    )
)

REM Activate correct virtual environment if needed
if "!VIRTUAL_ENV!"=="" (
    echo Activating local virtual environment...
    call .venv\Scripts\activate.bat
    if "!VIRTUAL_ENV!"=="" (
        echo ERROR: Failed to activate virtual environment
        echo Please check .venv\Scripts\activate.bat
        exit /b 1
    )
)

REM Check if mcp-coder is available in the local environment
python -c "import mcp_coder" 2>nul
if !errorlevel! neq 0 (
    echo ERROR: mcp-coder not found in local virtual environment
    echo Local environment: !VIRTUAL_ENV!
    echo Please run: tools\reinstall.bat
    exit /b 1
)

REM Set project directories for MCP servers
set "MCP_CODER_PROJECT_DIR=%CD%"
set "MCP_CODER_VENV_DIR=%CD%\.venv"
set "DISABLE_AUTOUPDATER=1"

REM Start Claude Code using the local mcp-coder installation
echo Starting Claude Code with:
echo VIRTUAL_ENV=!VIRTUAL_ENV!
echo MCP_CODER_PROJECT_DIR=!MCP_CODER_PROJECT_DIR!
echo MCP_CODER_VENV_DIR=!MCP_CODER_VENV_DIR!
echo DISABLE_AUTOUPDATER=!DISABLE_AUTOUPDATER!
C:\Users\%USERNAME%\.local\bin\claude.exe %*
