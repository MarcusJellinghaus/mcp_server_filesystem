@echo off
REM Run import-linter architecture checks

echo Running import-linter...
lint-imports

if %errorlevel% neq 0 (
    echo.
    echo ✗ Import linter found violations!
    exit /b 1
)

echo.
echo ✓ All import contracts satisfied!
