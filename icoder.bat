@echo off
cls
setlocal enabledelayedexpansion
REM Two-env aware launcher for iCoder with MCP servers
REM Discovers tool env (mcp-coder) separately from project env (.venv)
REM Assumes you're running from the project root

REM === Step 1: Tool env discovery ===
REM Determine where mcp-coder is installed (tool env Scripts dir)
set "TOOL_VENV_SCRIPTS="

if "!VIRTUAL_ENV!"=="" goto :discover_from_path

REM VIRTUAL_ENV is set — check if it's the project .venv or an external tool env
set "PROJECT_VENV=%CD%\.venv"
if /i "!VIRTUAL_ENV!"=="!PROJECT_VENV!" (
    REM VIRTUAL_ENV points to project .venv — tool env must be elsewhere
    goto :discover_from_path
) else (
    REM VIRTUAL_ENV points to an external env — assume it's the tool env
    set "TOOL_VENV_SCRIPTS=!VIRTUAL_ENV!\Scripts"
    goto :tool_env_found
)

:discover_from_path
REM Find mcp-coder on PATH
for /f "delims=" %%i in ('where mcp-coder 2^>nul') do (
    if "!TOOL_VENV_SCRIPTS!"=="" (
        set "TOOL_VENV_SCRIPTS=%%~dpi"
        REM Remove trailing backslash
        if "!TOOL_VENV_SCRIPTS:~-1!"=="\" set "TOOL_VENV_SCRIPTS=!TOOL_VENV_SCRIPTS:~0,-1!"
    )
)
if "!TOOL_VENV_SCRIPTS!"=="" (
    echo ERROR: Cannot find mcp-coder installation.
    echo.
    echo Either:
    echo   1. Activate the tool environment: path\to\tool\.venv\Scripts\activate.bat
    echo   2. Ensure mcp-coder is on your PATH: pip install mcp-coder
    exit /b 1
)

:tool_env_found
REM === Step 2: Set tool env variables ===
set "MCP_CODER_VENV_PATH=!TOOL_VENV_SCRIPTS!"

REM Resolve parent directory of Scripts to get venv root
for %%d in ("!MCP_CODER_VENV_PATH!\..") do set "MCP_CODER_VENV_DIR=%%~fd"

REM === Step 3: Project env activation ===
if exist "%CD%\.venv\Scripts\activate.bat" (
    echo Activating project environment: %CD%\.venv
    call "%CD%\.venv\Scripts\activate.bat"
    if "!VIRTUAL_ENV!"=="" (
        echo ERROR: Failed to activate project virtual environment.
        echo Please check .venv\Scripts\activate.bat
        exit /b 1
    )
) else (
    REM Self-hosting: tool env serves as both tool and project env
    echo No project .venv found — using tool environment for both.
    set "VIRTUAL_ENV=!MCP_CODER_VENV_DIR!"
)

REM === Step 4: MCP tool verification ===
if not exist "!MCP_CODER_VENV_PATH!\mcp-tools-py.exe" (
    echo ERROR: mcp-tools-py.exe not found in !MCP_CODER_VENV_PATH!
    echo Please reinstall mcp-coder: pip install mcp-coder
    exit /b 1
)
if not exist "!MCP_CODER_VENV_PATH!\mcp-workspace.exe" (
    echo ERROR: mcp-workspace.exe not found in !MCP_CODER_VENV_PATH!
    echo Please reinstall mcp-coder: pip install mcp-coder
    exit /b 1
)

REM === Step 4b: Print MCP server versions ===
"!MCP_CODER_VENV_PATH!\mcp-workspace.exe" --version
"!MCP_CODER_VENV_PATH!\mcp-tools-py.exe" --version

REM === Step 5: Set env vars and launch ===
set "MCP_CODER_PROJECT_DIR=%CD%"
set "DISABLE_AUTOUPDATER=1"
set "PATH=!MCP_CODER_VENV_PATH!;!PATH!"

echo Starting iCoder with:
echo   Tool env:     !MCP_CODER_VENV_PATH!
echo   Project env:  !VIRTUAL_ENV!
echo   Project dir:  !MCP_CODER_PROJECT_DIR!
echo   Venv dir:     !MCP_CODER_VENV_DIR!

mcp-coder icoder %*
