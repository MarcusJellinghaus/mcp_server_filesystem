@echo off
REM Reinstall mcp-server-filesystem package in development mode
REM This script uninstalls and reinstalls the package to ensure clean installation

echo =============================================
echo MCP-Server-Filesystem Package Reinstallation
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
    echo This script must be run from within a Python virtual environment.
    echo.
    echo To create a virtual environment:
    echo   python -m venv .venv
    echo.
    echo Then activate your virtual environment:
    echo   .venv\Scripts\activate
    echo.
    pause
    exit /b 1
)
echo [OK] Running in virtual environment: %VIRTUAL_ENV%
echo.

echo [1/5] Uninstalling existing package...
uv pip uninstall mcp-server-filesystem 2>nul
echo [OK] Done
echo.

echo [2/5] Installing package in development mode...
uv pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Installation failed!
    echo Please check for errors above and try again.
    pause
    exit /b 1
)
echo [OK] Package installed successfully
echo.

echo [3/5] Installing development dependencies...
uv pip install -e ".[dev]"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Development dependencies installation failed!
    echo Please check for errors above and try again.
    pause
    exit /b 1
)
echo [OK] Development dependencies installed successfully
echo.

echo [4/5] Verifying package import...
python -c "import mcp_server_filesystem; print('mcp_server_filesystem imported successfully')"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Import verification failed!
    echo The mcp_server_filesystem package is not working properly.
    pause
    exit /b 1
)
echo [OK] Package import verified successfully
echo.

echo [5/5] Verifying CLI entry point...
mcp-server-filesystem --help >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] CLI entry point verification failed!
    echo The mcp-server-filesystem command is not working properly.
    pause
    exit /b 1
)
echo [OK] CLI entry point verified successfully
echo.

echo =============================================
echo Reinstallation completed successfully!
echo You can now use the mcp_server_filesystem module
echo =============================================
