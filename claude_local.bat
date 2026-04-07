@echo off
cls
setlocal enabledelayedexpansion
REM Two-env aware launcher for Claude Code (developer edition)
REM Same two-env discovery as claude.bat, plus editable-install verification
REM Assumes mcp-coder is editable-installed (pip install -e .)

REM === Step 0: Project .venv must exist ===
if not exist "%CD%\.venv\Scripts\activate.bat" (
    echo ERROR: Local virtual environment not found at .venv
    echo Please run: tools\reinstall_local.bat
    exit /b 1
)

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
    echo   3. Run: tools\reinstall_local.bat
    exit /b 1
)

:tool_env_found
REM === Step 2: Set tool env variables ===
set "MCP_CODER_VENV_PATH=!TOOL_VENV_SCRIPTS!"

REM Resolve parent directory of Scripts to get venv root
for %%d in ("!MCP_CODER_VENV_PATH!\..") do set "MCP_CODER_VENV_DIR=%%~fd"

REM === Step 3: Project env activation ===
echo Activating project environment: %CD%\.venv
call "%CD%\.venv\Scripts\activate.bat"
if "!VIRTUAL_ENV!"=="" (
    echo ERROR: Failed to activate project virtual environment.
    echo Please check .venv\Scripts\activate.bat
    exit /b 1
)

REM === Step 4: Editable install verification ===
set "EDITABLE_OK=0"
for /f "delims=" %%L in ('pip show mcp-coder 2^>nul') do (
    echo %%L | findstr /i /c:"Editable project location" >nul 2>&1
    if !errorlevel! equ 0 (
        echo %%L | findstr /i /c:"%CD%" >nul 2>&1
        if !errorlevel! equ 0 set "EDITABLE_OK=1"
    )
    echo %%L | findstr /i /c:"Location:" >nul 2>&1
    if !errorlevel! equ 0 (
        echo %%L | findstr /i /c:"%CD%" >nul 2>&1
        if !errorlevel! equ 0 set "EDITABLE_OK=1"
    )
)
if "!EDITABLE_OK!"=="0" (
    echo WARNING: mcp-coder does not appear to be editable-installed from %CD%
    echo   For development, run: pip install -e .
    echo   Continuing anyway...
)

REM === Step 5: MCP tool verification ===
if not exist "!MCP_CODER_VENV_PATH!\mcp-tools-py.exe" (
    echo ERROR: mcp-tools-py.exe not found in !MCP_CODER_VENV_PATH!
    echo Please run: tools\reinstall_local.bat
    exit /b 1
)
if not exist "!MCP_CODER_VENV_PATH!\mcp-workspace.exe" (
    echo ERROR: mcp-workspace.exe not found in !MCP_CODER_VENV_PATH!
    echo Please run: tools\reinstall_local.bat
    exit /b 1
)

REM === Step 5b: Print MCP server versions ===
"!MCP_CODER_VENV_PATH!\mcp-workspace.exe" --version
"!MCP_CODER_VENV_PATH!\mcp-tools-py.exe" --version

REM === Step 6: Set env vars and launch ===
set "MCP_CODER_PROJECT_DIR=%CD%"
set "DISABLE_AUTOUPDATER=1"
set "PATH=!MCP_CODER_VENV_PATH!;!PATH!"

echo Starting Claude Code (developer mode) with:
echo   Tool env:     !MCP_CODER_VENV_PATH!
echo   Project env:  !VIRTUAL_ENV!
echo   Project dir:  !MCP_CODER_PROJECT_DIR!
echo   Venv dir:     !MCP_CODER_VENV_DIR!

C:\Users\%USERNAME%\.local\bin\claude.exe %*
