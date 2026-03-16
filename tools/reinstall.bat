@echo off
REM Reinstall mcp-workspace package in development mode
REM This script uninstalls and reinstalls the package to ensure clean installation

echo =============================================
echo mcp-workspace Package Reinstallation
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

echo [1/4] Uninstalling existing package...
uv pip uninstall mcp-workspace 2>nul
echo [OK] Done
echo.

echo [2/4] Installing package with development dependencies...
uv pip install -e ".[dev]"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Installation failed!
    echo Please check for errors above and try again.
    pause
    exit /b 1
)
echo [OK] Package installed successfully
echo.

echo [3/4] Verifying package import...
python -c "import mcp_workspace; print('mcp_workspace imported successfully')"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Import verification failed!
    echo The mcp_workspace package is not working properly.
    pause
    exit /b 1
)
echo [OK] Package import verified successfully
echo.

echo [4/4] Verifying CLI entry point...
mcp-workspace --help >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] CLI entry point verification failed!
    echo The mcp-workspace command is not working properly.
    pause
    exit /b 1
)
echo [OK] CLI entry point verified successfully
echo.

echo =============================================
echo Reinstallation completed successfully!
echo You can now use the mcp_workspace module
echo =============================================
