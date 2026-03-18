@echo off
REM Reinstall mcp-workspace package in development mode
REM This script ONLY works with the project-local .venv directory

echo =============================================
echo mcp-workspace Package Reinstallation (Local)
echo =============================================
echo.

REM Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] uv not found. Installing uv...
    pip install uv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install uv!
        echo Please install uv manually: pip install uv
        pause
        exit /b 1
    )
    echo [OK] uv installed successfully
    echo.
)
echo [OK] uv is available
echo.

REM Check if running in a virtual environment
if "%VIRTUAL_ENV%"=="" (
    echo [ERROR] Not running in a virtual environment!
    echo.
    echo This script must be run from within the project-local .venv.
    echo.
    echo To create and activate it:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo.
    pause
    exit /b 1
)

REM Check that the venv is the project-local .venv
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
pushd "%PROJECT_DIR%"
set "PROJECT_DIR=%CD%"
popd
set "EXPECTED_VENV=%PROJECT_DIR%\.venv"

if /I not "%VIRTUAL_ENV%"=="%EXPECTED_VENV%" (
    echo [ERROR] Wrong virtual environment!
    echo.
    echo Active venv:   %VIRTUAL_ENV%
    echo Expected venv: %EXPECTED_VENV%
    echo.
    echo This script only works with the project-local .venv directory.
    echo Please activate the correct environment:
    echo   %EXPECTED_VENV%\Scripts\activate
    echo.
    pause
    exit /b 1
)
echo [OK] Running in project-local .venv: %VIRTUAL_ENV%
echo.

echo [1/5] Uninstalling existing MCP packages...
echo Uninstalling mcp-workspace...
uv pip uninstall mcp-workspace 2>nul
echo Uninstalling mcp-tools-py...
uv pip uninstall mcp-tools-py 2>nul
echo Uninstalling mcp-coder...
uv pip uninstall mcp-coder 2>nul
echo [OK] Done
echo.

echo [2/5] Installing package with development dependencies...
uv pip install -e ".[dev]"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Installation failed!
    echo Please check for errors above and try again.
    pause
    exit /b 1
)
echo [OK] Package installed successfully
echo.

echo [3/6] Reinstalling local package (editable, no deps)...
uv pip install -e . --no-deps
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Local editable reinstall failed!
    pause
    exit /b 1
)
echo [OK] Local editable install takes precedence
echo.

echo [4/6] Verifying package import...
python -c "import mcp_workspace; print('mcp_workspace imported successfully')"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Import verification failed!
    echo The mcp_workspace package is not working properly.
    pause
    exit /b 1
)
echo [OK] Package import verified successfully
echo.

echo [5/6] Verifying CLI entry point...
mcp-workspace --help >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] CLI entry point verification failed!
    echo The mcp-workspace command is not working properly.
    pause
    exit /b 1
)
echo [OK] CLI entry point verified successfully
echo.

echo [6/6] Verifying MCP dependencies...
python -c "import mcp_tools_py; print('mcp-tools-py installed successfully')"
if %ERRORLEVEL% NEQ 0 (
    echo Warning: mcp-tools-py not available
) else (
    echo [OK] MCP tools-py verified
)
echo.

echo =============================================
echo Reinstallation completed successfully!
echo You can now use the mcp_workspace module
echo =============================================
