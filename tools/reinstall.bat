@echo off
REM Reinstall package in development mode

echo Reinstalling mcp-server-filesystem in development mode...
pip install -e .

if %errorlevel% neq 0 (
    echo ERROR: Installation failed
    exit /b 1
)

echo.
echo ✓ Reinstall complete!
echo.
echo To also install development dependencies, run:
echo pip install -e ".[dev]"
